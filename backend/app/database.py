import logging
import os
import time
import datetime
import enum
from typing import Generator, Dict, Any, List
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.exc import OperationalError
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

is_sqlite_db = settings.is_sqlite
fallback_sqlite_url = "sqlite:///./cloudwise.db"
is_mongodb = settings.DATABASE_URL.startswith("mongodb://") or settings.DATABASE_URL.startswith("mongodb+srv://")

engine = None
SessionLocal = None

class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass

# MongoDB translation layer
if is_mongodb:
    import pymongo
    from bson import ObjectId
    from sqlalchemy.orm.attributes import QueryableAttribute

    logger.info("Initializing MongoDB database connection client...")
    mongo_client = pymongo.MongoClient(settings.DATABASE_URL)
    
    # Overwrite comparison operators on QueryableAttribute to generate MongoDB filter conditions
    def eq(self, other):
        return {self.key: other}
    def ne(self, other):
        return {self.key: {"$ne": other}}
    def gt(self, other):
        return {self.key: {"$gt": other}}
    def ge(self, other):
        return {self.key: {"$gte": other}}
    def lt(self, decline):
        return {self.key: {"$lt": decline}}
    def le(self, other):
        return {self.key: {"$lte": other}}
    def in_op(self, values):
        return {self.key: {"$in": list(values)}}
    def like_op(self, pattern):
        regex = pattern.replace("%", ".*")
        return {self.key: {"$regex": regex, "$options": "i"}}
    def is_op(self, value):
        return {self.key: value}
    def is_not_op(self, value):
        return {self.key: {"$ne": value}}
    def desc_op(self):
        return (self.key, -1)
    def asc_op(self):
        return (self.key, 1)

    QueryableAttribute.__eq__ = eq
    QueryableAttribute.__ne__ = ne
    QueryableAttribute.__gt__ = gt
    QueryableAttribute.__ge__ = ge
    QueryableAttribute.__lt__ = lt
    QueryableAttribute.__le__ = le
    QueryableAttribute.in_ = in_op
    QueryableAttribute.like = like_op
    QueryableAttribute.is_ = is_op
    QueryableAttribute.is_not = is_not_op
    QueryableAttribute.desc = desc_op
    QueryableAttribute.asc = asc_op

    class RowTuple:
        """SQLAlchemy Row-like tuple wrapper for projections."""
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self._keys = list(kwargs.keys())
        def __getitem__(self, idx):
            if isinstance(idx, int):
                return getattr(self, self._keys[idx])
            return getattr(self, idx)
        def __getattr__(self, name):
            return self.__dict__.get(name)
        def __repr__(self):
            vals = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_"))
            return f"Row({vals})"

    def to_dict(obj):
        d = {}
        if hasattr(obj, "__mapper__"):
            for col in obj.__mapper__.columns:
                k = col.key
                v = getattr(obj, k, None)
                if v is None:
                    val = None
                    if col.default is not None:
                        val = col.default.arg
                        if callable(val):
                            try:
                                val = val()
                            except Exception:
                                val = val(None)
                    elif col.server_default is not None:
                        arg_str = str(col.server_default.arg).strip("'\"")
                        if arg_str.lower() in ("0", "false"):
                            val = False
                        elif arg_str.lower() in ("1", "true"):
                            val = True
                        else:
                            val = arg_str
                    if val is not None:
                        v = val
                        setattr(obj, k, val)
                if isinstance(v, (datetime.datetime, datetime.date)):
                    if isinstance(v, datetime.date) and not isinstance(v, datetime.datetime):
                        d[k] = datetime.datetime.combine(v, datetime.time.min)
                    else:
                        d[k] = v
                elif isinstance(v, enum.Enum):
                    d[k] = v.value
                else:
                    d[k] = v
        else:
            for k, v in obj.__dict__.items():
                if k.startswith("_"):
                    continue
                d[k] = v
        # Ensure UUID and Timestamp fields are set
        if not d.get("id"):
            from app.models.base import generate_uuid
            d["id"] = generate_uuid()
            obj.id = d["id"]
        if not d.get("created_at"):
            from app.models.base import utc_now
            now = utc_now()
            d["created_at"] = now
            obj.created_at = now
        if not d.get("updated_at"):
            from app.models.base import utc_now
            now = utc_now()
            d["updated_at"] = now
            obj.updated_at = now
        return d

    def from_dict(model_cls, doc):
        if not doc:
            return None
        instance = model_cls()
        for k, v in doc.items():
            if k == "_id":
                continue
            if isinstance(v, datetime.datetime):
                if hasattr(model_cls, "__mapper__") and k in model_cls.__mapper__.columns:
                    col_type = model_cls.__mapper__.columns[k].type
                    from sqlalchemy import Date
                    if isinstance(col_type, Date):
                        v = v.date()
                else:
                    if k in ("date", "forecast_date"):
                        v = v.date()
            instance.__dict__[k] = v
            
        # Populate missing properties with column defaults
        if hasattr(model_cls, "__mapper__"):
            for col in model_cls.__mapper__.columns:
                k = col.key
                if k not in instance.__dict__:
                    val = None
                    if col.default is not None:
                        val = col.default.arg
                        if callable(val):
                            try:
                                val = val()
                            except Exception:
                                val = val(None)
                    elif col.server_default is not None:
                        arg_str = str(col.server_default.arg).strip("'\"")
                        if arg_str.lower() in ("0", "false"):
                            val = False
                        elif arg_str.lower() in ("1", "true"):
                            val = True
                        else:
                            val = arg_str
                    if val is not None:
                        instance.__dict__[k] = val
        return instance

    class MongoQuery:
        """Mongo query builder shim implementing SQLAlchemy Query API."""
        def __init__(self, db, args):
            self.db = db
            self.args = args
            self.filter_dict = {}
            self.sort_fields = []
            self.limit_val = None
            self.offset_val = None
            self.group_fields = []
            self.joined_models = []
            
            self.model_class = None
            import re
            for arg in args:
                if hasattr(arg, "class_"):
                    self.model_class = arg.class_
                    break
                s = str(arg)
                m = re.search(r'([a-zA-Z_0-9]+)\.[a-zA-Z_0-9]+', s)
                if m:
                    tbl_name = m.group(1)
                    if hasattr(Base, "registry"):
                        for mapper in Base.registry.mappers:
                            cls = mapper.class_
                            if hasattr(cls, "__tablename__") and cls.__tablename__ == tbl_name:
                                self.model_class = cls
                                break
                    if self.model_class:
                        break
            if not self.model_class and len(args) == 1 and isinstance(args[0], type):
                self.model_class = args[0]
                
        @staticmethod
        def _coerce_dates(v):
            """Recursively convert datetime.date → datetime.datetime for PyMongo."""
            if isinstance(v, datetime.datetime):
                return v
            if isinstance(v, datetime.date):
                return datetime.datetime.combine(v, datetime.time.min)
            if isinstance(v, dict):
                return {sk: MongoQuery._coerce_dates(sv) for sk, sv in v.items()}
            return v

        def filter(self, *conditions):
            for cond in conditions:
                if isinstance(cond, dict):
                    for k, v in cond.items():
                        v = MongoQuery._coerce_dates(v)
                        if k in self.filter_dict and isinstance(self.filter_dict[k], dict) and isinstance(v, dict):
                            self.filter_dict[k].update(v)
                        else:
                            self.filter_dict[k] = v
            return self
            
        def filter_by(self, **kwargs):
            for k, v in kwargs.items():
                self.filter_dict[k] = MongoQuery._coerce_dates(v)
            return self
            
        def order_by(self, *sort_exprs):
            for expr in sort_exprs:
                parsed = self._parse_sort(expr)
                if parsed:
                    self.sort_fields.append(parsed)
            return self
            
        def limit(self, val):
            self.limit_val = val
            return self
            
        def offset(self, val):
            self.offset_val = val
            return self
            
        def group_by(self, *fields):
            for f in fields:
                if hasattr(f, "key"):
                    self.group_fields.append(f.key)
                elif isinstance(f, str):
                    self.group_fields.append(f)
            return self
            
        def join(self, joined_model, *join_conds):
            self.joined_models.append(joined_model)
            return self

        def options(self, *args):
            return self

        def scalar(self):
            res = self.all()
            if not res:
                # Fallback for count/sum aggregates on empty match cursors
                is_aggregate = False
                for arg in self.args:
                    expr = arg
                    if not isinstance(expr, type) and expr.__class__.__name__ == "Label" and hasattr(expr, "element"):
                        expr = expr.element
                    if not isinstance(expr, type) and hasattr(expr, "name") and expr.name.lower() in ("count", "sum"):
                        is_aggregate = True
                        break
                if is_aggregate:
                    return 0
                return None
            first_item = res[0]
            if isinstance(first_item, RowTuple):
                keys = first_item._keys
                if keys:
                    return getattr(first_item, keys[0])
            elif hasattr(first_item, "id"):
                return first_item.id
            elif isinstance(first_item, dict):
                return list(first_item.values())[0] if first_item else None
            return first_item

        def first(self):
            res = self.limit(1).all()
            return res[0] if res else None

        def count(self):
            collection_name = self.model_class.__tablename__
            return self.db[collection_name].count_documents(self.filter_dict)

        def delete(self, synchronize_session=False):
            collection_name = self.model_class.__tablename__
            res = self.db[collection_name].delete_many(self.filter_dict)
            return res.deleted_count

        def update(self, values, synchronize_session=False):
            collection_name = self.model_class.__tablename__
            update_dict = {}
            for k, v in values.items():
                field_name = k.key if hasattr(k, "key") else str(k)
                update_dict[field_name] = v
            self.db[collection_name].update_many(self.filter_dict, {"$set": update_dict})
            return self.count()

        def all(self):
            collection_name = self.model_class.__tablename__
            if self.joined_models or self.group_fields or self._has_aggregates():
                return self._run_aggregation_pipeline()
                
            cursor = self.db[collection_name].find(self.filter_dict)
            if self.sort_fields:
                cursor = cursor.sort(self.sort_fields)
            if self.offset_val is not None:
                cursor = cursor.skip(self.offset_val)
            if self.limit_val is not None:
                cursor = cursor.limit(self.limit_val)
                
            results = []
            for doc in cursor:
                results.append(from_dict(self.model_class, doc))
            return results

        def _has_aggregates(self):
            for arg in self.args:
                if not isinstance(arg, type) and hasattr(arg, "name"):
                    return True
            return False

        def _parse_sort(self, sort_expr):
            if isinstance(sort_expr, tuple):
                return sort_expr
            if hasattr(sort_expr, "key") and sort_expr.key is not None:
                return (sort_expr.key, 1)
            if isinstance(sort_expr, str):
                return (sort_expr, 1)
            
            s_str = str(sort_expr).lower()
            direction = -1 if "desc" in s_str else 1
            field = s_str.split()[0]
            if hasattr(sort_expr, "element"):
                if hasattr(sort_expr.element, "key") and sort_expr.element.key is not None:
                    field = sort_expr.element.key
                elif hasattr(sort_expr.element, "name") and sort_expr.element.name is not None:
                    field = sort_expr.element.name
                else:
                    field = str(sort_expr.element)
            return (field, direction)

        def _run_aggregation_pipeline(self):
            collection_name = self.model_class.__tablename__
            pipeline = []
            
            # 1. Lookups/Joins
            for joined in self.joined_models:
                joined_tbl = joined.__tablename__
                local_field = "id"
                foreign_field = "id"
                if collection_name == "anomalies" and joined_tbl == "cost_records":
                    local_field = "cost_record_id"
                elif collection_name == "cost_records" and joined_tbl == "users":
                    local_field = "user_id"
                elif collection_name == "cost_records" and joined_tbl == "aws_accounts":
                    local_field = "aws_account_id"
                    
                pipeline.append({
                    "$lookup": {
                        "from": joined_tbl,
                        "localField": local_field,
                        "foreignField": foreign_field,
                        "as": f"joined_{joined_tbl}"
                    }
                })
                pipeline.append({
                    "$unwind": {
                        "path": f"$joined_{joined_tbl}",
                        "preserveNullAndEmptyArrays": True
                    }
                })
                
            mapped_filters = {}
            for k, v in self.filter_dict.items():
                found_joined = False
                for joined in self.joined_models:
                    joined_tbl = joined.__tablename__
                    if hasattr(joined, k):
                        mapped_filters[f"joined_{joined_tbl}.{k}"] = v
                        found_joined = True
                        break
                if not found_joined:
                    mapped_filters[k] = v
                    
            if mapped_filters:
                # Convert dates/datetimes to ISO or native check inside filters
                for mk, mv in list(mapped_filters.items()):
                    if isinstance(mv, datetime.date) and not isinstance(mv, datetime.datetime):
                        mapped_filters[mk] = datetime.datetime.combine(mv, datetime.time.min)
                    elif isinstance(mv, dict):
                        for subk, subv in list(mv.items()):
                            if isinstance(subv, datetime.date) and not isinstance(subv, datetime.datetime):
                                mv[subk] = datetime.datetime.combine(subv, datetime.time.min)
                pipeline.append({"$match": mapped_filters})
                
            # Pre-addFields if strftime functions exist in target args
            for arg in self.args:
                expr = arg
                if not isinstance(expr, type) and expr.__class__.__name__ == "Label" and hasattr(expr, "element"):
                    expr = expr.element

                if not isinstance(expr, type) and hasattr(expr, "name") and expr.name.lower() == "strftime":
                    func_name = expr.name.lower()
                    label = getattr(arg, "name", "month")
                    if not label or label == "strftime":
                        label = getattr(arg, "_label", "month") or "month"
                    if label is None:
                        label = "month"

                    fmt = "%Y-%m"
                    field = "date"
                    if hasattr(expr, "get_children"):
                        for c in expr.get_children():
                            if hasattr(c, "value"):
                                fmt = str(c.value)
                            elif hasattr(c, "key"):
                                field = c.key
                    fmt = fmt.replace("%Y", "%Y").replace("%m", "%m").replace("%d", "%d")
                    pipeline.append({
                        "$addFields": {
                            label: {
                                "$dateToString": {
                                    "format": fmt,
                                    "date": f"${field}"
                                }
                            }
                        }
                    })

            # 2. Grouping stage
            if self.group_fields or self._has_aggregates():
                group_id = {}
                if len(self.group_fields) == 1:
                    group_id = f"${self.group_fields[0]}"
                elif len(self.group_fields) > 1:
                    group_id = {f: f"${f}" for f in self.group_fields}
                else:
                    group_id = None
                    
                group_stage = {"_id": group_id}
                
                for arg in self.args:
                    expr = arg
                    label = None
                    if not isinstance(expr, type) and expr.__class__.__name__ == "Label" and hasattr(expr, "element"):
                        label = getattr(expr, "name", None)
                        expr = expr.element

                    if not isinstance(expr, type) and hasattr(expr, "name"):
                        func_name = expr.name.lower()
                        target_field = "id"
                        s = str(expr)
                        import re
                        m = re.search(r'\((?:[a-zA-Z_0-9]+\.)?([a-zA-Z_0-9]+)\)', s)
                        if m:
                            target_field = m.group(1)
                        
                        if not label:
                            label = getattr(arg, "_label", None) or func_name or "total"
                        if label is None:
                            label = "total"
                        if not isinstance(label, str):
                            label = str(label)
                        if func_name == "sum":
                            group_stage[label] = {"$sum": f"${target_field}"}
                        elif func_name == "count":
                            group_stage[label] = {"$sum": 1}
                            
                pipeline.append({"$group": group_stage})
                
                project_stage = {"_id": 0}
                if len(self.group_fields) == 1:
                    project_stage[self.group_fields[0]] = "$_id"
                elif len(self.group_fields) > 1:
                    for f in self.group_fields:
                        project_stage[f] = f"$_id.{f}"
                for k in group_stage.keys():
                    if k != "_id":
                        project_stage[k] = 1
                pipeline.append({"$project": project_stage})
                
            # 3. Sorting
            if self.sort_fields:
                sort_dict = {}
                for field, direction in self.sort_fields:
                    sort_dict[field] = direction
                pipeline.append({"$sort": sort_dict})
                
            # 4. Limit/Offset
            if self.offset_val is not None:
                pipeline.append({"$skip": self.offset_val})
            if self.limit_val is not None:
                pipeline.append({"$limit": self.limit_val})
                
            cursor = self.db[collection_name].aggregate(pipeline)
            results = []
            for doc in cursor:
                if not isinstance(self.args[0], type):
                    results.append(RowTuple(**doc))
                else:
                    results.append(from_dict(self.model_class, doc))
            return results

    class MongoSession:
        """Mongo DB session shim implementing SQLAlchemy Session APIs."""
        def __init__(self, client):
            self.client = client
            self.db = client.get_default_database()
            self._pending_adds = []

        def query(self, *args):
            return MongoQuery(self.db, args)

        def add(self, obj):
            if obj not in self._pending_adds:
                self._pending_adds.append(obj)

        def add_all(self, objects):
            for obj in objects:
                self.add(obj)

        def bulk_save_objects(self, objects):
            """Efficiently insert/upsert a list of ORM objects via PyMongo insert_many."""
            from collections import defaultdict
            by_table = defaultdict(list)
            for obj in objects:
                d = to_dict(obj)
                by_table[obj.__tablename__].append(d)
            for tbl, docs in by_table.items():
                if docs:
                    # Use ordered=False for max throughput; upsert on 'id' field
                    from pymongo import UpdateOne
                    ops = [UpdateOne({"id": d["id"]}, {"$set": d}, upsert=True) for d in docs]
                    self.db[tbl].bulk_write(ops, ordered=False)

        def execute(self, statement, params=None):
            s_str = str(statement).strip().upper()
            if "SELECT 1" in s_str:
                self.client.admin.command('ping')
                class DummyResult:
                    def scalar(self):
                        return 1
                    def first(self):
                        return (1,)
                    def all(self):
                        return [(1,)]
                return DummyResult()
            raise NotImplementedError(f"Raw SQL execution is not supported in MongoDB mode: {s_str}")

        def commit(self):
            for obj in self._pending_adds:
                tbl = obj.__tablename__
                d = to_dict(obj)
                self.db[tbl].replace_one({"id": obj.id}, d, upsert=True)
            self._pending_adds.clear()

        def rollback(self):
            self._pending_adds.clear()

        def close(self):
            pass

        def delete(self, obj):
            tbl = obj.__tablename__
            self.db[tbl].delete_one({"id": obj.id})

        def refresh(self, obj):
            tbl = obj.__tablename__
            doc = self.db[tbl].find_one({"id": obj.id})
            if doc:
                for k, v in doc.items():
                    if k == "_id":
                        continue
                    setattr(obj, k, v)

    def _load_rel_one(self, model_cls, fk_name):
        cache_name = f"_cached_{model_cls.__name__.lower()}"
        if not hasattr(self, cache_name):
            fk_val = getattr(self, fk_name, None)
            if fk_val:
                db = MongoSession(mongo_client)
                setattr(self, cache_name, db.query(model_cls).filter_by(id=fk_val).first())
            else:
                setattr(self, cache_name, None)
        return getattr(self, cache_name)

    def _set_rel_one(self, fk_name, val):
        model_name = val.__class__.__name__.lower() if val else "rel"
        setattr(self, f"_cached_{model_name}", val)
        if val:
            setattr(self, fk_name, val.id)
        else:
            setattr(self, fk_name, None)

    def _load_rel_many(self, model_cls, fk_name):
        cache_name = f"_cached_{model_cls.__name__.lower()}_list"
        if not hasattr(self, cache_name):
            if hasattr(self, "id") and self.id:
                db = MongoSession(mongo_client)
                setattr(self, cache_name, db.query(model_cls).filter(getattr(model_cls, fk_name) == self.id).all())
            else:
                setattr(self, cache_name, [])
        return getattr(self, cache_name)

    def _load_rel_one_reverse(self, model_cls, fk_name):
        cache_name = f"_cached_{model_cls.__name__.lower()}"
        if not hasattr(self, cache_name):
            if hasattr(self, "id") and self.id:
                db = MongoSession(mongo_client)
                setattr(self, cache_name, db.query(model_cls).filter(getattr(model_cls, fk_name) == self.id).first())
            else:
                setattr(self, cache_name, None)
        return getattr(self, cache_name)

    def _set_rel_one_reverse(self, val):
        if val:
            model_name = val.__class__.__name__.lower()
            setattr(self, f"_cached_{model_name}", val)

    def patch_mongodb_relationships():
        logger.info("Injecting dynamic relation property descriptors on Mongo models...")
        from app.models.user import User
        from app.models.organization import Organization
        from app.models.aws_account import AWSAccount
        from app.models.cost_record import CostRecord
        from app.models.anomaly import Anomaly
        from app.models.budget import Budget
        from app.models.recommendation import Recommendation
        from app.models.forecast import Forecast
        from app.models.report import Report
        from app.models.audit_log import AuditLog
        from app.models.settings import UserSettings
        
        User.organization = property(
            lambda self: _load_rel_one(self, Organization, "org_id"),
            lambda self, val: _set_rel_one(self, "org_id", val)
        )
        User.settings = property(
            lambda self: _load_rel_one_reverse(self, UserSettings, "user_id"),
            lambda self, val: _set_rel_one_reverse(val)
        )
        
        Organization.users = property(
            lambda self: _load_rel_many(self, User, "org_id")
        )
        Organization.aws_accounts = property(
            lambda self: _load_rel_many(self, AWSAccount, "org_id")
        )
        
        AWSAccount.organization = property(
            lambda self: _load_rel_one(self, Organization, "org_id"),
            lambda self, val: _set_rel_one(self, "org_id", val)
        )
        
        CostRecord.aws_account = property(
            lambda self: _load_rel_one(self, AWSAccount, "aws_account_id"),
            lambda self, val: _set_rel_one(self, "aws_account_id", val)
        )
        CostRecord.user = property(
            lambda self: _load_rel_one(self, User, "user_id"),
            lambda self, val: _set_rel_one(self, "user_id", val)
        )
        
        Anomaly.cost_record = property(
            lambda self: _load_rel_one(self, CostRecord, "cost_record_id"),
            lambda self, val: _set_rel_one(self, "cost_record_id", val)
        )
        
        Budget.user = property(
            lambda self: _load_rel_one(self, User, "user_id"),
            lambda self, val: _set_rel_one(self, "user_id", val)
        )
        Recommendation.user = property(
            lambda self: _load_rel_one(self, User, "user_id"),
            lambda self, val: _set_rel_one(self, "user_id", val)
        )
        Forecast.user = property(
            lambda self: _load_rel_one(self, User, "user_id"),
            lambda self, val: _set_rel_one(self, "user_id", val)
        )
        Report.user = property(
            lambda self: _load_rel_one(self, User, "user_id"),
            lambda self, val: _set_rel_one(self, "user_id", val)
        )
        AuditLog.user = property(
            lambda self: _load_rel_one(self, User, "user_id"),
            lambda self, val: _set_rel_one(self, "user_id", val)
        )
        UserSettings.user = property(
            lambda self: _load_rel_one(self, User, "user_id"),
            lambda self, val: _set_rel_one(self, "user_id", val)
        )

    SessionLocal = lambda: MongoSession(mongo_client)
    patch_mongodb_relationships()

# Relational SQL (Postgres / SQLite) translation layer
else:
    engine_kwargs = {
        "pool_pre_ping": True,
        "echo": settings.DEBUG,
    }
    if is_sqlite_db:
        connect_args = {"check_same_thread": False}
        engine = create_engine(
            settings.DATABASE_URL, connect_args=connect_args, **engine_kwargs
        )
    else:
        # Production-grade PostgreSQL pool configurations
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_recycle"] = 1800
        engine_kwargs["pool_timeout"] = 30
        
        postgres_connected = False
        last_error = None
        max_attempts = 5 if settings.ENVIRONMENT.lower() == "production" else 1
        for attempt in range(max_attempts):
            try:
                logger.info("Connecting to PostgreSQL database (Attempt %d/%d)...", attempt + 1, max_attempts)
                temp_engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
                with temp_engine.connect() as conn:
                    pass
                engine = temp_engine
                postgres_connected = True
                logger.info("Connected to PostgreSQL successfully.")
                break
            except (OperationalError, Exception) as e:
                last_error = e
                logger.warning("PostgreSQL connection attempt %d failed: %s", attempt + 1, e)
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)

        if not postgres_connected:
            if settings.ENVIRONMENT.lower() == "production":
                logger.critical("FATAL: Could not connect to production PostgreSQL/RDS database. Error: %s", last_error)
                raise RuntimeError(f"Failed to connect to production database: {last_error}")
            else:
                logger.warning("PostgreSQL connection failed. Falling back to SQLite for local development. Error: %s", last_error)
                is_sqlite_db = True
                connect_args = {"check_same_thread": False}
                engine_kwargs = {
                    "pool_pre_ping": True,
                    "echo": settings.DEBUG,
                }
                engine = create_engine(
                    fallback_sqlite_url, connect_args=connect_args, **engine_kwargs
                )

    if is_sqlite_db:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Any, None, None]:
    """FastAPI dependency for database sessions with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables / indexes and run programmatic migrations."""
    if is_mongodb:
        logger.info("Initializing MongoDB collection indexes...")
        db = mongo_client.get_default_database()
        db["users"].create_index("email", unique=True)
        db["organizations"].create_index("slug", unique=True)
        db["aws_accounts"].create_index("account_id", unique=True)
        db["cost_records"].create_index([("aws_account_id", 1), ("date", 1), ("service", 1)])
        db["anomalies"].create_index("cost_record_id")
        db["budgets"].create_index("user_id")

        # New Demo & AWS Collections
        db["demo_users"].create_index("user_id", unique=True)
        db["demo_cost_records"].create_index("user_id")
        db["aws_cost_records"].create_index("aws_account_id")
        db["demo_anomalies"].create_index("cost_record_id")
        db["aws_anomalies"].create_index("cost_record_id")
        db["demo_budgets"].create_index("user_id")
        db["aws_budgets"].create_index("user_id")
        db["demo_recommendations"].create_index("user_id")
        db["aws_recommendations"].create_index("user_id")
        db["demo_forecasts"].create_index("user_id")
        db["aws_forecasts"].create_index("user_id")
        db["demo_reports"].create_index("user_id")
        db["aws_reports"].create_index("user_id")
        db["aws_resources"].create_index("aws_account_id")
        db["aws_billing"].create_index("aws_account_id")
        return

    import app.models
    Base.metadata.create_all(bind=engine)

    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("users")]
            with engine.begin() as conn:
                if "account_status" not in columns:
                    logger.info("Database migration: adding column 'account_status' to users table")
                    conn.execute(text("ALTER TABLE users ADD COLUMN account_status VARCHAR(20) DEFAULT 'active'"))
                if "last_login" not in columns:
                    logger.info("Database migration: adding column 'last_login' to users table")
                    conn.execute(text("ALTER TABLE users ADD COLUMN last_login TIMESTAMP"))
                
                logger.info("Database migration: migrating legacy user roles to uppercase")
                conn.execute(text("UPDATE users SET role = 'USER' WHERE role IN ('viewer', 'manager', 'user', 'viewers') OR role IS NULL"))
                conn.execute(text("UPDATE users SET role = 'ADMIN' WHERE role IN ('admin', 'admins')"))

        if "aws_accounts" in inspector.get_table_names():
            aws_columns = [col["name"] for col in inspector.get_columns("aws_accounts")]
            if "is_demo" not in aws_columns:
                with engine.begin() as conn:
                    logger.info("Database migration: adding column 'is_demo' to aws_accounts table")
                    conn.execute(text("ALTER TABLE aws_accounts ADD COLUMN is_demo BOOLEAN DEFAULT FALSE"))
    except Exception as e:
        logger.warning("Programmatic database schema upgrade warning: %s", e)


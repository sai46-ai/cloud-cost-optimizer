"""
Structured logging setup for production.
Outputs JSON logs natively compatible with DataDog, ELK, Splunk, etc.
"""

import logging
import json
from datetime import datetime, timezone
import traceback


class JSONFormatter(logging.Formatter):
    """Formatter that outputs JSON strings after parsing the LogRecord."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        # Include extra attributes injected via logger.info("..", extra={"foo":"bar"})
        for key, value in record.__dict__.items():
            if key not in [
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            ]:
                # To prevent serialization errors
                try:
                    json.dumps(value)
                    log_data[key] = value
                except TypeError:
                    log_data[key] = str(value)

        return json.dumps(log_data)


import os
import queue
import threading
import time
import boto3

class CloudWatchLogHandler(logging.Handler):
    """Background-threaded logging handler that pushes formatted messages to Amazon CloudWatch."""
    
    def __init__(self, log_group_name: str, log_stream_name: str, region_name: str = "us-east-1"):
        super().__init__()
        self.log_group_name = log_group_name
        self.log_stream_name = log_stream_name
        self.region_name = region_name
        self.queue: queue.Queue = queue.Queue()
        self.client = None
        self.sequence_token = None
        self.active = True
        
        # Start a background daemon worker thread to prevent blocking requests
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _worker(self):
        # Gracefully handle missing credentials or network errors on EC2/boto3
        try:
            self.client = boto3.client("logs", region_name=self.region_name)
            # Ensure the log group exists
            try:
                self.client.create_log_group(logGroupName=self.log_group_name)
            except Exception:
                pass
            
            # Ensure the log stream exists
            try:
                self.client.create_log_stream(
                    logGroupName=self.log_group_name,
                    logStreamName=self.log_stream_name
                )
            except Exception:
                pass
        except Exception as e:
            print(f"WARNING: CloudWatch Logging init failed: {e}. Falling back to standard logs only.")
            self.active = False
            return

        while self.active:
            batch = []
            start_time = time.time()
            # Batch logs for efficiency, wait at most 2.0s
            while len(batch) < 100 and (time.time() - start_time) < 2.0:
                try:
                    record = self.queue.get(timeout=0.1)
                    batch.append(record)
                    self.queue.task_done()
                except queue.Empty:
                    if batch:
                        break
                    continue
            
            if batch:
                log_events = []
                for rec in batch:
                    try:
                        timestamp = int(rec.created * 1000)
                        message = self.format(rec)
                        log_events.append({"timestamp": timestamp, "message": message})
                    except Exception:
                        pass
                
                if log_events:
                    log_events.sort(key=lambda x: x["timestamp"])
                    kwargs = {
                        "logGroupName": self.log_group_name,
                        "logStreamName": self.log_stream_name,
                        "logEvents": log_events,
                    }
                    if self.sequence_token:
                        kwargs["sequenceToken"] = self.sequence_token
                    
                    try:
                        resp = self.client.put_log_events(**kwargs)
                        self.sequence_token = resp.get("nextSequenceToken")
                    except Exception as e:
                        # If invalid sequence token or token mismatch, retry without sequence token
                        try:
                            # In modern logs APIs sequence token is optional
                            kwargs.pop("sequenceToken", None)
                            resp = self.client.put_log_events(**kwargs)
                            self.sequence_token = resp.get("nextSequenceToken")
                        except Exception as inner_ex:
                            print(f"Failed to put log events to CloudWatch: {inner_ex}")
                            time.sleep(1)

    def emit(self, record):
        if self.active:
            self.queue.put(record)

    def close(self):
        self.active = False
        super().close()


def configure_logging(is_production: bool = False, debug: bool = False):
    """Configure the root logger."""
    level = logging.DEBUG if debug else logging.INFO

    root_logger = logging.getLogger()
    # Remove existing handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    # Standard Console Handler
    console_handler = logging.StreamHandler()
    if is_production:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root_logger.addHandler(console_handler)

    # CloudWatch Logs Handler (Production Only)
    if is_production:
        group_name = os.getenv("CLOUDWATCH_LOG_GROUP", "/cloudwise/backend")
        stream_name = os.getenv("CLOUDWATCH_LOG_STREAM", "backend-stream")
        region = os.getenv("AWS_REGION", "us-east-1")
        
        cw_handler = CloudWatchLogHandler(
            log_group_name=group_name,
            log_stream_name=stream_name,
            region_name=region
        )
        cw_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(cw_handler)

    root_logger.setLevel(level)

    # Set third-party loggers
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING if is_production else logging.INFO
    )
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if not debug else logging.INFO
    )

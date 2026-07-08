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


def configure_logging(is_production: bool = False, debug: bool = False):
    """Configure the root logger."""
    level = logging.DEBUG if debug else logging.INFO

    root_logger = logging.getLogger()
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()

    if is_production:
        handler.setFormatter(JSONFormatter())
    else:
        # standard console output for dev
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Set third-party loggers
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING if is_production else logging.INFO
    )
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if not debug else logging.INFO
    )

import logging
import json
import traceback
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    Ideal for structured logging in microservices.
    """
    def __init__(self, service_name: str, **kwargs):
        super().__init__()
        self.service_name = service_name
        self.default_kwargs = kwargs

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": self.service_name,
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            **self.default_kwargs
        }

        # Include standard extra attributes if they exist
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = "".join(traceback.format_exception(*record.exc_info))
            
        return json.dumps(log_record)

def get_logger(name: str, service_name: str, level: int = logging.INFO) -> logging.Logger:
    """Creates a structured JSON logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if get_logger is called multiple times
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JSONFormatter(service_name=service_name))
        logger.addHandler(console_handler)
        
    # Do not propagate to root logger
    logger.propagate = False
    return logger

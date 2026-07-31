import logging
import json
import sys
import time
from typing import Dict, Any

class StructuredJSONFormatter(logging.Formatter):
    """
    Formats log records as structured JSON with correlation context.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Context enrichment
        for key in ["request_id", "user_id", "trace_id", "execution_ms"]:
            if hasattr(record, key):
                log_obj[key] = getattr(record, key)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

def setup_structured_logging():
    logger = logging.getLogger("streamora")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJSONFormatter())
        logger.addHandler(handler)

    return logger

structured_logger = setup_structured_logging()

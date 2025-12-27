import logging
from logging.handlers import RotatingFileHandler
import os
import structlog

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "logs/telemetry.log")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

console = logging.StreamHandler()
console.setLevel(LOG_LEVEL)

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
file_handler.setLevel(LOG_LEVEL)

root = logging.getLogger()
root.setLevel(LOG_LEVEL)
root.handlers.clear()
root.addHandler(console)
root.addHandler(file_handler)

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

console.setFormatter(structlog.stdlib.ProcessorFormatter(
    processor=structlog.dev.ConsoleRenderer()
))
file_handler.setFormatter(structlog.stdlib.ProcessorFormatter(
    processor=structlog.processors.JSONRenderer()
))

logger = structlog.get_logger()

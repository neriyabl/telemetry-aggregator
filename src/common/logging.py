import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def setup_logging(service_name: str, log_file_path: str | None = None):
    """
    Setup logging for a specific service with separate log files.

    Args:
        service_name: Name of the service (e.g., 'telemetry-simulator', 'telemetry-api')
        log_file_path: Optional custom log file path. If None, uses logs/{service_name}.log
    """
    if log_file_path is None:
        log_file_path = f"logs/{service_name}.log"

    # Ensure log directory exists
    Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)

    # Console handler with readable format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))

    # File handler with JSON format for this specific service
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))

    # Clear any existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        handlers=[console_handler, file_handler],
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(processor=structlog.dev.ConsoleRenderer())
    )
    file_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer()
        )
    )


def get_logger(name: str | None = None):
    """Get a logger with proper module name."""
    return structlog.get_logger(name)

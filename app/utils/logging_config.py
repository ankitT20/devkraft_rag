"""
Logging configuration for the RAG application.
Creates separate log files for app logs and error logs.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logging() -> tuple[logging.Logger, logging.Logger]:
    """
    Set up logging configuration with separate app and error logs.

    Returns:
        Tuple of (app_logger, error_logger)
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Generate log file names with date
    date_str = datetime.now().strftime("%Y%m%d")
    app_log_file = logs_dir / f"app_logs_{date_str}.log"
    error_log_file = logs_dir / f"errors_{date_str}.log"

    # Create app logger (INFO and above)
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_logger.handlers.clear()

    # Create error logger (ERROR and above)
    error_logger = logging.getLogger("error")
    error_logger.setLevel(logging.ERROR)
    error_logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # App log file handler
    app_handler = logging.FileHandler(app_log_file)
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(detailed_formatter)
    app_logger.addHandler(app_handler)

    # App console handler
    app_console_handler = logging.StreamHandler()
    app_console_handler.setLevel(logging.INFO)
    app_console_handler.setFormatter(detailed_formatter)
    app_logger.addHandler(app_console_handler)

    # Error log file handler
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    error_logger.addHandler(error_handler)

    # Error console handler
    error_console_handler = logging.StreamHandler()
    error_console_handler.setLevel(logging.ERROR)
    error_console_handler.setFormatter(detailed_formatter)
    error_logger.addHandler(error_console_handler)

    app_logger.info(f"Logging initialized. App log: {app_log_file}, Error log: {error_log_file}")

    return app_logger, error_logger


# Global logger instances
app_logger, error_logger = setup_logging()

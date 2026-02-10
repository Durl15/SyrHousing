"""
Centralized logging configuration for SyrHousing backend.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(app_name: str = "syrhousing", log_dir: str = "logs", level: int = logging.INFO):
    """
    Configure application-wide logging with both file and console output.

    Args:
        app_name: Name for the logger and log files
        log_dir: Directory to store log files
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler for all logs (rotating)
    all_log_file = log_path / f"{app_name}_all.log"
    all_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(detailed_formatter)

    # File handler for errors only (rotating)
    error_log_file = log_path / f"{app_name}_errors.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)

    # Add handlers to logger
    logger.addHandler(all_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "syrhousing") -> logging.Logger:
    """
    Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_api_call(logger: logging.Logger, endpoint: str, method: str, user_id: str = None, **kwargs):
    """
    Log API call details.

    Args:
        logger: Logger instance
        endpoint: API endpoint path
        method: HTTP method
        user_id: User ID if authenticated
        **kwargs: Additional parameters to log
    """
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    user_info = f"User: {user_id}" if user_id else "Anonymous"
    logger.info(f"API Call: {method} {endpoint} | {user_info}{' | ' + extra_info if extra_info else ''}")


def log_error(logger: logging.Logger, error: Exception, context: str = "", **kwargs):
    """
    Log error with context and additional details.

    Args:
        logger: Logger instance
        error: Exception object
        context: Context where error occurred
        **kwargs: Additional error details
    """
    error_type = type(error).__name__
    error_msg = str(error)
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])

    logger.error(
        f"Error in {context}: {error_type}: {error_msg}{' | ' + extra_info if extra_info else ''}",
        exc_info=True
    )


def log_database_operation(logger: logging.Logger, operation: str, table: str, record_id: str = None, **kwargs):
    """
    Log database operation.

    Args:
        logger: Logger instance
        operation: Type of operation (INSERT, UPDATE, DELETE, SELECT)
        table: Database table name
        record_id: Record ID if applicable
        **kwargs: Additional operation details
    """
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    record_info = f"ID: {record_id}" if record_id else ""
    logger.debug(
        f"DB Operation: {operation} | Table: {table}{' | ' + record_info if record_info else ''}{' | ' + extra_info if extra_info else ''}"
    )


# Initialize default logger
default_logger = setup_logging()

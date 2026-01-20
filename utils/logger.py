"""
Centralized logging utility
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from config.settings import LoggingConfig


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: str = LoggingConfig.LEVEL
) -> logging.Logger:
    """
    Set up a logger with file and console handlers

    Args:
        name: Logger name (usually __name__)
        log_file: Optional specific log file path
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        LoggingConfig.FORMAT,
        datefmt=LoggingConfig.DATE_FORMAT
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_path = log_file or LoggingConfig.LOG_FILE
    file_handler = logging.FileHandler(file_path, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with standard configuration

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return setup_logger(name)

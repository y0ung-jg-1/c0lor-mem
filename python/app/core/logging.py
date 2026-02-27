"""Structured logging module for the Python backend."""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Configured logger with stdout handler
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

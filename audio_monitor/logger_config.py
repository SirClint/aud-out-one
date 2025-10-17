import logging
import os

# Define custom log levels if needed, or map to standard ones
# For simplicity, we'll map FINE to DEBUG for now.
LOG_LEVEL_MAP = {
    'FINE': logging.DEBUG,
    'DEBUG': logging.DEBUG,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

DEFAULT_LOG_LEVEL = 'WARNING' # Minimal log level by default

def setup_logging(log_level_str: str = DEFAULT_LOG_LEVEL):
    """
    Sets up the logging configuration for the application.

    Args:
        log_level_str: The desired log level as a string (e.g., 'DEBUG', 'INFO', 'WARNING').
    """
    log_level = LOG_LEVEL_MAP.get(log_level_str.upper(), logging.WARNING)

    # Create a logger
    logger = logging.getLogger('audio_monitor')
    logger.setLevel(log_level)

    # Prevent adding multiple handlers if setup is called multiple times
    if not logger.handlers:
        # Create console handler and set level
        ch = logging.StreamHandler()
        ch.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Add formatter to ch
        ch.setFormatter(formatter)

        # Add ch to logger
        logger.addHandler(ch)

    # Set the level for existing handlers if setup is called again with a new level
    for handler in logger.handlers:
        handler.setLevel(log_level)

    return logger

# Initialize logger for modules to import
logger = setup_logging()

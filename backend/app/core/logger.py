import logging
import sys

from app.core.config import settings


def setup_logger() -> logging.Logger:
    """
    Configure and return the application's logger.
    """

    logger = logging.getLogger(settings.APP_NAME)

    # Prevent adding duplicate handlers when the app reloads
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
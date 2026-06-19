import logging
import sys
from logging.handlers import RotatingFileHandler

from .paths import RUNTIME_DIR


LOG_DIR = RUNTIME_DIR / "logs"
LOG_FILE = LOG_DIR / "fundrel.log"


def configure_logging(level=logging.INFO):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    if any(getattr(handler, "_fundrel_handler", False) for handler in root.handlers):
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler._fundrel_handler = True

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler._fundrel_handler = True

    root.addHandler(console_handler)
    root.addHandler(file_handler)


def get_logger(name):
    configure_logging()
    return logging.getLogger(name)

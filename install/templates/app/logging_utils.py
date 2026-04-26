from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

try:
    from app.config import settings
except ImportError:  # pragma: no cover - execução direta do script
    from config import settings


def setup_logging(component: str) -> logging.Logger:
    logs_dir = Path(settings.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger_name = f"autoreflex.{component}"
    logger = logging.getLogger(logger_name)
    if getattr(logger, "_autoreflex_configured", False):
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    info_handler = RotatingFileHandler(
        logs_dir / f"{component}.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)

    error_handler = RotatingFileHandler(
        logs_dir / f"{component}.error.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    logger._autoreflex_configured = True  # type: ignore[attr-defined]
    return logger

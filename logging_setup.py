# logging_setup.py
from __future__ import annotations
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

def _level_from_env(value: str | None) -> int:
    lv = (value or "").strip().upper()
    mapping = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARN": logging.WARNING,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return mapping.get(lv, logging.INFO)

def setup_logging(
    log_dir: str | Path = "logs",
    filename: str = "mini.log",
    level_env: str | None = None,
    console: bool = True,
) -> None:
    """
    Globale Logging-Konfiguration:
      - RotatingFileHandler logs/mini.log (5 × 5MB)
      - Console-Handler
      - Level aus LOG_LEVEL (default INFO)
    """
    level = _level_from_env(level_env or os.getenv("LOG_LEVEL"))
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / filename

    # Root-Logger sauber neu konfigurieren
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_h = RotatingFileHandler(str(log_path), maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    file_h.setLevel(level)
    file_h.setFormatter(fmt)
    root.addHandler(file_h)

    if console:
        sh = logging.StreamHandler()
        sh.setLevel(level)
        sh.setFormatter(fmt)
        root.addHandler(sh)

    # Laute 3rd-party Logger zähmen (außer wenn DEBUG)
    noisy = ["discord", "aiohttp", "urllib3", "requests"]
    if level > logging.DEBUG:
        for n in noisy:
            logging.getLogger(n).setLevel(logging.WARNING)

    logging.getLogger(__name__).info("Logging initialisiert: %s (Level=%s)", log_path, logging.getLevelName(level))

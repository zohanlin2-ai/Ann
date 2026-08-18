"""Persistent debug logging for Ann update diagnostics."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _logger(project_root: Path, logger_name: str, log_path: Path) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_update_logger(project_root: Path) -> logging.Logger:
    return _logger(project_root, "ann.update", project_root / "logs" / "ann-update.log")


def get_module_logger(project_root: Path, module_id: str, mirror_update_log: bool = False) -> logging.Logger:
    safe_id = "".join(character if character.isalnum() or character in "._-" else "_" for character in module_id)
    logger = _logger(project_root, f"ann.module.{module_id}", project_root / "logs" / "modules" / f"{safe_id}.log")
    if mirror_update_log:
        update_logger = get_update_logger(project_root)
        for handler in update_logger.handlers:
            if handler not in logger.handlers:
                logger.addHandler(handler)
    return logger

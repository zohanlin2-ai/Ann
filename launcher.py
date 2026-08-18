"""Stable bootstrap that starts Ann and applies verified full-project updates."""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler


ROOT = Path(__file__).resolve().parent
STAGED_CORE = ROOT / "backup_ann"
ROLLBACK_CORE = ROOT / "rollback_ann"
ACTIVE_CORE = ROOT / "Ann_core"
PRESERVED_NAMES = {".git", ".venv", "backup_ann", "rollback_ann", "launcher.py"}
PRESERVED_MODULE_NAMES = {"registry.json", "downloaded"}


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger("ann.launcher")
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger
    log_path = ROOT / "logs" / "ann-update.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


LOGGER = _configure_logger()


def run_core() -> int:
    environment = os.environ.copy()
    environment["ANN_PROJECT_ROOT"] = str(ROOT)
    environment["ANN_CORE_DIR"] = str(ACTIVE_CORE)
    command = [sys.executable, str(ACTIVE_CORE / "main.py")]
    LOGGER.info("Starting active Ann Core: %s", command)
    returncode = subprocess.call(command, cwd=ROOT, env=environment)
    LOGGER.info("Active Ann Core exited with returncode=%s", returncode)
    return returncode


def _wait_for_process_exit(process_id: int) -> None:
    """Wait for the running Ann process to release its project files."""
    LOGGER.info("Waiting for process %s to exit before applying update", process_id)
    while True:
        try:
            os.kill(process_id, 0)
        except OSError:
            LOGGER.info("Process %s has exited", process_id)
            return
        time.sleep(0.2)


def apply_verified_update() -> None:
    """Replace managed project files while preserving local data and this bootstrap."""
    if not STAGED_CORE.is_dir():
        raise RuntimeError("No verified backup_ann project is available.")
    LOGGER.info("Applying verified project update from %s", STAGED_CORE)
    if ROLLBACK_CORE.exists():
        shutil.rmtree(ROLLBACK_CORE)
    ROLLBACK_CORE.mkdir()
    managed_names = [item.name for item in STAGED_CORE.iterdir() if item.name not in PRESERVED_NAMES]
    LOGGER.info("Managed project entries to replace: %s", managed_names)
    for name in managed_names:
        current = ROOT / name
        if current.exists():
            destination = ROLLBACK_CORE / name
            if name == "modules":
                destination.mkdir()
                for item in current.iterdir():
                    if item.name not in PRESERVED_MODULE_NAMES:
                        copy_target = destination / item.name
                        if item.is_dir():
                            shutil.copytree(item, copy_target)
                        else:
                            shutil.copy2(item, copy_target)
            elif current.is_dir():
                shutil.copytree(current, destination)
            else:
                shutil.copy2(current, destination)
    for name in managed_names:
        current = ROOT / name
        staged = STAGED_CORE / name
        if name == "modules":
            current.mkdir(exist_ok=True)
            for item in staged.iterdir():
                if item.name in PRESERVED_MODULE_NAMES:
                    continue
                target = current / item.name
                if target.is_dir():
                    shutil.rmtree(target)
                elif target.exists():
                    target.unlink()
                if item.is_dir():
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)
            continue
        if current.is_dir():
            shutil.rmtree(current)
        elif current.exists():
            current.unlink()
        if staged.is_dir():
            shutil.copytree(staged, current)
        else:
            shutil.copy2(staged, current)
    shutil.rmtree(STAGED_CORE)
    LOGGER.info("Verified project update applied successfully; rollback stored in %s", ROLLBACK_CORE)
    print("The verified Ann project update was applied successfully.")


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--apply-update", action="store_true")
    parser.add_argument("--wait-for", type=int)
    arguments = parser.parse_args()
    if arguments.apply_update:
        try:
            if arguments.wait_for:
                _wait_for_process_exit(arguments.wait_for)
            apply_verified_update()
            return run_core()
        except Exception:
            LOGGER.exception("Failed to apply verified Ann project update")
            print("Ann update could not be applied. See logs/ann-update.log for details.")
            return 1
    if not ACTIVE_CORE.is_dir():
        print("Ann Core is missing. Restore Ann_core or download an update.")
        return 1
    return run_core()


if __name__ == "__main__":
    raise SystemExit(main())

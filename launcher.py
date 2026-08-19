"""Stable bootstrap that starts Ann and applies verified full-project updates."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from logging.handlers import RotatingFileHandler


ROOT = Path(__file__).resolve().parent
STAGED_CORE = ROOT / "backup_ann"
ROLLBACK_CORE = ROOT / "rollback_ann"
ACTIVE_CORE = ROOT / "Ann_core"
UPDATE_STATE = ROOT / ".ann-update-state.json"
READY_STATE = ROOT / ".ann-core-ready.json"
PRESERVED_NAMES = {".git", ".venv", "backup_ann", "rollback_ann", UPDATE_STATE.name}
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


@dataclass(frozen=True)
class CoreRun:
    returncode: int
    ready: bool


def run_core() -> CoreRun:
    if READY_STATE.exists():
        READY_STATE.unlink()
    environment = os.environ.copy()
    environment["ANN_PROJECT_ROOT"] = str(ROOT)
    environment["ANN_CORE_DIR"] = str(ACTIVE_CORE)
    environment["ANN_CORE_READY_FILE"] = str(READY_STATE)
    command = [sys.executable, str(ACTIVE_CORE / "main.py")]
    LOGGER.info("Starting active Ann Core: %s", command)
    process = subprocess.Popen(command, cwd=ROOT, env=environment)
    deadline = time.monotonic() + 30
    while not READY_STATE.exists():
        returncode = process.poll()
        if returncode is not None:
            LOGGER.error("Ann Core exited before Ready; returncode=%s", returncode)
            return CoreRun(returncode, False)
        if time.monotonic() >= deadline:
            LOGGER.error("Ann Core did not report Ready within 30 seconds")
            process.terminate()
            return CoreRun(process.wait(), False)
        time.sleep(0.1)
    LOGGER.info("Ann Core reported Ready")
    returncode = process.wait()
    LOGGER.info("Active Ann Core exited after Ready; returncode=%s", returncode)
    return CoreRun(returncode, True)


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
    UPDATE_STATE.write_text(
        json.dumps({"managed_names": managed_names, "rollback_attempted": False}, indent=2) + "\n",
        encoding="utf-8",
    )
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


def restore_rollback_update() -> None:
    """Restore the pre-update managed project after the new Core fails to start."""
    if not ROLLBACK_CORE.is_dir():
        raise RuntimeError("No rollback_ann project is available.")
    if not UPDATE_STATE.is_file():
        raise RuntimeError("No update state is available for rollback.")
    state = json.loads(UPDATE_STATE.read_text(encoding="utf-8"))
    if state.get("rollback_attempted"):
        raise RuntimeError("Automatic rollback was already attempted for this update.")
    managed_names = state.get("managed_names", [])
    if not isinstance(managed_names, list) or not all(isinstance(name, str) for name in managed_names):
        raise RuntimeError("The update state is invalid.")
    state["rollback_attempted"] = True
    UPDATE_STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    LOGGER.warning("Restoring rollback project after failed updated Core; entries=%s", managed_names)
    for name in managed_names:
        current = ROOT / name
        rollback = ROLLBACK_CORE / name
        if name == "modules":
            current.mkdir(exist_ok=True)
            for item in current.iterdir():
                if item.name in PRESERVED_MODULE_NAMES:
                    continue
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            if rollback.is_dir():
                for item in rollback.iterdir():
                    if item.name in PRESERVED_MODULE_NAMES:
                        continue
                    target = current / item.name
                    if item.is_dir():
                        shutil.copytree(item, target)
                    else:
                        shutil.copy2(item, target)
            continue
        if current.is_dir():
            shutil.rmtree(current)
        elif current.exists():
            current.unlink()
        if rollback.is_dir():
            shutil.copytree(rollback, current)
        elif rollback.is_file():
            shutil.copy2(rollback, current)
    LOGGER.info("Rollback project restored successfully from %s", ROLLBACK_CORE)


def clear_update_state() -> None:
    if UPDATE_STATE.exists():
        UPDATE_STATE.unlink()


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
            outcome = run_core()
            if outcome.ready:
                clear_update_state()
                if outcome.returncode != 0:
                    LOGGER.error("Updated Ann Core exited after Ready; returncode=%s", outcome.returncode)
                return outcome.returncode
            LOGGER.error("Updated Ann Core failed before Ready; returncode=%s", outcome.returncode)
            restore_rollback_update()
            restored = run_core()
            if restored.ready:
                LOGGER.info("Rollback Ann Core reported Ready")
                clear_update_state()
            else:
                LOGGER.error("Rollback Ann Core also failed before Ready; returncode=%s", restored.returncode)
            return restored.returncode
        except Exception:
            LOGGER.exception("Failed to apply verified Ann project update")
            print("Ann update could not be applied. See logs/ann-update.log for details.")
            return 1
    if not ACTIVE_CORE.is_dir():
        print("Ann Core is missing. Restore Ann_core or download an update.")
        return 1
    return run_core().returncode


if __name__ == "__main__":
    raise SystemExit(main())

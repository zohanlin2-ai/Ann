"""Stable bootstrap that starts Ann and applies verified full-project updates."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from logging.handlers import RotatingFileHandler


ROOT = Path(__file__).resolve().parent
STAGED_CORE = ROOT / "backup_ann"
ROLLBACK_CORE = ROOT / "rollback_ann"
FAILED_UPDATES = ROOT / "failed_updates"
ACTIVE_CORE = ROOT / "Ann_core"
UPDATE_REQUEST = ROOT / ".ann-update-request.json"
UPDATE_STATE = ROOT / ".ann-update-state.json"
READY_STATE = ROOT / ".ann-core-ready.json"
PRESERVED_NAMES = {".git", ".venv", "backup_ann", "rollback_ann", "failed_updates", UPDATE_REQUEST.name, UPDATE_STATE.name}
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
    process_id: int
    session_id: str


def _write_json_atomically(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path.name} must contain a JSON object.")
    return value


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_core() -> CoreRun:
    if READY_STATE.exists():
        READY_STATE.unlink()
    environment = os.environ.copy()
    environment["ANN_PROJECT_ROOT"] = str(ROOT)
    environment["ANN_CORE_DIR"] = str(ACTIVE_CORE)
    environment["ANN_CORE_READY_FILE"] = str(READY_STATE)
    session_id = uuid.uuid4().hex
    environment["ANN_LAUNCH_SESSION_ID"] = session_id
    command = [sys.executable, str(ACTIVE_CORE / "main.py")]
    process = subprocess.Popen(command, cwd=ROOT, env=environment)
    LOGGER.info("Starting Ann Core; launcher_pid=%s core_pid=%s command=%s", os.getpid(), process.pid, command)
    deadline = time.monotonic() + 30
    while not READY_STATE.exists():
        returncode = process.poll()
        if returncode is not None:
            LOGGER.error("Ann Core exited before Ready; returncode=%s", returncode)
            return CoreRun(returncode, False, process.pid, session_id)
        if time.monotonic() >= deadline:
            LOGGER.error("Ann Core did not report Ready within 30 seconds")
            process.terminate()
            return CoreRun(process.wait(), False, process.pid, session_id)
        time.sleep(0.1)
    LOGGER.info("Ann Core reported Ready")
    returncode = process.wait()
    LOGGER.info("Active Ann Core exited after Ready; returncode=%s", returncode)
    return CoreRun(returncode, True, process.pid, session_id)

def apply_verified_update(request: dict) -> dict:
    """Replace managed project files while preserving local data and this bootstrap."""
    if not STAGED_CORE.is_dir():
        raise RuntimeError("No verified backup_ann project is available.")
    staged_launcher = STAGED_CORE / "launcher.py"
    if not staged_launcher.is_file():
        raise RuntimeError("The staged project does not contain launcher.py.")
    launcher_changed = _file_hash(ROOT / "launcher.py") != _file_hash(staged_launcher)
    LOGGER.info("Applying verified project update; transaction_id=%s launcher_changed=%s", request["transaction_id"], launcher_changed)
    if ROLLBACK_CORE.exists():
        shutil.rmtree(ROLLBACK_CORE)
    ROLLBACK_CORE.mkdir()
    managed_names = [item.name for item in STAGED_CORE.iterdir() if item.name not in PRESERVED_NAMES]
    _write_json_atomically(UPDATE_STATE, {
        "transaction_id": request["transaction_id"],
        "managed_names": managed_names,
        "rollback_attempted": False,
        "launcher_changed": launcher_changed,
    })
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
    LOGGER.info("Verified update applied; awaiting updated Core Ready; transaction_id=%s", request["transaction_id"])
    return _read_json(UPDATE_STATE)


def restore_rollback_update() -> None:
    """Restore the pre-update managed project after the new Core fails to start."""
    if not ROLLBACK_CORE.is_dir():
        raise RuntimeError("No rollback_ann project is available.")
    if not UPDATE_STATE.is_file():
        raise RuntimeError("No update state is available for rollback.")
    state = _read_json(UPDATE_STATE)
    if state.get("rollback_attempted"):
        raise RuntimeError("Automatic rollback was already attempted for this update.")
    managed_names = state.get("managed_names", [])
    if not isinstance(managed_names, list) or not all(isinstance(name, str) for name in managed_names):
        raise RuntimeError("The update state is invalid.")
    state["rollback_attempted"] = True
    _write_json_atomically(UPDATE_STATE, state)
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
    for path in (UPDATE_REQUEST, UPDATE_STATE):
        if path.exists(): path.unlink()


def _read_update_request() -> dict | None:
    if not UPDATE_REQUEST.is_file(): return None
    request = _read_json(UPDATE_REQUEST)
    if not isinstance(request.get("transaction_id"), str) or request.get("staging_name") != STAGED_CORE.name or not isinstance(request.get("launch_session_id"), str):
        raise RuntimeError("The update request is invalid.")
    return request


def _archive_staged_update(transaction_id: str) -> None:
    if not STAGED_CORE.exists(): return
    FAILED_UPDATES.mkdir(exist_ok=True)
    destination = FAILED_UPDATES / transaction_id
    if destination.exists(): shutil.rmtree(destination)
    shutil.move(str(STAGED_CORE), str(destination))
    LOGGER.warning("Archived failed staged project at %s", destination)


def _complete_update() -> None:
    if STAGED_CORE.exists(): shutil.rmtree(STAGED_CORE)
    clear_update_state()
    LOGGER.info("Update transaction completed successfully")


def _handoff_to_current_launcher(mode: str) -> None:
    command = [sys.executable, str(ROOT / "launcher.py"), mode]
    LOGGER.info("Handing off to launcher on disk; old_launcher_pid=%s command=%s", os.getpid(), command)
    os.execv(sys.executable, command)


def _resume_updated_core() -> int:
    outcome = run_core()
    if outcome.ready:
        _complete_update()
        return outcome.returncode
    LOGGER.error("Updated Core failed before Ready; core_pid=%s returncode=%s", outcome.process_id, outcome.returncode)
    restore_rollback_update()
    request = _read_update_request()
    _archive_staged_update(str(request["transaction_id"]) if request else "unknown")
    _handoff_to_current_launcher("--resume-rollback")
    return 1


def _resume_rollback_core() -> int:
    outcome = run_core()
    if outcome.ready:
        _complete_update()
        LOGGER.info("Rollback Core reported Ready; core_pid=%s", outcome.process_id)
        return outcome.returncode
    LOGGER.error("Rollback Core also failed before Ready; core_pid=%s returncode=%s", outcome.process_id, outcome.returncode)
    return outcome.returncode


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--resume-update", action="store_true")
    parser.add_argument("--resume-rollback", action="store_true")
    arguments = parser.parse_args()
    if arguments.resume_update:
        LOGGER.info("Resumed updated launcher; launcher_pid=%s", os.getpid())
        return _resume_updated_core()
    if arguments.resume_rollback:
        LOGGER.info("Resumed restored launcher; launcher_pid=%s", os.getpid())
        return _resume_rollback_core()
    if not ACTIVE_CORE.is_dir():
        print("Ann Core is missing. Restore Ann_core or download an update.")
        return 1
    outcome = run_core()
    try:
        request = _read_update_request()
        if request is None:
            return outcome.returncode
        if request["launch_session_id"] != outcome.session_id:
            LOGGER.error("Update request session mismatch; request_session=%s observed_session=%s", request["launch_session_id"], outcome.session_id)
            return outcome.returncode
        if not outcome.ready or outcome.returncode != 0:
            LOGGER.error("Update request was not applied because Core did not exit normally; ready=%s returncode=%s", outcome.ready, outcome.returncode)
            return outcome.returncode
        state = apply_verified_update(request)
        if state["launcher_changed"]:
            _handoff_to_current_launcher("--resume-update")
            return 1
        return _resume_updated_core()
    except Exception:
        LOGGER.exception("Failed to apply requested Ann update")
        print("Ann update could not be applied. See logs/ann-update.log for details.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

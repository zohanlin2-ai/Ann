"""Stable Ann launcher that selects the active or staged Core."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ACTIVE_CORE = ROOT / "Ann_core"
STAGED_CORE = ROOT / "backup_ann"
ROLLBACK_CORE = ROOT / "rollback_ann"
TRIAL_MARKER = ROOT / ".ann_trial_ready"


def run_core(core_dir: Path, trial: bool = False) -> int:
    environment = os.environ.copy()
    environment["ANN_PROJECT_ROOT"] = str(ROOT)
    environment["ANN_CORE_DIR"] = str(core_dir)
    if trial:
        TRIAL_MARKER.unlink(missing_ok=True)
        environment["ANN_TRIAL_MARKER"] = str(TRIAL_MARKER)

    process = subprocess.Popen([sys.executable, str(core_dir / "main.py")], cwd=ROOT, env=environment)
    if not trial:
        return process.wait()

    deadline = time.monotonic() + 15
    while process.poll() is None and time.monotonic() < deadline:
        if TRIAL_MARKER.exists():
            promote_staged_core()
            break
        time.sleep(0.2)
    return process.wait()


def promote_staged_core() -> None:
    """Promote a Core only after its trial process reports a healthy UI start."""
    if not STAGED_CORE.exists():
        return
    if ROLLBACK_CORE.exists():
        shutil.rmtree(ROLLBACK_CORE)
    if ACTIVE_CORE.exists():
        ACTIVE_CORE.replace(ROLLBACK_CORE)
    STAGED_CORE.replace(ACTIVE_CORE)
    TRIAL_MARKER.unlink(missing_ok=True)
    print("The staged Ann Core was promoted successfully.")


def main() -> int:
    if STAGED_CORE.is_dir():
        print("Starting the staged Ann Core for verification.")
        return run_core(STAGED_CORE, trial=True)
    if not ACTIVE_CORE.is_dir():
        print("Ann Core is missing. Restore Ann_core or download an update.")
        return 1
    return run_core(ACTIVE_CORE)


if __name__ == "__main__":
    raise SystemExit(main())

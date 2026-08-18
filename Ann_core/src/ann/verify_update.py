"""Headless validation for a fully staged Ann project update."""

from __future__ import annotations

import json
from pathlib import Path


def verify_update(project_root: Path, core_root: Path) -> bool:
    """Validate the staged project without writing its local module data."""
    required_paths = [
        project_root / "launcher.py",
        project_root / "requirements.txt",
        project_root / "VERSION.md",
        project_root / "catalog.json",
        core_root / "main.py",
        core_root / "manifest.json",
        core_root / "modules" / "updater" / "manifest.json",
        core_root / "src" / "ann" / "app.py",
    ]
    if not all(path.is_file() for path in required_paths):
        return False
    core_manifest = json.loads((core_root / "manifest.json").read_text(encoding="utf-8"))
    updater_manifest = json.loads((core_root / "modules" / "updater" / "manifest.json").read_text(encoding="utf-8"))
    if core_manifest.get("id") != "ann.core" or updater_manifest.get("id") != "ann.updater":
        return False
    try:
        import PySide6  # noqa: F401
        from ann.module_runtime import load_updater  # noqa: F401
        from PySide6.QtWidgets import QApplication

        application = QApplication.instance() or QApplication([])
        application.quit()
    except ImportError:
        return False
    return True

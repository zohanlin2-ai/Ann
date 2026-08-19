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
    catalog = json.loads((project_root / "catalog.json").read_text(encoding="utf-8"))
    if core_manifest.get("id") != "ann.core" or core_manifest.get("version") != catalog["ann_core"].get("version"):
        return False
    if updater_manifest.get("id") != "ann.updater":
        return False
    for module in catalog.get("modules", []):
        relative_manifest_path = Path(module["manifest_path"])
        if relative_manifest_path.is_absolute():
            return False
        manifest_path = (project_root / relative_manifest_path).resolve()
        if not manifest_path.is_relative_to(project_root.resolve()):
            return False
        if not manifest_path.is_file():
            return False
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("id") != module["id"] or manifest.get("version") != module["version"]:
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

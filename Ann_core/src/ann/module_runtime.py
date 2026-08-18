"""Load the bundled, privileged updater module."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from ann.registry import ModuleRegistry


def load_updater(project_root: Path, core_root: Path, registry: ModuleRegistry):
    entry_point = core_root / "modules" / "updater" / "module.py"
    specification = importlib.util.spec_from_file_location("ann_system_updater", entry_point)
    if specification is None or specification.loader is None:
        raise RuntimeError("The Ann Updater entry point could not be loaded.")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module.Updater(project_root, core_root, registry)

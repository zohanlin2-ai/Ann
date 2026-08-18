"""Entry point for Ann's local, read-only Security Monitor module."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def create_module(project_root: Path):
    module_root = Path(__file__).resolve().parent
    package_root = module_root / "security_monitor"
    spec = importlib.util.spec_from_file_location("ann_security_monitor", package_root / "service.py", submodule_search_locations=[str(package_root)])
    if spec is None or spec.loader is None:
        raise RuntimeError("Security Monitor could not be loaded.")
    package = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = package
    spec.loader.exec_module(package)
    return package.SecurityMonitor(project_root)

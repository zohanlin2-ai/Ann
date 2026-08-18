"""Load Ann modules after checking their local manifests and registry state."""

from __future__ import annotations

import importlib.util
import json
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


def load_enabled_modules(project_root: Path, registry: ModuleRegistry) -> tuple[dict[str, object], list[str]]:
    """Load enabled local modules without letting one broken module stop Ann.

    Only modules explicitly registered as Local and enabled by the owner are
    eligible. Each entry point must expose `create_module(project_root)`.
    """
    loaded: dict[str, object] = {}
    errors: list[str] = []
    for item in registry.list_modules():
        if item["system"] or not item["enabled"] or item["source"] != "Local":
            continue
        module_root = project_root / item["path"]
        manifest_path = module_root / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest["id"] != item["id"]:
                raise ValueError("manifest id does not match the registry")
            entry_point = module_root / manifest["entry_point"]
            if not entry_point.is_file() or entry_point.parent != module_root:
                raise ValueError("invalid module entry point")
            specification = importlib.util.spec_from_file_location(f"ann_module_{item['id'].replace('.', '_').replace('-', '_')}", entry_point)
            if specification is None or specification.loader is None:
                raise ValueError("entry point could not be loaded")
            module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(module)
            factory = getattr(module, "create_module", None)
            if not callable(factory):
                raise ValueError("module does not expose create_module(project_root)")
            loaded[item["id"]] = factory(project_root)
        except (OSError, ValueError, KeyError, json.JSONDecodeError, ImportError, RuntimeError) as error:
            errors.append(f"{item['id']}: {error}")
    return loaded, errors

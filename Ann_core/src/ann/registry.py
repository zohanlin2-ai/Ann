"""Persistent registry of modules Ann may enable."""

from __future__ import annotations

import json
import re
from pathlib import Path


VALID_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class ModuleRegistry:
    def __init__(self, project_root: Path, core_root: Path) -> None:
        self.project_root = project_root
        self.core_root = core_root
        self.registry_path = project_root / "modules" / "registry.json"
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._read()
        self._ensure_updater()
        self._write()

    def _read(self) -> dict:
        if not self.registry_path.exists():
            return {"schema_version": 1, "modules": {}}
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def _write(self) -> None:
        temporary = self.registry_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.registry_path)

    def _ensure_updater(self) -> None:
        core_manifest_path = self.core_root / "manifest.json"
        core_manifest = json.loads(core_manifest_path.read_text(encoding="utf-8"))
        self.data["modules"][core_manifest["id"]] = {
            "id": core_manifest["id"],
            "name": core_manifest["name"],
            "version": core_manifest["version"],
            "path": "Ann_core",
            "source": "System",
            "enabled": True,
            "system": True,
        }
        manifest_path = self.core_root / "modules" / "updater" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.data["modules"][manifest["id"]] = {
            "id": manifest["id"],
            "name": manifest["name"],
            "version": manifest["version"],
            "path": "Ann_core/modules/updater",
            "source": "System",
            "enabled": True,
            "system": True,
        }

    def list_modules(self) -> list[dict]:
        return sorted(self.data["modules"].values(), key=lambda module: module["id"])

    def set_enabled(self, module_id: str, enabled: bool) -> None:
        module = self.data["modules"].get(module_id)
        if module is None:
            raise ValueError(f"Module '{module_id}' has not been downloaded.")
        if module["system"] and not enabled:
            raise ValueError(f"{module['name']} is a required system module and must remain enabled.")
        module["enabled"] = enabled
        self._write()

    def register_download(self, manifest: dict, module_path: Path) -> None:
        module_id = manifest.get("id", "")
        if not VALID_ID.fullmatch(module_id):
            raise ValueError("The downloaded module manifest has an invalid id.")
        self.data["modules"][module_id] = {
            "id": module_id,
            "name": manifest.get("name", module_id),
            "version": manifest["version"],
            "path": str(module_path.relative_to(self.project_root)).replace("\\", "/"),
            "source": "GitHub",
            "enabled": self.data["modules"].get(module_id, {}).get("enabled", False),
            "system": False,
        }
        self._write()

    def format_modules(self) -> str:
        modules = self.list_modules()
        lines = ["Module                 Version   Status"]
        for module in modules:
            status = "Enabled" if module["enabled"] else "Disabled"
            lines.append(f"{module['id']:<22} {module['version']:<9} {status}")
        return "\n".join(lines)

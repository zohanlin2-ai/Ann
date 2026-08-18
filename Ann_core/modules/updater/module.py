"""GitHub-backed system updater for Ann Core and optional modules."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


class Updater:
    def __init__(self, project_root: Path, core_root: Path, registry) -> None:
        self.project_root = project_root
        self.core_root = core_root
        self.registry = registry
        self.config_path = project_root / "ann_config.json"

    def _catalog(self) -> dict:
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        with urllib.request.urlopen(config["catalog_url"], timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _is_newer(remote: str, local: str) -> bool:
        return tuple(map(int, remote.split("."))) > tuple(map(int, local.split(".")))

    @staticmethod
    def _safe_extract(archive: Path, destination: Path) -> None:
        with zipfile.ZipFile(archive) as zip_file:
            root = destination.resolve()
            for member in zip_file.infolist():
                target = (destination / member.filename).resolve()
                if not target.is_relative_to(root):
                    raise ValueError("The downloaded archive contains an unsafe path.")
            zip_file.extractall(destination)

    @staticmethod
    def _download(url: str, destination: Path, expected_hash: str | None = None) -> None:
        with urllib.request.urlopen(url, timeout=30) as response:
            destination.write_bytes(response.read())
        if expected_hash:
            actual_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                raise ValueError("Downloaded file hash does not match the catalog.")

    def list_available(self) -> str:
        catalog = self._catalog()
        modules = catalog.get("modules", [])
        if not modules:
            return "No optional modules are currently published in the GitHub catalog."
        return "\n".join(f"{item['id']}  {item['version']}  {item['name']}" for item in modules)

    def check(self) -> str:
        catalog = self._catalog()
        messages: list[str] = []
        remote_core = catalog["ann_core"]["version"]
        local_core = json.loads((self.core_root / "modules" / "updater" / "manifest.json").read_text(encoding="utf-8"))["version"]
        messages.append(
            f"Ann Core: {local_core} → {remote_core}" if self._is_newer(remote_core, local_core) else f"Ann Core: {local_core} (current)"
        )
        available = {item["id"]: item for item in catalog.get("modules", [])}
        for module in self.registry.list_modules():
            remote = available.get(module["id"])
            if remote and self._is_newer(remote["version"], module["version"]):
                messages.append(f"{module['id']}: {module['version']} → {remote['version']}")
        return "\n".join(messages)

    def stage_core_update(self) -> str:
        catalog = self._catalog()
        item = catalog["ann_core"]
        local = json.loads((self.core_root / "modules" / "updater" / "manifest.json").read_text(encoding="utf-8"))["version"]
        if not self._is_newer(item["version"], local):
            return "Ann Core is already current."
        target = self.project_root / "backup_ann"
        if target.exists():
            return "A staged Core already exists. Restart Ann to validate it before downloading another update."
        with tempfile.TemporaryDirectory() as temporary_name:
            temporary = Path(temporary_name)
            archive = temporary / "ann_core.zip"
            self._download(item["archive_url"], archive, item.get("sha256"))
            extracted = temporary / "extracted"
            extracted.mkdir()
            self._safe_extract(archive, extracted)
            candidates = [path.parent for path in extracted.rglob("main.py") if path.parent.name == "Ann_core"]
            if len(candidates) != 1 or not (candidates[0] / "src" / "ann").is_dir():
                raise ValueError("The GitHub archive does not contain a valid Ann_core directory.")
            shutil.copytree(candidates[0], target)
        return "Ann Core was staged in backup_ann. Restart Ann to validate and promote it."

    def install_or_update_module(self, module_id: str) -> str:
        catalog = self._catalog()
        item = next((entry for entry in catalog.get("modules", []) if entry["id"] == module_id), None)
        if item is None:
            return f"Module '{module_id}' is not available in the GitHub catalog."
        if item.get("system"):
            return "The Ann Updater is bundled with Ann Core and cannot be downloaded separately."
        with tempfile.TemporaryDirectory() as temporary_name:
            temporary = Path(temporary_name)
            archive = temporary / "module.zip"
            self._download(item["archive_url"], archive, item.get("sha256"))
            extracted = temporary / "extracted"
            extracted.mkdir()
            self._safe_extract(archive, extracted)
            manifests = list(extracted.rglob("manifest.json"))
            if len(manifests) != 1:
                raise ValueError("The module archive must contain exactly one manifest.json.")
            manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
            if manifest.get("id") != module_id or not manifest.get("version"):
                raise ValueError("The module manifest does not match the requested module.")
            destination = self.project_root / "modules" / "downloaded" / module_id.replace(".", "_")
            replacement = destination.with_name(destination.name + ".new")
            if replacement.exists():
                shutil.rmtree(replacement)
            shutil.copytree(manifests[0].parent, replacement)
            if destination.exists():
                shutil.rmtree(destination)
            replacement.replace(destination)
            self.registry.register_download(manifest, destination)
        return f"Module '{module_id}' {manifest['version']} was downloaded. Enable it in Module List when ready."

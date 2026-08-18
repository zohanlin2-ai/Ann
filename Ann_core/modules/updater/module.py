"""GitHub-backed system updater for Ann Core and optional modules."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from ann.debug_log import get_module_logger


class Updater:
    def __init__(self, project_root: Path, core_root: Path, registry) -> None:
        self.project_root = project_root
        self.core_root = core_root
        self.registry = registry
        self.config_path = project_root / "ann_config.json"
        self.logger = get_module_logger(project_root, "ann.updater", mirror_update_log=True)

    def _catalog(self) -> dict:
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.logger.info("Fetching update catalog from %s", config["catalog_url"])
        try:
            with urllib.request.urlopen(config["catalog_url"], timeout=15) as response:
                catalog = json.loads(response.read().decode("utf-8"))
        except Exception:
            self.logger.exception("Failed to fetch or parse the update catalog")
            raise
        self.logger.info("Catalog fetched successfully; Ann Core version=%s", catalog.get("ann_core", {}).get("version"))
        return catalog

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

    def _download(self, url: str, destination: Path, expected_hash: str | None = None) -> None:
        self.logger.info("Downloading update archive from %s", url)
        with urllib.request.urlopen(url, timeout=30) as response:
            destination.write_bytes(response.read())
        self.logger.info("Archive download completed; bytes=%s", destination.stat().st_size)
        if expected_hash:
            actual_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                self.logger.error("Archive hash mismatch; expected=%s actual=%s", expected_hash, actual_hash)
                raise ValueError("Downloaded file hash does not match the catalog.")
            self.logger.info("Archive SHA-256 hash validated")

    def check(self) -> str:
        catalog = self._catalog()
        messages: list[str] = []
        remote_core = catalog["ann_core"]["version"]
        local_core = json.loads((self.core_root / "modules" / "updater" / "manifest.json").read_text(encoding="utf-8"))["version"]
        self.logger.info("Update check comparison; local=%s remote=%s", local_core, remote_core)
        messages.append(
            f"Ann Core: {local_core} → {remote_core}" if self._is_newer(remote_core, local_core) else f"Ann Core: {local_core} (current)"
        )
        messages.append(f"Ann Updater: {local_core} (bundled with Ann Core)")
        return "\n".join(messages)

    def stage_project_update(self):
        """Download, verify, and schedule a complete Ann project replacement."""
        from ann.core import CommandResult
        try:
            catalog = self._catalog()
            item = catalog["ann_core"]
            local = json.loads((self.core_root / "manifest.json").read_text(encoding="utf-8"))["version"]
            self.logger.info("Update Ann requested; local=%s remote=%s", local, item["version"])
            if not self._is_newer(item["version"], local):
                self.logger.info("Update skipped because the catalog is not newer")
                return CommandResult("Ann is already current.")
            target = self.project_root / "backup_ann"
            if target.exists():
                self.logger.warning("Update blocked because backup_ann already exists: %s", target)
                return CommandResult("A staged Ann project already exists. Restart Ann to finish or inspect the pending update.")
            with tempfile.TemporaryDirectory() as temporary_name:
                temporary = Path(temporary_name)
                archive = temporary / "ann_project.zip"
                self._download(item["archive_url"], archive, item.get("sha256"))
                extracted = temporary / "extracted"
                extracted.mkdir()
                self._safe_extract(archive, extracted)
                candidates = [path for path in extracted.iterdir() if (path / "Ann_core" / "main.py").is_file()]
                self.logger.info("Archive extraction completed; project candidates=%s", len(candidates))
                if len(candidates) != 1:
                    raise ValueError("The GitHub archive does not contain a valid Ann project directory.")
                shutil.copytree(candidates[0], target)
            self.logger.info("Complete Ann project staged in %s", target)
            environment = os.environ.copy()
            environment["ANN_PROJECT_ROOT"] = str(target)
            environment["ANN_CORE_DIR"] = str(target / "Ann_core")
            environment["QT_QPA_PLATFORM"] = "offscreen"
            command = [sys.executable, str(target / "Ann_core" / "main.py"), "--verify-update"]
            self.logger.info("Running staged-project verification: %s", command)
            verification = subprocess.run(command, cwd=target, env=environment, capture_output=True, text=True, timeout=30)
            self.logger.info("Verification completed; returncode=%s stdout=%r stderr=%r", verification.returncode, verification.stdout, verification.stderr)
            if verification.returncode != 0:
                details = verification.stderr.strip() or verification.stdout.strip() or "unknown validation failure"
                return CommandResult(f"Ann update validation failed; backup_ann was preserved for inspection: {details}")
            helper = [sys.executable, str(self.project_root / "launcher.py"), "--apply-update", "--wait-for", str(os.getpid())]
            self.logger.info("Scheduling update helper: %s", helper)
            subprocess.Popen(helper, cwd=self.project_root, env=os.environ.copy())
            return CommandResult("Ann update was downloaded and verified. Ann will restart to apply it.", restart_for_update=True)
        except Exception:
            self.logger.exception("Update Ann failed")
            return CommandResult("Ann update failed. See logs/ann-update.log for details.")

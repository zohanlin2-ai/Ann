from __future__ import annotations

import logging
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = MODULE_ROOT.parents[1]
CORE_SOURCE = PROJECT_ROOT / "Ann_core" / "src"
for source in (str(CORE_SOURCE), str(MODULE_ROOT)):
    if source not in sys.path:
        sys.path.insert(0, source)

from ann.module_lifecycle import ModuleState
from ann.core import AnnCore
from module import create_module
from security_monitor.service import SecurityMonitor
from security_monitor.store import Store


class FakeCapture:
    def __init__(self, observe) -> None:
        self.observe = observe
        self.active = False
        self.stop_calls = 0

    def start(self, seconds: int, interface: str | None = None) -> None:
        self.active = True

    def stop(self) -> None:
        self.stop_calls += 1
        self.active = False


class FailingCapture(FakeCapture):
    def start(self, seconds: int, interface: str | None = None) -> None:
        raise RuntimeError("Npcap is not available for this test")


class FailingHealthStore:
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root

    def settings(self) -> dict:
        return {"retention_days": 30}

    def dashboard(self) -> dict:
        raise OSError("simulated database failure")


class SecurityMonitorLifecycleTests(unittest.TestCase):
    def monitor(self, project_root: Path, store_factory=Store, capture_factory=FakeCapture) -> SecurityMonitor:
        return SecurityMonitor(project_root, logging.getLogger("security-monitor-tests"), store_factory, capture_factory)

    def test_start_health_stop_and_repeated_stop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            monitor = self.monitor(Path(temporary))
            self.assertEqual(monitor.validate(None).state, ModuleState.READY)
            self.assertEqual(monitor.start(None).state, ModuleState.READY)
            self.assertTrue(monitor.is_running)
            self.assertEqual(monitor.health_check(None).state, ModuleState.READY)
            self.assertEqual(monitor.stop(None).state, ModuleState.STOPPED)
            self.assertFalse(monitor.is_running)
            self.assertEqual(monitor.stop(None).state, ModuleState.STOPPED)

    def test_entry_point_exposes_controlled_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            module = create_module(Path(temporary))
            try:
                for method in ("validate", "start", "health_check", "stop"):
                    self.assertTrue(callable(getattr(module, method, None)))
                self.assertEqual(module.validate(None).state, ModuleState.READY)
                self.assertEqual(module.start(None).state, ModuleState.READY)
                self.assertEqual(module.stop(None).state, ModuleState.STOPPED)
            finally:
                for handler in list(module.logger.handlers):
                    module.logger.removeHandler(handler)
                    handler.close()

    def test_core_controls_stop_start_and_restart_without_affecting_other_modules(self) -> None:
        """Use a temporary project to verify failure isolation at the Core boundary."""
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            shutil.copytree(MODULE_ROOT, project_root / "modules" / "security_monitor")
            (project_root / "ann_config.json").write_text('{"catalog_url": "https://example.invalid/catalog.json"}\n', encoding="utf-8")
            core = AnnCore(project_root, PROJECT_ROOT / "Ann_core")
            try:
                self.assertEqual(core.module_results["ann.security-monitor"].state, ModuleState.READY)
                self.assertEqual(core.execute("modules stop ann.security-monitor").status.value, "Ready")
                self.assertEqual(core.module_results["ann.security-monitor"].state, ModuleState.STOPPED)
                self.assertEqual(core.execute("modules start ann.security-monitor").status.value, "Ready")
                self.assertEqual(core.execute("modules restart ann.security-monitor").status.value, "Ready")
                self.assertEqual(core.module_results["ann.core"].state, ModuleState.READY)
                self.assertEqual(core.module_results["ann.updater"].state, ModuleState.READY)
            finally:
                core.stop_all_modules()
                for name, logger in logging.Logger.manager.loggerDict.items():
                    if not name.startswith("ann.") or not isinstance(logger, logging.Logger):
                        continue
                    for handler in list(logger.handlers):
                        logger.removeHandler(handler)
                        handler.close()

    def test_invalid_data_path_fails_without_starting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            data = project_root / "data"
            data.mkdir()
            (data / "security_monitor").write_text("not a directory", encoding="utf-8")
            monitor = self.monitor(project_root)
            self.assertEqual(monitor.validate(None).state, ModuleState.FAILED)
            self.assertFalse(monitor.is_running)

    def test_invalid_settings_fail_without_affecting_module_instance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary)
            data_root = project_root / "data" / "security_monitor"
            data_root.mkdir(parents=True)
            (data_root / "settings.json").write_text("{not valid json", encoding="utf-8")
            monitor = self.monitor(project_root)
            self.assertEqual(monitor.validate(None).state, ModuleState.FAILED)
            self.assertFalse(monitor.is_running)

    def test_failed_health_check_stops_created_capture(self) -> None:
        created: list[FakeCapture] = []

        def capture_factory(observe):
            capture = FakeCapture(observe)
            created.append(capture)
            return capture

        with tempfile.TemporaryDirectory() as temporary:
            monitor = self.monitor(Path(temporary), FailingHealthStore, capture_factory)
            self.assertEqual(monitor.start(None).state, ModuleState.FAILED)
            self.assertFalse(monitor.is_running)
            self.assertEqual(created[0].stop_calls, 1)

    def test_post_stop_capture_callback_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            monitor = self.monitor(Path(temporary))
            self.assertEqual(monitor.start(None).state, ModuleState.READY)
            store = monitor.store
            capture = monitor.capture
            assert store is not None
            assert capture is not None
            capture.observe("192.0.2.1", "198.51.100.2", "tcp", 443, True, False)
            self.assertEqual(store.dashboard()["network_events"], 1)
            monitor.stop(None)
            capture.observe("192.0.2.1", "198.51.100.2", "tcp", 444, True, False)
            self.assertEqual(store.dashboard()["network_events"], 1)

    def test_capture_failure_is_isolated_from_login_monitoring(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            monitor = self.monitor(Path(temporary), capture_factory=FailingCapture)
            self.assertEqual(monitor.start(None).state, ModuleState.READY)
            response = monitor.handle_command("security capture start 30")
            self.assertIn("Network metadata capture is unavailable", response or "")
            self.assertTrue(monitor.is_running)
            monitor.record_login("ann", "192.0.2.10", None, True)
            assert monitor.store is not None
            self.assertEqual(monitor.store.dashboard()["login_events"], 1)

    def test_restart_clears_session_pause(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            monitor = self.monitor(Path(temporary))
            monitor.start(None)
            monitor.pause()
            self.assertTrue(monitor.paused)
            monitor.stop(None)
            monitor.start(None)
            self.assertFalse(monitor.paused)


if __name__ == "__main__":
    unittest.main()

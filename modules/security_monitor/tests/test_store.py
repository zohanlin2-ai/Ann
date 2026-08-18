from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from security_monitor.store import Store


class StoreTests(unittest.TestCase):
    def test_default_settings_and_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = Store(Path(temporary))
            self.assertEqual(store.settings()["retention_days"], 30)
            self.assertEqual(store.dashboard()["open_alerts"], 0)

    def test_alert_is_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = Store(Path(temporary))
            store.add_alert("possible_port_scan", "high", "192.0.2.1", "Test alert")
            self.assertEqual(store.dashboard()["open_alerts"], 1)
            self.assertEqual(store.alerts()[0].kind, "possible_port_scan")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from .models import Alert


class Store:
    def __init__(self, data_root: Path) -> None:
        self.data_root = data_root
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.database = self.data_root / "events.db"
        self.settings_path = self.data_root / "settings.json"
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS login_events (
                    id INTEGER PRIMARY KEY, account_id TEXT, source_ip TEXT, device_id TEXT,
                    succeeded INTEGER, occurred_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS network_events (
                    id INTEGER PRIMARY KEY, source_ip TEXT, destination_ip TEXT, protocol TEXT,
                    destination_port INTEGER, tcp_syn INTEGER, tcp_ack INTEGER, observed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY, kind TEXT, severity TEXT, subject TEXT, detail TEXT,
                    created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open'
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY, action TEXT NOT NULL, detail TEXT, created_at TEXT NOT NULL
                );
            """)
        if not self.settings_path.exists():
            self.save_settings({"retention_days": 30, "failed_login_threshold": 5, "syn_scan_threshold": 20})
        self.enforce_retention()

    def settings(self) -> dict:
        return json.loads(self.settings_path.read_text(encoding="utf-8"))

    def save_settings(self, settings: dict) -> None:
        self.settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        self.audit("settings_updated", "Security Monitor settings were changed.")
        self.enforce_retention()

    def enforce_retention(self) -> None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.settings()["retention_days"])).isoformat()
        with self.connection() as conn:
            for table, column in (("login_events", "occurred_at"), ("network_events", "observed_at"), ("alerts", "created_at")):
                conn.execute(f"DELETE FROM {table} WHERE {column} < ?", (cutoff,))

    def audit(self, action: str, detail: str) -> None:
        with self.connection() as conn:
            conn.execute("INSERT INTO audit_log(action,detail,created_at) VALUES(?,?,?)", (action, detail, datetime.now(timezone.utc).isoformat()))

    def add_login(self, account_id: str, source_ip: str, device_id: str | None, succeeded: bool) -> None:
        with self.connection() as conn:
            conn.execute("INSERT INTO login_events(account_id,source_ip,device_id,succeeded,occurred_at) VALUES(?,?,?,?,?)", (account_id, source_ip, device_id, succeeded, datetime.now(timezone.utc).isoformat()))

    def known_login_source(self, account_id: str, source_ip: str, device_id: str | None) -> bool:
        with self.connection() as conn:
            return conn.execute("SELECT 1 FROM login_events WHERE account_id=? AND succeeded=1 AND (source_ip=? OR (? IS NOT NULL AND device_id=?)) LIMIT 1", (account_id, source_ip, device_id, device_id)).fetchone() is not None

    def recent_failed_logins(self, source_ip: str) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        with self.connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM login_events WHERE source_ip=? AND succeeded=0 AND occurred_at>=?", (source_ip, cutoff)).fetchone()[0]

    def add_network(self, source_ip: str, destination_ip: str, protocol: str, destination_port: int | None, tcp_syn: bool, tcp_ack: bool) -> None:
        with self.connection() as conn:
            conn.execute("INSERT INTO network_events(source_ip,destination_ip,protocol,destination_port,tcp_syn,tcp_ack,observed_at) VALUES(?,?,?,?,?,?,?)", (source_ip, destination_ip, protocol, destination_port, tcp_syn, tcp_ack, datetime.now(timezone.utc).isoformat()))

    def recent_syn_ports(self, source_ip: str) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
        with self.connection() as conn:
            return conn.execute("SELECT COUNT(DISTINCT destination_port) FROM network_events WHERE source_ip=? AND protocol='tcp' AND tcp_syn=1 AND tcp_ack=0 AND observed_at>=?", (source_ip, cutoff)).fetchone()[0]

    def add_alert(self, kind: str, severity: str, subject: str, detail: str) -> Alert:
        created_at = datetime.now(timezone.utc)
        with self.connection() as conn:
            cursor = conn.execute("INSERT INTO alerts(kind,severity,subject,detail,created_at,status) VALUES(?,?,?,?,?,?)", (kind, severity, subject, detail, created_at.isoformat(), "open"))
        return Alert(kind, severity, subject, detail, created_at, id=cursor.lastrowid)

    def has_recent_alert(self, kind: str, subject: str) -> bool:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        with self.connection() as conn:
            return conn.execute("SELECT 1 FROM alerts WHERE kind=? AND subject=? AND created_at>=? LIMIT 1", (kind, subject, cutoff)).fetchone() is not None

    def alerts(self, limit: int = 100) -> list[Alert]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [Alert(row["kind"], row["severity"], row["subject"], row["detail"], datetime.fromisoformat(row["created_at"]), row["status"], row["id"]) for row in rows]

    def dashboard(self) -> dict[str, int]:
        with self.connection() as conn:
            return {"open_alerts": conn.execute("SELECT COUNT(*) FROM alerts WHERE status='open'").fetchone()[0], "login_events": conn.execute("SELECT COUNT(*) FROM login_events").fetchone()[0], "network_events": conn.execute("SELECT COUNT(*) FROM network_events").fetchone()[0]}

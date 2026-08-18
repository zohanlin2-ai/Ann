from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path

from PySide6.QtWidgets import QDialog

from .capture import PacketCapture
from .store import Store


class SecurityMonitor:
    def __init__(self, project_root: Path) -> None:
        self.store = Store(project_root / "data" / "security_monitor")
        self.capture = PacketCapture(self.record_network)
        # Pause state is intentionally process-only. Ann restarts monitoring on
        # every new launch, as requested by the product owner.
        self.paused = False

    def pause(self) -> None:
        self.paused = True
        self.capture.stop()
        self.store.audit("monitoring_paused", "Monitoring paused for this Ann session.")

    def resume(self) -> None:
        self.paused = False
        self.store.audit("monitoring_resumed", "Monitoring resumed for this Ann session.")

    def record_login(self, account_id: str, source_ip: str, device_id: str | None, succeeded: bool) -> None:
        if self.paused:
            return
        self.store.enforce_retention()
        source_ip = str(ip_address(source_ip))
        known = self.store.known_login_source(account_id, source_ip, device_id)
        self.store.add_login(account_id, source_ip, device_id, succeeded)
        settings = self.store.settings()
        if succeeded and not known:
            self._alert_once("new_login_source", "medium", account_id, f"Successful login from a new source: {source_ip}.")
        if not succeeded and self.store.recent_failed_logins(source_ip) >= settings["failed_login_threshold"]:
            self._alert_once("repeated_login_failures", "high", source_ip, "Repeated failed logins in the last 15 minutes.")

    def record_network(self, source_ip: str, destination_ip: str, protocol: str, destination_port: int | None, tcp_syn: bool, tcp_ack: bool) -> None:
        if self.paused:
            return
        self.store.enforce_retention()
        self.store.add_network(source_ip, destination_ip, protocol, destination_port, tcp_syn, tcp_ack)
        threshold = self.store.settings()["syn_scan_threshold"]
        if protocol == "tcp" and tcp_syn and not tcp_ack and self.store.recent_syn_ports(source_ip) >= threshold:
            self._alert_once("possible_port_scan", "high", source_ip, f"TCP SYN traffic reached {threshold} or more destination ports in two minutes.")

    def _alert_once(self, kind: str, severity: str, subject: str, detail: str) -> None:
        if not self.store.has_recent_alert(kind, subject):
            self.store.add_alert(kind, severity, subject, detail)

    def handle_command(self, command: str) -> str | None:
        parts = command.strip().split()
        if not parts or parts[0].lower() != "security":
            return None
        if len(parts) == 1 or parts[1].lower() == "status":
            data = self.store.dashboard()
            capture = "running" if self.capture.active else "stopped"
            state = "paused for this session" if self.paused else "active"
            return f"Security Monitor: {state}\nNetwork capture: {capture}\nOpen alerts: {data['open_alerts']}\nLogin events: {data['login_events']}\nNetwork observations: {data['network_events']}"
        if parts[1].lower() == "open":
            return "Open Security Center from Ann's right-click menu."
        if parts[1].lower() == "alerts":
            alerts = self.store.alerts(10)
            return "No alerts." if not alerts else "\n".join(f"[{item.severity.upper()}] {item.kind}: {item.detail}" for item in alerts)
        if parts[1].lower() in {"pause", "暫停"}:
            self.pause()
            return "Security Monitor is paused for this Ann session. It will start automatically when Ann is restarted."
        if parts[1].lower() in {"resume", "恢復"}:
            self.resume()
            return "Security Monitor resumed."
        if parts[1:3] == ["capture", "start"]:
            if self.paused:
                return "Security Monitor is paused. Resume it before starting network capture."
            seconds = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 30
            seconds = max(1, min(seconds, 600))
            self.capture.start(seconds)
            self.store.audit("capture_started", f"Metadata capture started for up to {seconds} seconds.")
            return f"Network metadata capture started for up to {seconds} seconds."
        if parts[1:3] == ["capture", "stop"]:
            self.capture.stop()
            self.store.audit("capture_stopped", "Metadata capture stopped by user.")
            return "Network metadata capture stopped."
        return "Security commands: status, alerts, open, pause, resume, capture start [seconds], capture stop"

    def create_dialog(self, parent) -> QDialog:
        from .ui import SecurityCenterDialog
        return SecurityCenterDialog(self, parent)

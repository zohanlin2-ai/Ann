from __future__ import annotations

import json
from ipaddress import ip_address
import logging
from pathlib import Path
import traceback
from typing import TYPE_CHECKING, Callable

from ann.module_lifecycle import ModuleResult

from .capture import PacketCapture
from .store import Store

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog


class SecurityMonitor:
    """A controlled, local-only monitoring module.

    Store and capture resources are intentionally created by ``start()`` rather
    than construction so a failed module cannot leave background work running.
    """

    def __init__(
        self,
        project_root: Path,
        logger: logging.Logger,
        store_factory: Callable[[Path], Store] = Store,
        capture_factory: Callable[[Callable[..., None]], PacketCapture] = PacketCapture,
    ) -> None:
        self.project_root = project_root
        self.logger = logger
        self.data_root = project_root / "data" / "security_monitor"
        self._store_factory = store_factory
        self._capture_factory = capture_factory
        self.store: Store | None = None
        self.capture: PacketCapture | None = None
        self.running = False
        # Pause state is intentionally process-only. Ann restarts monitoring on
        # every new launch, as requested by the product owner.
        self.paused = False

    @property
    def is_running(self) -> bool:
        return self.running and self.store is not None and self.capture is not None

    def validate(self, context) -> ModuleResult:
        """Check pre-existing local configuration without starting runtime work."""
        try:
            if self.data_root.exists() and not self.data_root.is_dir():
                self.logger.error("Security Monitor data path is not a directory: %s", self.data_root)
                return ModuleResult.failed(
                    "Security Monitor data path is not a directory.",
                    str(self.data_root),
                )
            if self.data_root.parent.exists() and not self.data_root.parent.is_dir():
                self.logger.error("Security Monitor data parent is not a directory: %s", self.data_root.parent)
                return ModuleResult.failed(
                    "Security Monitor data parent is not a directory.",
                    str(self.data_root.parent),
                )
            settings_path = self.data_root / "settings.json"
            if settings_path.exists():
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
                required = {"retention_days", "failed_login_threshold", "syn_scan_threshold"}
                if not isinstance(settings, dict) or not required.issubset(settings):
                    self.logger.error("Security Monitor settings are incomplete: %s", settings_path)
                    return ModuleResult.failed(
                        "Security Monitor settings are incomplete.",
                        f"Expected settings: {', '.join(sorted(required))}.",
                    )
                values = (settings["retention_days"], settings["failed_login_threshold"], settings["syn_scan_threshold"])
                if any(not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in values):
                    self.logger.error("Security Monitor settings contain invalid values: %s", settings_path)
                    return ModuleResult.failed(
                        "Security Monitor settings contain invalid values.",
                        "Retention and alert thresholds must be positive integers.",
                    )
            return ModuleResult.ready("Security Monitor validation passed.")
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            self.logger.exception("Security Monitor validation failed")
            return ModuleResult.failed("Security Monitor settings could not be validated.", str(error))

    def start(self, context) -> ModuleResult:
        if self.is_running:
            return ModuleResult.ready("Security Monitor is already running.")
        self.running = False
        self.paused = False
        self.store = None
        self.capture = None
        try:
            self.store = self._store_factory(self.data_root)
            self.capture = self._capture_factory(self.record_network)
            self.running = True
            health = self.health_check(context)
            if health.state.value not in {"Ready", "Degraded"}:
                self.stop(context)
                return health
            self.logger.info("Security Monitor started and passed health check")
            return ModuleResult.ready("Security Monitor is ready.")
        except Exception as error:
            self.logger.exception("Security Monitor startup failed")
            self._cleanup_after_failure()
            return ModuleResult.failed(
                "Security Monitor could not start.",
                f"{error}\n{traceback.format_exc()}",
            )

    def health_check(self, context) -> ModuleResult:
        if not self.is_running or self.store is None or self.capture is None:
            return ModuleResult.failed("Security Monitor is not running.", retryable=True)
        try:
            self.store.settings()
            self.store.dashboard()
            self.logger.info("Security Monitor health check passed")
            return ModuleResult.ready("Security Monitor health check passed.")
        except Exception as error:
            self.logger.exception("Security Monitor health check failed")
            return ModuleResult.failed("Security Monitor health check failed.", str(error))

    def stop(self, context) -> ModuleResult:
        capture = self.capture
        was_running = self.running or capture is not None or self.store is not None
        # Set this first so callbacks racing with capture shutdown are ignored.
        self.running = False
        self.paused = False
        self.capture = None
        self.store = None
        try:
            if capture is not None:
                capture.stop()
            self.logger.info("Security Monitor stopped")
            return ModuleResult.stopped(
                "Security Monitor stopped." if was_running else "Security Monitor is already stopped."
            )
        except Exception as error:
            self.logger.exception("Security Monitor stop failed")
            return ModuleResult.failed("Security Monitor could not stop cleanly.", str(error))

    def _cleanup_after_failure(self) -> None:
        capture = self.capture
        self.running = False
        self.paused = False
        self.capture = None
        self.store = None
        if capture is not None:
            try:
                capture.stop()
            except Exception:
                self.logger.exception("Security Monitor failed while cleaning up capture")

    def pause(self) -> None:
        if not self.is_running or self.capture is None or self.store is None:
            raise RuntimeError("Security Monitor is stopped.")
        self.logger.info("Security Monitor paused")
        self.paused = True
        self.capture.stop()
        self.store.audit("monitoring_paused", "Monitoring paused for this Ann session.")

    def resume(self) -> None:
        if not self.is_running or self.store is None:
            raise RuntimeError("Security Monitor is stopped.")
        self.logger.info("Security Monitor resumed")
        self.paused = False
        self.store.audit("monitoring_resumed", "Monitoring resumed for this Ann session.")

    def record_login(self, account_id: str, source_ip: str, device_id: str | None, succeeded: bool) -> None:
        if not self.is_running or self.paused or self.store is None:
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
        if not self.is_running or self.paused or self.store is None:
            return
        try:
            self.store.enforce_retention()
            self.store.add_network(source_ip, destination_ip, protocol, destination_port, tcp_syn, tcp_ack)
            threshold = self.store.settings()["syn_scan_threshold"]
            if protocol == "tcp" and tcp_syn and not tcp_ack and self.store.recent_syn_ports(source_ip) >= threshold:
                self._alert_once("possible_port_scan", "high", source_ip, f"TCP SYN traffic reached {threshold} or more destination ports in two minutes.")
        except Exception:
            self.logger.exception("Security Monitor could not record network metadata")

    def _alert_once(self, kind: str, severity: str, subject: str, detail: str) -> None:
        if self.store is None:
            return
        if not self.store.has_recent_alert(kind, subject):
            self.store.add_alert(kind, severity, subject, detail)
            self.logger.warning("Security alert created; kind=%s severity=%s subject=%s", kind, severity, subject)

    def handle_command(self, command: str) -> str | None:
        parts = command.strip().split()
        if not parts or parts[0].lower() != "security":
            return None
        self.logger.info("Security command received: %s", command)
        if not self.is_running or self.store is None or self.capture is None:
            return "Security Monitor is stopped or unavailable. Use modules start ann.security-monitor to start it."
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
            try:
                self.start_capture(seconds)
            except (RuntimeError, OSError) as error:
                self.logger.exception("Network metadata capture could not start")
                return f"Network metadata capture is unavailable: {error}"
            return f"Network metadata capture started for up to {seconds} seconds."
        if parts[1:3] == ["capture", "stop"]:
            self.stop_capture("Metadata capture stopped by user.")
            return "Network metadata capture stopped."
        return "Security commands: status, alerts, open, pause, resume, capture start [seconds], capture stop"

    def start_capture(self, seconds: int) -> None:
        if not self.is_running or self.capture is None or self.store is None:
            raise RuntimeError("Security Monitor is stopped.")
        self.capture.start(seconds)
        self.store.audit("capture_started", f"Metadata capture started for up to {seconds} seconds.")

    def stop_capture(self, audit_detail: str) -> None:
        if not self.is_running or self.capture is None or self.store is None:
            raise RuntimeError("Security Monitor is stopped.")
        self.capture.stop()
        self.store.audit("capture_stopped", audit_detail)

    def create_dialog(self, parent) -> "QDialog":
        if not self.is_running:
            raise RuntimeError("Security Monitor is stopped.")
        from .ui import SecurityCenterDialog
        return SecurityCenterDialog(self, parent)

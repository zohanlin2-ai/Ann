from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget


class SecurityCenterDialog(QDialog):
    def __init__(self, monitor, parent=None) -> None:
        super().__init__(parent)
        self.monitor = monitor
        self.setWindowTitle("Security Center")
        self.setMinimumSize(680, 480)
        layout = QVBoxLayout(self)
        self.status = QLabel()
        self.status.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(self.status)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._dashboard(), "Dashboard")
        self.tabs.addTab(self._alerts(), "Alert Center")
        self.tabs.addTab(self._monitoring(), "Monitoring")
        self.tabs.addTab(self._privacy(), "Privacy & Data")
        self.tabs.addTab(self._permissions(), "Permissions")
        layout.addWidget(self.tabs)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignRight)
        self.refresh()

    def _dashboard(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        self.summary = QLabel(); self.summary.setWordWrap(True); layout.addWidget(self.summary)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh); layout.addWidget(refresh, alignment=Qt.AlignLeft)
        layout.addStretch(); return page

    def _alerts(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        self.alert_list = QListWidget(); layout.addWidget(self.alert_list)
        return page

    def _monitoring(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Login monitoring is active when this module is enabled. Ann currently supplies local events only."))
        layout.addWidget(QLabel("Network monitoring is disabled until you explicitly start a time-bounded session. It captures metadata only, never packet contents."))
        row = QHBoxLayout()
        self.pause_button = QPushButton("Pause monitoring")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.capture_button = QPushButton("Start network monitoring (30 sec)")
        self.capture_button.clicked.connect(self.toggle_capture)
        row.addWidget(self.pause_button); row.addWidget(self.capture_button)
        layout.addLayout(row); layout.addStretch(); return page

    def _privacy(self) -> QWidget:
        page = QWidget(); form = QFormLayout(page)
        settings = self.monitor.store.settings() if self.monitor.store else {"retention_days": 30, "failed_login_threshold": 5, "syn_scan_threshold": 20}
        self.retention = QSpinBox(); self.retention.setRange(1, 365); self.retention.setValue(settings["retention_days"])
        self.failed = QSpinBox(); self.failed.setRange(2, 100); self.failed.setValue(settings["failed_login_threshold"])
        self.syn = QSpinBox(); self.syn.setRange(5, 1000); self.syn.setValue(settings["syn_scan_threshold"])
        form.addRow("Keep event data (days)", self.retention); form.addRow("Failed logins before alert", self.failed); form.addRow("Distinct SYN ports before alert", self.syn)
        self.save_button = QPushButton("Save settings"); self.save_button.clicked.connect(self.save_settings); form.addRow(self.save_button)
        return page

    def _permissions(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        layout.addWidget(QLabel("✓ Local storage: event metadata, alerts, settings, and audit actions."))
        layout.addWidget(QLabel("○ Network capture: disabled by default; initiated only from this screen or a direct command."))
        layout.addWidget(QLabel("No account control, firewall control, packet payload retention, or TLS decryption."))
        layout.addStretch(); return page

    def refresh(self) -> None:
        if not self.monitor.is_running or self.monitor.store is None or self.monitor.capture is None:
            self.status.setText("● Security Monitor is stopped or unavailable")
            self.summary.setText("Start Security Monitor from Module List before using Security Center.")
            self.alert_list.clear()
            self.capture_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.save_button.setEnabled(False)
            return
        data = self.monitor.store.dashboard(); running = self.monitor.capture.active
        if self.monitor.paused:
            status = "Paused for this Ann session"
        else:
            status = "Network monitoring active" if running else "Read-only monitoring ready"
        self.status.setText(f"● {status}   Open alerts: {data['open_alerts']}")
        self.summary.setText(f"Login events: {data['login_events']}\nNetwork metadata observations: {data['network_events']}\n\nNetwork monitoring is {'running' if running else 'stopped'}. Start it only on authorised networks.")
        self.alert_list.clear()
        for item in self.monitor.store.alerts():
            self.alert_list.addItem(f"[{item.severity.upper()}] {item.created_at:%Y-%m-%d %H:%M} — {item.detail}")
        self.capture_button.setText("Stop network monitoring" if running else "Start network monitoring (30 sec)")
        self.pause_button.setText("Resume monitoring" if self.monitor.paused else "Pause monitoring")
        self.capture_button.setEnabled(not self.monitor.paused)
        self.pause_button.setEnabled(True)
        self.save_button.setEnabled(True)

    def toggle_pause(self) -> None:
        if not self.monitor.is_running:
            return
        if self.monitor.paused:
            self.monitor.resume()
        else:
            self.monitor.pause()
        self.refresh()

    def toggle_capture(self) -> None:
        if not self.monitor.is_running or self.monitor.capture is None:
            return
        if self.monitor.capture.active:
            self.monitor.stop_capture("Stopped from Security Center."); self.refresh(); return
        choice = QMessageBox.question(self, "Start network monitoring?", "Ann will collect network metadata only for up to 30 seconds. It will not store packet contents, decrypt traffic, or block connections. Continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if choice != QMessageBox.Yes:
            return
        if self.monitor.paused:
            QMessageBox.information(self, "Security Center", "Resume monitoring before starting network capture.")
            return
        try:
            self.monitor.start_capture(30)
        except (RuntimeError, OSError) as error:
            QMessageBox.warning(self, "Network monitoring unavailable", str(error))
        self.refresh()

    def save_settings(self) -> None:
        if not self.monitor.is_running or self.monitor.store is None:
            QMessageBox.information(self, "Security Center", "Security Monitor is stopped or unavailable.")
            return
        self.monitor.store.save_settings({"retention_days": self.retention.value(), "failed_login_threshold": self.failed.value(), "syn_scan_threshold": self.syn.value()})
        QMessageBox.information(self, "Security Center", "Settings saved.")

"""Desktop UI for Ann's Bubble, chat, and module management."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QMenu, QMessageBox,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from ann.core import AnnCore, AnnStatus


STATUS_COLORS = {AnnStatus.READY: QColor("#66B8FF"), AnnStatus.WORKING: QColor("#8D7BFF"), AnnStatus.ATTENTION: QColor("#FFB454"), AnnStatus.ERROR: QColor("#FF6B6B"), AnnStatus.OFFLINE: QColor("#8C98A8")}


class Bubble(QWidget):
    clicked = Signal()
    update_requested = Signal()
    modules_requested = Signal()
    about_requested = Signal()
    exit_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.status = AnnStatus.READY
        self.drag_position: QPoint | None = None
        self.press_position: QPoint | None = None
        self.setFixedSize(110, 110)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setToolTip("Ann — Ready")

    def set_status(self, status: AnnStatus) -> None:
        self.status = status
        self.setToolTip(f"Ann — {status.value}")
        self.update()

    def move_to_bottom_right(self, margin: int = 24) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen:
            area = screen.availableGeometry()
            self.move(area.x() + area.width() - self.width() - margin, area.y() + area.height() - self.height() - margin)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center, color = self.rect().center(), STATUS_COLORS[self.status]
        for radius, alpha, width in ((48, 25, 10), (41, 55, 5), (35, 150, 2)):
            glow = QColor(color); glow.setAlpha(alpha)
            painter.setPen(QPen(glow, width)); painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, radius, radius)
        painter.setPen(Qt.NoPen); painter.setBrush(QColor("#172131")); painter.drawEllipse(center, 30, 30)
        painter.setPen(QPen(QColor("#F3F7FF"))); painter.setFont(QFont("Segoe UI", 15, QFont.DemiBold))
        painter.drawText(self.rect(), Qt.AlignCenter, "Ann")

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.press_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self.drag_position and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        dragged = self.press_position and (event.globalPosition().toPoint() - self.press_position).manhattanLength() > 3
        self.drag_position = self.press_position = None
        if event.button() == Qt.LeftButton and not dragged:
            self.clicked.emit()

    def contextMenuEvent(self, event) -> None:  # type: ignore[override]
        menu = QMenu(self)
        update = menu.addAction("Update")
        modules = menu.addAction("Modules")
        menu.addSeparator()
        about = menu.addAction("About Ann")
        menu.addSeparator()
        exit_ann = menu.addAction("Exit Ann")
        selected = menu.exec(event.globalPos())
        signals = {update: self.update_requested, modules: self.modules_requested, about: self.about_requested, exit_ann: self.exit_requested}
        if selected in signals:
            signals[selected].emit()


class ChatWindow(QDialog):
    status_changed = Signal(AnnStatus)
    exit_requested = Signal()

    def __init__(self, core: AnnCore) -> None:
        super().__init__(); self.core = core
        self.setWindowTitle("Ann"); self.setMinimumSize(520, 440); self.resize(620, 520)
        layout = QVBoxLayout(self); layout.setContentsMargins(22, 22, 22, 22); layout.setSpacing(14)
        heading = QLabel("Ann"); heading.setObjectName("heading"); layout.addWidget(heading)
        subtitle = QLabel("Command interface"); subtitle.setObjectName("subtitle"); layout.addWidget(subtitle)
        self.output = QPlainTextEdit(readOnly=True); layout.addWidget(self.output, 1)
        row = QHBoxLayout(); self.input = QLineEdit(); self.input.setPlaceholderText("Enter a command…"); self.input.returnPressed.connect(self._submit)
        send = QPushButton("Send"); send.clicked.connect(self._submit); row.addWidget(self.input, 1); row.addWidget(send); layout.addLayout(row)
        self.setStyleSheet("QDialog { background: #101722; color: #edf4ff; } QLabel#heading { font-size: 28px; font-weight: 600; } QLabel#subtitle { color: #8fa4bc; } QPlainTextEdit, QLineEdit { background: #192434; border: 1px solid #2c3c52; border-radius: 8px; padding: 10px; color: #edf4ff; } QPushButton { background: #4d87c7; border: none; border-radius: 8px; padding: 10px 18px; color: white; font-weight: 600; }")
        self._append("Ann is ready. Type 'help' to see available commands.", "Ann")

    def _append(self, message: str, speaker: str) -> None:
        self.output.appendPlainText(f"{speaker}> {message}\n")
        self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())

    def _submit(self) -> None:
        command = self.input.text().strip()
        if not command: return
        self.input.clear(); self._append(command, "You"); self.status_changed.emit(AnnStatus.WORKING)
        result = self.core.execute(command)
        if result.text == "__CLEAR__": self.output.clear()
        else: self._append(result.text, "Ann")
        self.status_changed.emit(result.status)
        if result.status is AnnStatus.OFFLINE: self.exit_requested.emit()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        event.ignore(); self.hide()


class ModuleListDialog(QDialog):
    def __init__(self, core: AnnCore) -> None:
        super().__init__(); self.core = core
        self.setWindowTitle("Downloaded Modules"); self.setMinimumWidth(420)
        layout = QVBoxLayout(self); layout.addWidget(QLabel("Module List"))
        for module in core.registry.list_modules():
            checkbox = QCheckBox(f"{module['name']}  ({module['id']})  {module['version']}")
            checkbox.setChecked(module["enabled"]); checkbox.setEnabled(not module["system"])
            if module["system"]: checkbox.setToolTip("Required system module")
            checkbox.toggled.connect(lambda enabled, module_id=module["id"]: self._set_enabled(module_id, enabled))
            layout.addWidget(checkbox)
        close = QPushButton("Close"); close.clicked.connect(self.accept); layout.addWidget(close)

    def _set_enabled(self, module_id: str, enabled: bool) -> None:
        try: self.core.registry.set_enabled(module_id, enabled)
        except ValueError as error: QMessageBox.warning(self, "Module List", str(error))


class UpdateDialog(QDialog):
    def __init__(self, core: AnnCore) -> None:
        super().__init__(); self.core = core
        self.setWindowTitle("Update"); self.setMinimumSize(480, 300)
        layout = QVBoxLayout(self); layout.addWidget(QLabel("GitHub Update Module"))
        self.output = QPlainTextEdit(readOnly=True); self.output.setPlainText("Check GitHub for Ann Core and module updates."); layout.addWidget(self.output, 1)
        row = QHBoxLayout()
        check = QPushButton("Check for Updates"); check.clicked.connect(lambda: self._run("update check"))
        core_update = QPushButton("Update Ann Core"); core_update.clicked.connect(lambda: self._run("update ann"))
        row.addWidget(check); row.addWidget(core_update); layout.addLayout(row)
        close = QPushButton("Close"); close.clicked.connect(self.accept); layout.addWidget(close)

    def _run(self, command: str) -> None:
        self.output.setPlainText(self.core.execute(command).text)

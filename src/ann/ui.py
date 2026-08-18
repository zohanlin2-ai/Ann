"""Desktop UI for Ann's bubble and command chat window."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ann.core import AnnCore, AnnStatus


STATUS_COLORS = {
    AnnStatus.READY: QColor("#66B8FF"),
    AnnStatus.WORKING: QColor("#8D7BFF"),
    AnnStatus.ATTENTION: QColor("#FFB454"),
    AnnStatus.ERROR: QColor("#FF6B6B"),
    AnnStatus.OFFLINE: QColor("#8C98A8"),
}


class Bubble(QWidget):
    """A compact, draggable, always-on-top status control."""

    clicked = Signal()

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

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event
        color = STATUS_COLORS[self.status]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self.rect().center()

        for radius, alpha, width in ((48, 25, 10), (41, 55, 5), (35, 150, 2)):
            glow = QColor(color)
            glow.setAlpha(alpha)
            painter.setPen(QPen(glow, width))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, radius, radius)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#172131"))
        painter.drawEllipse(center, 30, 30)
        painter.setPen(QPen(QColor("#F3F7FF")))
        font = QFont("Segoe UI", 18, QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "A")

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.press_position = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self.drag_position and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        was_dragging = self.press_position and (
            event.globalPosition().toPoint() - self.press_position
        ).manhattanLength() > 3
        self.drag_position = None
        self.press_position = None
        if event.button() == Qt.LeftButton and not was_dragging:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class ChatWindow(QDialog):
    """Command-only conversation window for the first Ann milestone."""

    status_changed = Signal(AnnStatus)

    def __init__(self, core: AnnCore) -> None:
        super().__init__()
        self.core = core
        self.setWindowTitle("Ann")
        self.setMinimumSize(520, 440)
        self.resize(620, 520)
        self._build_ui()
        self._append("Ann is ready. Type 'help' to see available commands.", "Ann")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        heading = QLabel("Ann")
        heading.setObjectName("heading")
        subtitle = QLabel("Command interface")
        subtitle.setObjectName("subtitle")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        self.output = QPlainTextEdit(readOnly=True)
        self.output.setObjectName("output")
        layout.addWidget(self.output, 1)

        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter a command…")
        self.input.returnPressed.connect(self._submit)
        send = QPushButton("Send")
        send.clicked.connect(self._submit)
        input_row.addWidget(self.input, 1)
        input_row.addWidget(send)
        layout.addLayout(input_row)

        self.setStyleSheet(
            "QDialog { background: #101722; color: #edf4ff; }"
            "QLabel#heading { font-size: 28px; font-weight: 600; }"
            "QLabel#subtitle { color: #8fa4bc; }"
            "QPlainTextEdit, QLineEdit { background: #192434; border: 1px solid #2c3c52; border-radius: 8px; padding: 10px; color: #edf4ff; }"
            "QPushButton { background: #4d87c7; border: none; border-radius: 8px; padding: 10px 18px; color: white; font-weight: 600; }"
            "QPushButton:hover { background: #609bdd; }"
        )

    def _append(self, message: str, speaker: str) -> None:
        self.output.appendPlainText(f"{speaker}> {message}\n")
        self.output.verticalScrollBar().setValue(self.output.verticalScrollBar().maximum())

    def _submit(self) -> None:
        command = self.input.text().strip()
        if not command:
            return
        self.input.clear()
        self._append(command, "You")
        self.status_changed.emit(AnnStatus.WORKING)
        result = self.core.execute(command)
        if result.text == "__CLEAR__":
            self.output.clear()
        else:
            self._append(result.text, "Ann")
        self.status_changed.emit(result.status)
        self.input.setFocus()

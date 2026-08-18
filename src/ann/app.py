"""Application composition root."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from ann.core import AnnCore
from ann.ui import Bubble, ChatWindow, show_update_message
from ann.version_info import current_release_text


def show_about(parent: Bubble) -> None:
    QMessageBox.about(
        parent,
        "About Ann",
        "Ann\n\n"
        f"{current_release_text()}\n\n"
        "Runtime\n"
        f"Python: {sys.version.split()[0]}",
    )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Ann")
    app.setQuitOnLastWindowClosed(False)
    core = AnnCore()
    bubble = Bubble()
    chat = ChatWindow(core)
    bubble.clicked.connect(chat.showNormal)
    chat.status_changed.connect(bubble.set_status)
    chat.exit_requested.connect(app.quit)
    bubble.update_requested.connect(lambda: show_update_message(bubble))
    bubble.about_requested.connect(lambda: show_about(bubble))
    bubble.exit_requested.connect(app.quit)
    bubble.move_to_bottom_right()
    bubble.show()
    return app.exec()

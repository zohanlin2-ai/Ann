"""Application composition root."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ann.core import AnnCore
from ann.ui import Bubble, ChatWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Ann")
    app.setQuitOnLastWindowClosed(False)
    core = AnnCore()
    bubble = Bubble()
    chat = ChatWindow(core)
    bubble.clicked.connect(chat.showNormal)
    chat.status_changed.connect(bubble.set_status)
    bubble.show()
    return app.exec()

"""Ann Core application composition root."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from ann.core import AnnCore
from ann.ui import Bubble, ChatWindow, ModuleListDialog, UpdateDialog
from ann.version_info import current_release_text


def show_about(parent: Bubble) -> None:
    QMessageBox.about(parent, "About Ann", f"Ann\n\n{current_release_text()}\n\nRuntime\nPython: {sys.version.split()[0]}")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Ann")
    app.setQuitOnLastWindowClosed(False)
    project_root = Path(os.environ.get("ANN_PROJECT_ROOT", Path(__file__).resolve().parents[3]))
    core_root = Path(os.environ.get("ANN_CORE_DIR", Path(__file__).resolve().parents[2]))
    core = AnnCore(project_root, core_root)
    bubble = Bubble()
    chat = ChatWindow(core)
    bubble.clicked.connect(chat.showNormal)
    chat.status_changed.connect(bubble.set_status)
    chat.exit_requested.connect(app.quit)
    bubble.update_requested.connect(lambda: UpdateDialog(core).exec())
    bubble.modules_requested.connect(lambda: ModuleListDialog(core).exec())
    bubble.about_requested.connect(lambda: show_about(bubble))
    bubble.exit_requested.connect(app.quit)
    bubble.move_to_bottom_right()
    bubble.show()
    marker = os.environ.get("ANN_TRIAL_MARKER")
    if marker:
        Path(marker).touch()
    return app.exec()

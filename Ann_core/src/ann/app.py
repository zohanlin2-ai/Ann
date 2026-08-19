"""Ann Core application composition root."""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from ann.core import AnnCore
from ann.debug_log import get_module_logger
from ann.ui import Bubble, ChatWindow, ModuleListDialog, UpdateDialog
from ann.version_info import current_release_text


def show_about(parent: Bubble) -> None:
    QMessageBox.about(parent, "About Ann", f"Ann\n\n{current_release_text()}\n\nRuntime\nPython: {sys.version.split()[0]}")


def show_security(parent: Bubble, core: AnnCore) -> None:
    module = core.get_module("ann.security-monitor")
    dialog_factory = getattr(module, "create_dialog", None) if module else None
    if not callable(dialog_factory):
        QMessageBox.information(parent, "Security Center", "Security Monitor is disabled or unavailable. Enable it in Modules first.")
        return
    dialog_factory(parent).exec()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Ann")
    app.setQuitOnLastWindowClosed(False)
    project_root = Path(os.environ.get("ANN_PROJECT_ROOT", Path(__file__).resolve().parents[3]))
    core_root = Path(os.environ.get("ANN_CORE_DIR", Path(__file__).resolve().parents[2]))
    core_logger = get_module_logger(project_root, "ann.core")
    core_logger.info("Starting Ann Core; core_pid=%s", os.getpid())
    core = AnnCore(project_root, core_root)
    def request_quit(reason: str) -> None:
        core_logger.info("Quit requested; core_pid=%s reason=%s", os.getpid(), reason)
        app.quit()

    def on_about_to_quit() -> None:
        core_logger.info("QApplication aboutToQuit; core_pid=%s", os.getpid())
        core.stop_all_modules()

    app.aboutToQuit.connect(on_about_to_quit)
    bubble = Bubble()
    chat = ChatWindow(core)
    bubble.clicked.connect(chat.showNormal)
    chat.status_changed.connect(bubble.set_status)
    chat.exit_requested.connect(lambda: request_quit("chat exit command"))
    chat.restart_requested.connect(lambda: request_quit("chat update restart"))
    def show_update() -> None:
        dialog = UpdateDialog(core)
        dialog.restart_requested.connect(lambda: request_quit("Update Ann completed"))
        dialog.exec()

    bubble.update_requested.connect(show_update)
    bubble.modules_requested.connect(lambda: ModuleListDialog(core).exec())
    bubble.security_requested.connect(lambda: show_security(bubble, core))
    bubble.about_requested.connect(lambda: show_about(bubble))
    bubble.exit_requested.connect(lambda: request_quit("bubble exit action"))
    bubble.move_to_bottom_right()
    bubble.show()
    core_logger.info("Ann Core UI started successfully")
    ready_file = os.environ.get("ANN_CORE_READY_FILE")
    if ready_file:
        module_summary = {module_id: result.state.value for module_id, result in core.module_results.items()}
        Path(ready_file).write_text(json.dumps({"status": "Ready", "module_summary": module_summary}) + "\n", encoding="utf-8")
        core_logger.info("Ann Core reported Ready to launcher")
    marker = os.environ.get("ANN_TRIAL_MARKER")
    if marker:
        Path(marker).touch()
    exit_code = app.exec()
    core_logger.info("QApplication event loop returned; core_pid=%s exit_code=%s", os.getpid(), exit_code)
    return exit_code

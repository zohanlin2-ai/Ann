"""The small command-oriented core used by Ann's user interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AnnStatus(str, Enum):
    READY = "Ready"
    WORKING = "Working"
    ATTENTION = "Needs attention"
    ERROR = "Error"
    OFFLINE = "Offline"


@dataclass(frozen=True)
class CommandResult:
    text: str
    status: AnnStatus = AnnStatus.READY


class AnnCore:
    """Minimal command router; modules will be registered here in a later milestone."""

    def __init__(self) -> None:
        self.awaiting_exit_confirmation = False

    def execute(self, command: str) -> CommandResult:
        command = command.strip()
        if not command:
            return CommandResult("Enter a command, or type 'help' to see available commands.")

        normalized = command.lower()
        if self.awaiting_exit_confirmation:
            if normalized == "y":
                self.awaiting_exit_confirmation = False
                return CommandResult("Ann is shutting down.", AnnStatus.OFFLINE)
            if normalized == "n":
                self.awaiting_exit_confirmation = False
                return CommandResult("Exit cancelled.")
            return CommandResult("Please enter Y or N.", AnnStatus.ATTENTION)

        if normalized == "help":
            return CommandResult(
                "Available commands:\n"
                "  help          Show this message\n"
                "  status        Show Ann's current status\n"
                "  modules list  List installed modules\n"
                "  clear         Clear the conversation\n"
                "  exit / quit   Close Ann after Y/N confirmation"
            )
        if normalized == "status":
            return CommandResult("Ann is ready.")
        if normalized == "modules list":
            return CommandResult("No optional modules are installed yet.")
        if normalized == "clear":
            return CommandResult("__CLEAR__")
        if normalized in {"exit", "quit"}:
            self.awaiting_exit_confirmation = True
            return CommandResult("Exit Ann? (Y/N)", AnnStatus.ATTENTION)
        return CommandResult(f"Unknown command: {command}\nType 'help' for available commands.", AnnStatus.ATTENTION)

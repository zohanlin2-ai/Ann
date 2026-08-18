"""Command router backed by Ann's persistent module registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ann.module_runtime import load_enabled_modules, load_updater
from ann.registry import ModuleRegistry


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
    restart_for_update: bool = False


class AnnCore:
    def __init__(self, project_root: Path, core_root: Path) -> None:
        self.awaiting_exit_confirmation = False
        self.registry = ModuleRegistry(project_root, core_root)
        self.updater = load_updater(project_root, core_root, self.registry)
        self.modules, self.module_load_errors = load_enabled_modules(project_root, self.registry)

    def get_module(self, module_id: str) -> object | None:
        return self.modules.get(module_id)

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
        try:
            return self._execute(normalized, command)
        except (OSError, ValueError, KeyError) as error:
            return CommandResult(f"Command failed: {error}", AnnStatus.ERROR)

    def _execute(self, normalized: str, original: str) -> CommandResult:
        if normalized == "help":
            return CommandResult(
                "Available commands:\n"
                "  modules list\n"
                "  modules enable <module-id>\n"
                "  modules disable <module-id>\n"
                "  update check\n"
                "  update ann\n"
                "  security open\n"
                "  security status\n"
                "  security alerts\n"
                "  clear\n"
                "  exit / quit"
            )
        if normalized == "status":
            return CommandResult("Ann is ready.")
        if normalized == "modules list":
            return CommandResult(self.registry.format_modules())
        if normalized.startswith("modules enable "):
            module_id = original.split(maxsplit=2)[2]
            self.registry.set_enabled(module_id, True)
            return CommandResult(f"Module '{module_id}' is enabled.")
        if normalized.startswith("modules disable "):
            module_id = original.split(maxsplit=2)[2]
            self.registry.set_enabled(module_id, False)
            return CommandResult(f"Module '{module_id}' is disabled.")
        if normalized == "update check":
            return CommandResult(self.updater.check())
        if normalized == "update ann":
            return self.updater.stage_project_update()
        if normalized == "clear":
            return CommandResult("__CLEAR__")
        if normalized in {"exit", "quit"}:
            self.awaiting_exit_confirmation = True
            return CommandResult("Exit Ann? (Y/N)", AnnStatus.ATTENTION)
        for module in self.modules.values():
            handler = getattr(module, "handle_command", None)
            if callable(handler):
                response = handler(original)
                if response is not None:
                    return CommandResult(response)
        return CommandResult(f"Unknown command: {original}\nType 'help' for available commands.", AnnStatus.ATTENTION)

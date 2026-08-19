"""Command router backed by Ann's persistent module registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ann.debug_log import get_module_logger
from ann.module_lifecycle import ModuleResult, ModuleState
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


class UnavailableUpdater:
    def __init__(self, message: str) -> None:
        self.message = message

    def check(self) -> str:
        return self.message

    def stage_project_update(self) -> CommandResult:
        return CommandResult(self.message, AnnStatus.ERROR)


class AnnCore:
    def __init__(self, project_root: Path, core_root: Path) -> None:
        self.awaiting_exit_confirmation = False
        self.project_root = project_root
        self.core_root = core_root
        self.logger = get_module_logger(project_root, "ann.core")
        self.registry = ModuleRegistry(project_root, core_root)
        self.module_results: dict[str, ModuleResult] = {}
        try:
            self.updater = load_updater(project_root, core_root, self.registry)
            self.module_results["ann.updater"] = self._start_module("ann.updater", self.updater)
        except Exception as error:
            self.logger.exception("Ann Updater could not be loaded")
            message = f"Ann Updater is unavailable: {error}"
            self.updater = UnavailableUpdater(message)
            self.module_results["ann.updater"] = ModuleResult.failed(message, str(error))
        self._load_optional_modules()

    def _start_module(self, module_id: str, module: object) -> ModuleResult:
        starter = getattr(module, "start", None)
        try:
            result = starter(self) if callable(starter) else ModuleResult.ready("Loaded through legacy module adapter.")
        except Exception as error:
            self.logger.exception("Module startup failed: %s", module_id)
            result = ModuleResult.failed(f"Module '{module_id}' failed to start.", str(error))
        self.logger.info("Module %s state=%s message=%s", module_id, result.state.value, result.message)
        return result

    def _load_optional_modules(self) -> None:
        self.modules, self.module_load_errors = load_enabled_modules(self.project_root, self.registry)
        for error in self.module_load_errors:
            module_id, _, details = error.partition(": ")
            self.module_results[module_id] = ModuleResult.failed(f"Module '{module_id}' failed to load.", details)
            self.logger.error("%s", error)
        for module_id, module in self.modules.items():
            self.module_results[module_id] = self._start_module(module_id, module)

    def get_module(self, module_id: str) -> object | None:
        result = self.module_results.get(module_id)
        return self.modules.get(module_id) if result is None or result.state is not ModuleState.FAILED else None

    def format_module_status(self) -> str:
        lines = ["Module                 Runtime state       Details"]
        for module in self.registry.list_modules():
            result = self.module_results.get(module["id"])
            state = result.state.value if result else ("Disabled" if not module["enabled"] else "Not started")
            details = result.message if result else ""
            lines.append(f"{module['id']:<22} {state:<19} {details}")
        return "\n".join(lines)

    def retry_module(self, module_id: str) -> CommandResult:
        if module_id == "ann.updater":
            try:
                self.updater = load_updater(self.project_root, self.core_root, self.registry)
                self.module_results[module_id] = self._start_module(module_id, self.updater)
            except Exception as error:
                self.logger.exception("Ann Updater retry failed")
                message = f"Ann Updater is unavailable: {error}"
                self.updater = UnavailableUpdater(message)
                self.module_results[module_id] = ModuleResult.failed(message, str(error))
        else:
            self._load_optional_modules()
        result = self.module_results.get(module_id)
        if result is None:
            return CommandResult(f"Module '{module_id}' is not enabled or is not installed.", AnnStatus.ATTENTION)
        status = AnnStatus.READY if result.state is ModuleState.READY else AnnStatus.ERROR
        return CommandResult(result.message, status)

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
                "  modules status\n"
                "  modules retry <module-id>\n"
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
        if normalized == "modules status":
            return CommandResult(self.format_module_status())
        if normalized.startswith("modules retry "):
            return self.retry_module(original.split(maxsplit=2)[2])
        if normalized.startswith("modules enable "):
            module_id = original.split(maxsplit=2)[2]
            self.registry.set_enabled(module_id, True)
            return CommandResult(f"Module '{module_id}' is enabled.")
        if normalized.startswith("modules disable "):
            module_id = original.split(maxsplit=2)[2]
            self.registry.set_enabled(module_id, False)
            return CommandResult(f"Module '{module_id}' is disabled.")
        if normalized == "update check":
            updater_result = self.module_results.get("ann.updater")
            if updater_result and updater_result.state is ModuleState.FAILED:
                return CommandResult(updater_result.message, AnnStatus.ERROR)
            return CommandResult(self.updater.check())
        if normalized == "update ann":
            updater_result = self.module_results.get("ann.updater")
            if updater_result and updater_result.state is ModuleState.FAILED:
                return CommandResult(updater_result.message, AnnStatus.ERROR)
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

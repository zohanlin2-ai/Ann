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
        self.modules: dict[str, object] = {}
        self.module_load_errors: list[str] = []
        self.module_results["ann.core"] = ModuleResult.ready("Ann Core is ready.")
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
        validator = getattr(module, "validate", None)
        starter = getattr(module, "start", None)
        try:
            validation = validator(self) if callable(validator) else ModuleResult.ready()
            if isinstance(validation, ModuleResult) and validation.state not in {ModuleState.READY, ModuleState.DEGRADED}:
                result = validation
            else:
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
        if result and result.state not in {ModuleState.READY, ModuleState.DEGRADED}:
            return None
        return self.modules.get(module_id)

    def _module_instance(self, module_id: str) -> object | None:
        if module_id == "ann.updater":
            return self.updater
        return self.modules.get(module_id)

    def _module_entry(self, module_id: str) -> dict | None:
        return next((item for item in self.registry.list_modules() if item["id"] == module_id), None)

    def _load_optional_module(self, module_id: str) -> ModuleResult | None:
        loaded, errors = load_enabled_modules(self.project_root, self.registry)
        for error in errors:
            error_id, _, details = error.partition(": ")
            if error_id == module_id:
                self.module_results[module_id] = ModuleResult.failed(f"Module '{module_id}' failed to load.", details)
                self.logger.error("%s", error)
                return self.module_results[module_id]
        module = loaded.get(module_id)
        if module is None:
            return None
        self.modules[module_id] = module
        return self._start_module(module_id, module)

    def format_module_status(self) -> str:
        lines = ["Module                 Runtime state       Details"]
        for module in self.registry.list_modules():
            result = self.module_results.get(module["id"])
            state = result.state.value if result else ("Disabled" if not module["enabled"] else "Not started")
            details = result.message if result else ""
            lines.append(f"{module['id']:<22} {state:<19} {details}")
        return "\n".join(lines)

    def retry_module(self, module_id: str) -> CommandResult:
        return self.start_module(module_id, retry=True)

    def start_module(self, module_id: str, retry: bool = False) -> CommandResult:
        entry = self._module_entry(module_id)
        if entry is None:
            return CommandResult(f"Module '{module_id}' is not installed.", AnnStatus.ATTENTION)
        if module_id == "ann.core":
            return CommandResult("Ann Core is already running and cannot be started separately.", AnnStatus.ATTENTION)
        if not entry["enabled"]:
            return CommandResult(f"Module '{module_id}' is disabled. Enable it before starting it.", AnnStatus.ATTENTION)
        current = self.module_results.get(module_id)
        if current and current.state in {ModuleState.READY, ModuleState.DEGRADED} and not retry:
            return CommandResult(f"Module '{module_id}' is already running.", AnnStatus.ATTENTION)
        if module_id == "ann.updater":
            try:
                self.updater = load_updater(self.project_root, self.core_root, self.registry)
                self.module_results[module_id] = self._start_module(module_id, self.updater)
            except Exception as error:
                self.logger.exception("Ann Updater retry failed")
                message = f"Ann Updater is unavailable: {error}"
                self.updater = UnavailableUpdater(message)
                self.module_results[module_id] = ModuleResult.failed(message, str(error))
        elif self._module_instance(module_id) is None or (current and current.state is ModuleState.FAILED):
            result = self._load_optional_module(module_id)
            if result is None:
                return CommandResult(f"Module '{module_id}' could not be loaded.", AnnStatus.ERROR)
        else:
            self.module_results[module_id] = self._start_module(module_id, self._module_instance(module_id))
        result = self.module_results.get(module_id)
        if result is None:
            return CommandResult(f"Module '{module_id}' is not enabled or is not installed.", AnnStatus.ATTENTION)
        status = AnnStatus.READY if result.state in {ModuleState.READY, ModuleState.DEGRADED} else AnnStatus.ERROR
        return CommandResult(result.message, status)

    def stop_module(self, module_id: str) -> CommandResult:
        if module_id == "ann.core":
            return CommandResult("Ann Core cannot be stopped independently. Exit Ann to stop it.", AnnStatus.ATTENTION)
        entry = self._module_entry(module_id)
        module = self._module_instance(module_id)
        result = self.module_results.get(module_id)
        if entry is None or module is None or result is None:
            return CommandResult(f"Module '{module_id}' is not running.", AnnStatus.ATTENTION)
        if result.state is ModuleState.STOPPED:
            return CommandResult(f"Module '{module_id}' is already stopped.", AnnStatus.ATTENTION)
        if result.state is ModuleState.FAILED:
            return CommandResult(f"Module '{module_id}' is unavailable; use retry to start it again.", AnnStatus.ATTENTION)
        stopper = getattr(module, "stop", None)
        if not callable(stopper):
            return CommandResult(f"Module '{module_id}' does not support controlled stopping.", AnnStatus.ATTENTION)
        try:
            stop_result = stopper(self)
        except Exception as error:
            self.logger.exception("Module stop failed: %s", module_id)
            self.module_results[module_id] = ModuleResult.failed(f"Module '{module_id}' failed to stop.", str(error))
        else:
            if isinstance(stop_result, ModuleResult) and stop_result.state is ModuleState.FAILED:
                self.module_results[module_id] = stop_result
            else:
                message = stop_result.message if isinstance(stop_result, ModuleResult) else f"Module '{module_id}' stopped."
                self.module_results[module_id] = ModuleResult.stopped(message)
        final = self.module_results[module_id]
        self.logger.info("Module %s state=%s message=%s", module_id, final.state.value, final.message)
        return CommandResult(final.message, AnnStatus.READY if final.state is ModuleState.STOPPED else AnnStatus.ERROR)

    def restart_module(self, module_id: str) -> CommandResult:
        current = self.module_results.get(module_id)
        if current and current.state in {ModuleState.READY, ModuleState.DEGRADED}:
            stopped = self.stop_module(module_id)
            if self.module_results.get(module_id, current).state is not ModuleState.STOPPED:
                return stopped
        return self.start_module(module_id, retry=True)

    def stop_all_modules(self) -> None:
        for module_id, result in list(self.module_results.items()):
            if module_id != "ann.core" and result.state in {ModuleState.READY, ModuleState.DEGRADED}:
                self.stop_module(module_id)

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
                "  modules start <module-id>\n"
                "  modules stop <module-id>\n"
                "  modules restart <module-id>\n"
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
        if normalized.startswith("modules start "):
            return self.start_module(original.split(maxsplit=2)[2])
        if normalized.startswith("modules stop "):
            return self.stop_module(original.split(maxsplit=2)[2])
        if normalized.startswith("modules restart "):
            return self.restart_module(original.split(maxsplit=2)[2])
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
        for module_id, module in self.modules.items():
            if self.module_results.get(module_id, ModuleResult.ready()).state not in {ModuleState.READY, ModuleState.DEGRADED}:
                continue
            handler = getattr(module, "handle_command", None)
            if callable(handler):
                response = handler(original)
                if response is not None:
                    return CommandResult(response)
        return CommandResult(f"Unknown command: {original}\nType 'help' for available commands.", AnnStatus.ATTENTION)

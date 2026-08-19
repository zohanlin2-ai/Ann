"""Shared lifecycle results for Ann modules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModuleState(str, Enum):
    STARTING = "Starting"
    READY = "Ready"
    STOPPED = "Stopped"
    DEGRADED = "Degraded"
    FAILED = "Failed"


@dataclass(frozen=True)
class ModuleResult:
    state: ModuleState
    message: str
    details: str = ""
    retryable: bool = True

    @classmethod
    def ready(cls, message: str = "Ready.") -> "ModuleResult":
        return cls(ModuleState.READY, message)

    @classmethod
    def stopped(cls, message: str = "Stopped.") -> "ModuleResult":
        return cls(ModuleState.STOPPED, message)

    @classmethod
    def failed(cls, message: str, details: str = "", retryable: bool = True) -> "ModuleResult":
        return cls(ModuleState.FAILED, message, details, retryable)

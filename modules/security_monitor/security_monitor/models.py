from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


def now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Alert:
    kind: str
    severity: str
    subject: str
    detail: str
    created_at: datetime
    status: str = "open"
    id: int | None = None

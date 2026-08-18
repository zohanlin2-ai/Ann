"""Read VERSION.md from the stable project root."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(os.environ.get("ANN_PROJECT_ROOT", Path(__file__).resolve().parents[3]))


def current_release_text() -> str:
    lines = (PROJECT_ROOT / "VERSION.md").read_text(encoding="utf-8").splitlines()
    rows: list[str] = []
    active = False
    for line in lines:
        if line == "## Current Release":
            active = True
            continue
        if active and line.startswith("## "):
            break
        if active and line.startswith("| ") and "---" not in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells[0] != "Component":
                rows.append(f"{cells[0]}: {cells[1]}")
    return "\n".join(rows) or "Version information is unavailable."

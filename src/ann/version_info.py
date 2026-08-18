"""Read the human-maintained current-release table from VERSION.md."""

from __future__ import annotations

from pathlib import Path


VERSION_FILE = Path(__file__).resolve().parents[2] / "VERSION.md"


def current_release_text() -> str:
    """Return the component/version rows from VERSION.md for the About dialog."""
    lines = VERSION_FILE.read_text(encoding="utf-8").splitlines()
    rows: list[str] = []
    in_current_release = False
    for line in lines:
        if line == "## Current Release":
            in_current_release = True
            continue
        if in_current_release and line.startswith("## "):
            break
        if in_current_release and line.startswith("| ") and "---" not in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells[0] != "Component":
                rows.append(f"{cells[0]}: {cells[1]}")
    return "\n".join(rows) or "Version information is unavailable."

"""Dependency-aware entry point for the modular Ann Core."""

from __future__ import annotations

import importlib.metadata
import os
import sys
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = Path(os.environ.get("ANN_PROJECT_ROOT", CORE_ROOT.parent))
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"


def pinned_requirements(path: Path) -> list[tuple[str, str]]:
    """Read pinned requirements, including project-local `-r` files."""
    items: list[tuple[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r "):
            items.extend(pinned_requirements(path.parent / line[3:].strip()))
            continue
        package, expected = line.split("==", maxsplit=1)
        items.append((package, expected))
    return items


def verify_dependencies() -> bool:
    missing: list[str] = []
    for package, expected in pinned_requirements(REQUIREMENTS):
        try:
            installed = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            missing.append(f"{package}=={expected} (not installed)")
            continue
        if installed != expected:
            missing.append(f"{package}=={expected} (installed: {installed})")
    if not missing:
        return True
    print("Ann cannot start because required packages are missing or incompatible:")
    print("\n".join(f"  - {item}" for item in missing))
    print(f'\nInstall them with:\n  "{sys.executable}" -m pip install -r requirements.txt')
    return False


if __name__ == "__main__":
    if not verify_dependencies():
        raise SystemExit(1)
    sys.path.insert(0, str(CORE_ROOT / "src"))
    if "--verify-update" in sys.argv:
        from ann.verify_update import verify_update

        raise SystemExit(0 if verify_update(PROJECT_ROOT, CORE_ROOT) else 1)
    from ann.app import main

    raise SystemExit(main())

"""Ann's dependency-aware launcher.

Run this file directly during development: ``python main.py``.
"""

from __future__ import annotations

import importlib.metadata
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REQUIREMENTS = ROOT / "requirements.txt"


def required_packages() -> dict[str, str]:
    packages: dict[str, str] = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, version = line.split("==", maxsplit=1)
        packages[name] = version
    return packages


def verify_dependencies() -> bool:
    missing_or_incompatible: list[str] = []
    for package, expected_version in required_packages().items():
        try:
            installed_version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            missing_or_incompatible.append(f"{package}=={expected_version} (not installed)")
            continue
        if installed_version != expected_version:
            missing_or_incompatible.append(
                f"{package}=={expected_version} (installed: {installed_version})"
            )

    if not missing_or_incompatible:
        return True

    print("Ann cannot start because required packages are missing or incompatible:")
    for package in missing_or_incompatible:
        print(f"  - {package}")
    print("\nInstall the required versions with:")
    print(f'  "{sys.executable}" -m pip install -r requirements.txt')
    return False


if __name__ == "__main__":
    if not verify_dependencies():
        raise SystemExit(1)
    sys.path.insert(0, str(ROOT / "src"))
    from ann.app import main

    raise SystemExit(main())

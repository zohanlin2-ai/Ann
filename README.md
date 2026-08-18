# Ann

Ann is a modular AI Assistant designed to stay small at its core and grow through independently managed modules. The core application provides the shared runtime, configuration, module discovery, and capability routing. Modules provide the features.

## Goals

- Keep the default installation simple and focused.
- Add capabilities without changing the core application.
- Let users review, install, enable, disable, and update modules independently.
- Keep every module's implementation and detailed documentation together.
- Support a GitHub-based module catalog so Ann can check for available updates and optional features.

## Architecture

Ann has two layers:

1. **Core** — Starts Ann, loads configuration, discovers modules, routes requests, records logs, and applies permission rules.
2. **Modules** — Add focused features such as commands, integrations, user interfaces, memory, notifications, or scheduled tasks.

The core should not depend on a particular module. A module declares its identity, version, entry point, dependencies, and requested permissions in a manifest file.

## Proposed Project Layout

```text
Ann/
├── src/
│   ├── ann/                     # Core application
│   └── modules/                 # Installed modules
│       └── example-module/
│           ├── module.py         # Module implementation
│           ├── manifest.json     # Module metadata and compatibility
│           ├── README.md         # Complete module documentation
│           └── tests/            # Module-specific tests
├── tests/                        # Core tests
├── README.md                     # This overview
└── CHANGELOG.md                  # Project-level release history
```

## Modules

Each module must be self-contained in its own directory. Its detailed documentation must live beside its source code, normally in that module's `README.md`.

The project-level README only provides a short catalog entry for each available module. Detailed setup instructions, configuration reference, permissions, examples, compatibility notes, limitations, and troubleshooting belong in the module directory.

A module manifest is expected to describe at least:

- A stable module identifier and display name
- Version and Ann core compatibility requirements
- Entry point
- Dependencies
- Requested permissions, such as network or file-system access
- Optional configuration schema

## Module Catalog and Updates

The canonical Ann repository is intended to be hosted at [zohanlin2-ai/Ann](https://github.com/zohanlin2-ai/Ann).

Ann can use the repository as a module catalog. On request, the core can compare locally installed module versions with the published catalog, report available updates, and let the user choose which optional modules to install or enable. Updates should always be reviewed before installation, especially when a module requests new permissions.

The exact catalog format and update mechanism will be defined with the first working module system. A future catalog should include module version, compatibility information, source location, integrity information, and release notes.

## Security Principles

- Modules should have the minimum permissions needed for their purpose.
- Permission requests should be explicit and visible to the user.
- The core should verify compatibility and package integrity before installing updates.
- Module updates should not be applied silently unless the user explicitly enables automatic updates.

## Status

Ann currently includes its first desktop UI milestone: a draggable status bubble with a glowing state ring and a command-only chat window. The command core currently supports `help`, `status`, `modules list`, and `clear`.

## Requirements and Installation

### Technology and Dependency Record

Ann is currently written in **Python** and uses **PySide6** for its desktop interface. This table is the single human-readable record of the runtime environment. Whenever a dependency changes, this table, `requirements.txt`, and `pyproject.toml` must be updated in the same change.

| Item | Required version | Purpose |
| --- | --- | --- |
| Python | 3.10 or newer | Ann core, module runtime, and launcher |
| PySide6 | 6.8.0.2 | Desktop bubble, status ring, and command window |

`requirements.txt` and `pyproject.toml` contain the same pinned dependency information in machine-readable form so installation and startup checks can use it reliably.

### Windows Development Setup

Use an official Windows CPython installation (Python 3.10 or newer) and create a virtual environment in the project directory. Do not use the MSYS2/MinGW Python for this installation workflow because PyPI does not provide a compatible PySide6 wheel for that platform.

In PowerShell, from the project directory:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

If the Python Launcher cannot resolve the desired version, replace `py -3.10` in the first command with the full path to an installed CPython executable:

```powershell
& "C:\Path\To\Python\python.exe" -m venv .venv
```

After the environment has been created, start Ann with:

```powershell
.\.venv\Scripts\python.exe main.py
```

`main.py` checks required packages and versions before Ann starts. If a package is missing or incompatible, it stops and prints the exact installation command. It does not install packages automatically.

## Development and Distribution

During development, Ann runs in a project-specific Python virtual environment. This keeps the Python interpreter and dependency versions reproducible without changing the system Python installation.

End users will not be expected to install, configure, or manage Python. A future release build will bundle Ann, its Python runtime, and its required dependencies into a native Windows application and installer. The bundled runtime will be controlled by Ann, so it will not depend on or conflict with Python versions already installed on the user's computer.

Modules will declare compatibility with Ann releases rather than relying on the user's system Python version. The exact packaging tool and release workflow will be selected before the first distributable release.

## Versioning Rules

Ann uses the version format `A.B.C`.

The current release is recorded in [VERSION.md](VERSION.md). `VERSION.md`, `pyproject.toml`, and `CHANGELOG.md` must be kept consistent whenever the Ann Core version changes.

- `A` is fixed at `0` unless the project owner explicitly authorizes a change.
- `B` ranges from `0` to `9`.
- `C` ranges from `0` to `99`.
- Each completed, committable code change increments `C` by one.
- Documentation-only changes do not change the version number.
- After `C` reaches `99`, the next code change resets `C` to `0` and increments `B` by one.
- When the version has reached `0.9.99`, the next code change must not be versioned automatically. Ann must ask the project owner whether `A` should be increased before proceeding.

Examples:

```text
0.0.00 + code change = 0.0.01
0.0.99 + code change = 0.1.00
0.9.99 + code change = project-owner decision required
```

## License

No license has been selected yet.

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

1. **Ann Core module** — The required system module that starts Ann, loads configuration, discovers modules, routes requests, records logs, and applies permission rules.
2. **Other modules** — Add focused features such as commands, integrations, user interfaces, memory, notifications, or scheduled tasks.

Ann Core is itself a required, always-enabled system module. Other modules declare their identity, version, entry point, dependencies, and requested permissions in a manifest file.

## Proposed Project Layout

```text
Ann/
├── launcher.py                   # Stable Core selector and trial launcher
├── Ann_core/                     # Active modular Ann Core
│   ├── main.py
│   ├── src/ann/
│   └── modules/updater/          # Required GitHub update module
├── backup_ann/                   # Staged complete project update; created at runtime
├── modules/
│   ├── registry.json             # Local enabled/disabled module state
│   └── downloaded/               # Downloaded optional modules
├── catalog.json                  # GitHub module and Core catalog
├── README.md                     # This overview
├── VERSION.md                    # Current release information
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

### Current Module Versions

The following table lists every module currently included with Ann. Ann Core and Ann Updater are required system modules; Ann Security Monitor is currently the only optional module.

| Module ID | Module | Version | Type | Default state | Summary |
| --- | --- | --- | --- | --- | --- |
| `ann.core` | Ann Core | 0.0.10 | Required system module | Enabled | Desktop UI, command routing, registry, and module runtime. |
| `ann.updater` | Ann Updater | 0.0.10 | Required system module | Enabled | Checks, verifies, and applies full-project Ann updates. |
| `ann.security-monitor` | Ann Security Monitor | 0.1.1 | Optional module | Enabled | Read-only login-anomaly and packet-metadata monitoring with a local Security Center. |

## Module Catalog and Updates

The canonical Ann repository is intended to be hosted at [zohanlin2-ai/Ann](https://github.com/zohanlin2-ai/Ann).

Ann can use the repository as a module catalog. On request, the core can compare locally installed module versions with the published catalog, report available updates, and let the user choose which optional modules to install or enable. Updates should always be reviewed before installation, especially when a module requests new permissions.

The exact catalog format and update mechanism will be defined with the first working module system. A future catalog should include module version, compatibility information, source location, integrity information, and release notes.

### Version Consistency

Ann Updater reads `catalog.json`, not README, to decide whether an Ann update is available. The `ann_core.version` value in `catalog.json` must match the Ann Core version declared in all of the following places:

- `Ann_core/manifest.json`
- `Ann_core/src/ann/__init__.py`
- `pyproject.toml`
- The Ann Core row in `VERSION.md`

When Ann Core is released, the Ann Updater manifest is bundled with that release and must use the same version. Every optional module must declare its own version in its `manifest.json` and must be listed in the **Current Module Versions** table above. A release must not be published until these values have been checked for consistency.

### Updating `catalog.json`

`catalog.json` is the machine-readable release index used by Ann Updater. It must be updated in the same commit as every Ann Core release, before that commit is pushed to GitHub.

For an Ann Core release:

1. Set `ann_core.version` in `catalog.json` to the new Ann Core version.
2. Keep `ann_core.archive_url` pointed at the GitHub archive for the release branch or tag.
3. Set the same version in `Ann_core/manifest.json`, `Ann_core/modules/updater/manifest.json`, `Ann_core/src/ann/__init__.py`, `pyproject.toml`, and `VERSION.md`.
4. Add the release notes to `CHANGELOG.md`.
5. Commit and push all of these files together.

For example, Ann Core version `0.0.8` requires this catalog entry:

```json
{
  "ann_core": {
    "version": "0.0.8",
    "archive_url": "https://github.com/zohanlin2-ai/Ann/archive/refs/heads/master.zip"
  }
}
```

Ann Updater compares the installed Ann Core version with `ann_core.version`. If the catalog version is not higher, it correctly reports that Ann is already current.

### Adding or Updating a Module

When a module is added or its code changes, update all of the following before publishing the Ann release:

1. Keep the module implementation, `manifest.json`, and detailed module `README.md` in the same module directory.
2. Set the module's own version in its `manifest.json`.
3. Add or update that module in the **Current Module Versions** table in this README.
4. Add a module-specific release note to its README and a project-level note to `CHANGELOG.md`.
5. If the module is distributed through Ann Updater in the future, add its version, archive URL, compatibility requirements, and permissions to `catalog.json`.
6. Commit and push the module code, manifest, README, catalog entry when applicable, and version documentation together.

For example, the current Ann Security Monitor module is maintained in `modules/security_monitor/` with its implementation, `manifest.json`, detailed README, tests, and its own version (`0.1.0`).

## Security Principles

- Modules should have the minimum permissions needed for their purpose.
- Permission requests should be explicit and visible to the user.
- The core should verify compatibility and package integrity before installing updates.
- Module updates should not be applied silently unless the user explicitly enables automatic updates.

## Status

Ann currently includes its first desktop UI milestone: a draggable status bubble with a glowing state ring and a command-only chat window. The Bubble starts in the primary screen's bottom-right corner. Its context menu provides Update, Modules, Security Center (when Security Monitor is enabled), About Ann, and Exit Ann actions. The command core supports module and update commands as well as `exit` / `quit`.

## Requirements and Installation

### Technology and Dependency Record

Ann is currently written in **Python** and uses **PySide6** for its desktop interface. This table is the single human-readable record of the runtime environment. Whenever a dependency changes, this table, `requirements.txt`, and `pyproject.toml` must be updated in the same change.

| Item | Required version | Purpose |
| --- | --- | --- |
| Python | 3.10 or newer | Ann core, module runtime, and launcher |
| PySide6 | 6.8.0.2 | Desktop bubble, status ring, and command window |
| Scapy | 2.6.1 | Security Monitor packet-metadata capture support |

`requirements.txt` and `pyproject.toml` contain the same pinned dependency information in machine-readable form so installation and startup checks can use it reliably.

The root `requirements.txt` includes the bundled Security Monitor dependency file. When you manually run the normal installation command, pip installs Scapy together with Ann's other dependencies. Ann does not download or install Scapy automatically at startup. On Windows, packet capture additionally requires Npcap and an authorised environment that permits capture.

### Windows Development Setup

Use an official Windows CPython installation (Python 3.10 or newer) and create a virtual environment in the project directory. Do not use the MSYS2/MinGW Python for this installation workflow because PyPI does not provide a compatible PySide6 wheel for that platform.

In PowerShell, from the project directory:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launcher.py
```

If the Python Launcher cannot resolve the desired version, replace `py -3.10` in the first command with the full path to an installed CPython executable:

```powershell
& "C:\Path\To\Python\python.exe" -m venv .venv
```

After the environment has been created, start Ann with:

```powershell
.\.venv\Scripts\python.exe launcher.py
```

`Ann_core/main.py` checks required packages and versions before Ann starts. If a package is missing or incompatible, it stops and prints the exact installation command. It does not install packages automatically.

## Development and Distribution

During development, Ann runs in a project-specific Python virtual environment. This keeps the Python interpreter and dependency versions reproducible without changing the system Python installation.

End users will not be expected to install, configure, or manage Python. A future release build will bundle Ann, its Python runtime, and its required dependencies into a native Windows application and installer. The bundled runtime will be controlled by Ann, so it will not depend on or conflict with Python versions already installed on the user's computer.

Modules will declare compatibility with Ann releases rather than relying on the user's system Python version. The exact packaging tool and release workflow will be selected before the first distributable release.

## Updates and Module State

The required **Ann Updater** module uses the configured GitHub catalog to check for and update Ann Core. It is always enabled and is updated together with Ann Core. Downloading optional modules is not supported yet.

For an Ann update, the Updater downloads the complete GitHub project into `backup_ann/` and runs a headless validation of the staged project. If validation succeeds, Ann closes and the stable `launcher.py` automatically applies the update and restarts Ann. The updater preserves `.venv`, `.git`, local module state, and `launcher.py`; replaced managed project files are saved in `rollback_ann/`.

### Update Debug Log

Ann records update diagnostics in `logs/ann-update.log`. This file records the catalog URL and version comparison, archive download size and validation, staged-project verification output, launcher replacement steps, and full error stack traces. Log files rotate automatically at 1 MB and keep three previous files. The `logs/` directory is local diagnostic data and is not committed to Git.

### Module Debug Logs

Every loaded module has an individual debug log at `logs/modules/<module-id>.log`. Ann Core uses `ann.core.log`, Ann Updater uses `ann.updater.log`, and Ann Security Monitor uses `ann.security-monitor.log`. Module logs record startup and module-specific diagnostic events; Ann Updater additionally mirrors its update lifecycle events to `logs/ann-update.log`.

Available chat commands include:

```text
modules list
modules enable <module-id>
modules disable <module-id>
update check
update ann
security open
security status
security alerts
security pause
security resume
security capture start [seconds]
security capture stop
```

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

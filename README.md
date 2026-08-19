# Ann

Ann is a modular AI Assistant designed to stay small at its core and grow through independently managed modules. The core application provides the shared runtime, configuration, module discovery, and capability routing. Modules provide the features.

## Goals

- Keep the default installation simple and focused.
- Add capabilities without changing the core application.
- Let users review and enable or disable modules independently; independent module downloads and updates are planned.
- Keep every module's implementation and detailed documentation together.
- Support a GitHub-based module catalog so Ann can check for available updates and optional features.

## Architecture

Ann has two layers:

1. **Ann Core module** — The required system module that starts Ann, loads configuration, discovers modules, routes requests, records logs, and applies permission rules.
2. **Other modules** — Add focused features such as commands, integrations, user interfaces, memory, notifications, or scheduled tasks.

Ann Core is itself a required, always-enabled system module. Other modules declare their identity, version, entry point, dependencies, and requested permissions in a manifest file.

## Project Layout

```text
Ann/
├── launcher.py                   # Bootstrap, update application, and recovery
├── ann_config.json               # Local catalog and application configuration
├── catalog.json                  # Machine-readable GitHub release catalog
├── requirements.txt              # Pinned runtime dependencies
├── pyproject.toml                # Python package and runtime metadata
├── Ann_core/                     # Required Ann Core system module
│   ├── main.py                   # Core entry point and dependency check
│   ├── manifest.json
│   ├── README.md
│   ├── src/ann/                  # Core runtime and desktop UI
│   └── modules/updater/          # Required Ann Updater system module
│       ├── manifest.json
│       ├── module.py
│       ├── README.md
│       └── UPDATE_VERIFICATION.md
├── modules/
│   ├── registry.json             # Local enabled/disabled module state
│   └── security_monitor/         # Optional Ann Security Monitor module
├── backup_ann/                   # Runtime: verified staged full-project update
├── rollback_ann/                 # Runtime: previous project used for recovery
├── data/                         # Runtime: local module data
├── logs/                         # Runtime: Ann and module diagnostics
├── README.md                     # This overview
├── VERSION.md                    # Current release information
└── CHANGELOG.md                  # Project-level release history
```

`backup_ann/`, `rollback_ann/`, `data/`, and `logs/` are created or maintained at runtime and are not source directories. `modules/downloaded/` is reserved for a future individual-module installer; it is not used by the current full-project updater.

## Modules

Each module must be self-contained in its own directory. Its detailed documentation must live beside its source code, normally in that module's `README.md`.

The project-level README only provides a short catalog entry for each available module. Detailed setup instructions, configuration reference, permissions, examples, compatibility notes, limitations, and troubleshooting belong in the module directory.

A module manifest must always describe its stable identifier, display name, version, entry point, and default enabled state. It must also describe the following when they apply to the module:

- A stable module identifier and display name
- Version and Ann Core compatibility requirements, when applicable
- Entry point
- Dependencies
- Requested permissions, such as network or file-system access
- Optional configuration schema

## Module Development Contract

This section defines the minimum development and release contract for every Ann module. A module's own README contains its feature-specific details; it does not replace the project rules below.

Before creating or changing a module, read these root README sections:

- **Modules** for structure and documentation placement.
- **Module Development Contract** for required development and release behaviour.
- **Version and Release Management** for independent versions, catalog maintenance, and release records.
- **Security Principles** for permissions and safety boundaries.
- **Technology and Dependency Record** when adding or changing dependencies.
- **Updates and Module State** for how catalog-managed modules are delivered and recovered.

Every module must:

1. Keep its implementation, `manifest.json`, and detailed `README.md` in one module directory.
2. Use a stable lowercase module ID and declare its entry point, version, and default-enabled state in `manifest.json`; declare dependencies, permissions, compatibility requirements, and configuration when applicable.
3. Keep its version independent from Ann Core and other modules; increment only when that module's code changes.
4. Record module-specific diagnostics in `logs/modules/<module-id>.log` when it performs runtime work.
5. Store user data only in its approved local data location and never modify Ann Core or another module's files.
6. Follow the module release checklist in **Adding or Updating a Module** before publishing.

Before release, test the module enabled and disabled, check missing-dependency handling, verify its permissions, and verify its catalog/update behaviour when it is catalog-managed.

### Module Startup and Failure Contract

Every module must implement a clear lifecycle:

```text
Disabled → Starting → Ready → Stopped
                   ↘ Degraded
                   ↘ Failed
```

New modules must expose the following lifecycle methods, either directly on the created module object or through Ann's supported module adapter:

```text
validate(context)     → ModuleResult
start(context)        → ModuleResult
health_check(context) → ModuleResult
stop(context)         → ModuleResult
```

`ModuleResult` must report a `Ready`, `Stopped`, `Degraded`, or `Failed` state, a user-readable message, technical details for logs, and whether retry is safe. Ann Core's Module Runtime owns the shared response: it stores each module's runtime state, exposes that state to the user, skips commands and UI for modules that are not running, and provides generic start, stop, restart, and retry operations. Launcher only waits for Ann Core readiness; it never manages individual modules.

For a running module, Ann Core provides `modules stop <module-id>` and `modules restart <module-id>`. Restart always performs `stop()` followed by `validate()` and `start()` through the module's start path. A stopped, enabled module can be started with `modules start <module-id>`. Stopping a module is immediate for the current Ann session and does not change its **Enabled** preference; disabling it controls whether it starts automatically next time Ann starts. When Ann exits, Core calls `stop()` for every running module that supports controlled stopping. Ann Core itself cannot be stopped independently; exit Ann to stop it.

Before reporting `Ready`, a module must validate its configuration, required files, permissions, and dependencies; start its runtime work; register its commands or UI; and write a successful startup record to its module log. A module may report `Degraded` when an optional sub-feature is unavailable but its remaining features can continue safely.

When startup fails, the module must record a clear error and stack trace in `logs/modules/<module-id>.log`, report a user-readable reason, stop only its own runtime work, and provide a safe retry or restart path. It must not crash Ann Core or disable unrelated modules. A failed optional module remains enabled in the user's saved Module List preference, but is unavailable for the current session until it is retried or Ann restarts.

Ann Core is the exception: a Core startup failure prevents Ann from starting. If the failure occurs before Core reports `Ready` after an update, the launcher recovery process handles rollback. A required system module such as Ann Updater should leave Ann running but mark only its own functionality unavailable. An optional module may degrade a sub-feature instead of failing completely when that is safe.

New modules must implement this lifecycle contract. Existing legacy modules remain loadable through Ann Core's compatibility adapter while they are migrated. Ann Security Monitor is currently such a legacy module; it remains supported but is not the implementation example for new modules.

Each module README must include a **Startup and Failure Handling** section covering its preconditions, successful startup behaviour, health checks, failure behaviour, recovery or retry procedure, and log location. Each module must test normal startup, an injected or simulated startup failure, missing dependencies or invalid configuration, failure isolation from Ann and other modules, and successful recovery after retry or restart.

## Launcher Startup and Recovery Contract

`launcher.py` is Ann's bootstrap and recovery component, not a module. It is not listed in Module List and has no enabled or disabled state, but it must follow the startup and failure-handling rules below.

The launcher lifecycle is:

```text
Validating → Starting Core → Waiting for Ready → Ready
                                      ↘ Startup Failed
```

Before starting Ann Core, the launcher must validate the active Core path and any pending update state. After starting Core, it must wait for an explicit `Ready` signal from Core. A non-zero Core exit before that signal is a startup failure. When this happens immediately after a verified update, the launcher must restore `rollback_ann/` once and start the previous Core. A failed restored Core must stop recovery rather than enter a retry loop.

After Core reports `Ready`, the launcher must treat later non-zero exits as runtime failures: record them in `logs/ann-update.log`, but do not automatically roll back a successfully started update. The launcher must record validation, Core start, Ready confirmation, startup failure, rollback, restored-Core result, and unexpected runtime exit events in that log.

Launcher tests must cover normal Core readiness, Core failure before readiness, one-time rollback success, rollback failure without looping, and a non-zero exit after readiness without rollback.

### Current Modules

The following table provides a short catalog of every module currently included with Ann. Ann Core and Ann Updater are required system modules; Ann Security Monitor is currently the only optional module. Current module versions and latest modification logs are recorded only in [VERSION.md](VERSION.md).

| Module ID | Module | Type | Default state | Summary |
| --- | --- | --- | --- | --- |
| `ann.core` | Ann Core | Required system module | Enabled | Desktop UI, command routing, registry, module runtime, and update recovery. |
| `ann.updater` | Ann Updater | Required system module | Enabled | Checks, verifies, and applies full-project Ann updates. |
| `ann.security-monitor` | Ann Security Monitor | Optional legacy module | Enabled | Read-only login-anomaly and packet-metadata monitoring with a local Security Center; lifecycle migration is planned. |

## Version and Release Management

The canonical Ann repository is intended to be hosted at [zohanlin2-ai/Ann](https://github.com/zohanlin2-ai/Ann).

Ann uses the repository as a module catalog. The core compares locally installed catalog-managed module versions with the published catalog and reports available Ann updates. Users can enable or disable already installed optional modules. Downloading individual optional modules is not supported yet.

The catalog records each managed module's ID, display name, version, and manifest location. Future catalog fields may add compatibility information, source locations for independently distributed modules, integrity information, and release notes.

This chapter is the authoritative process for releasing Ann and its modules. Every new module must keep its detailed README beside its code and follow the version, catalog, and documentation rules in this chapter before it is released.

### Version Number Rules

Each independently versioned component uses the format `A.B.C`. Ann Core, Ann Updater, and every optional module own their own version sequence.

- `A` is fixed at `0` unless the project owner explicitly authorizes a change.
- `B` ranges from `0` to `9`.
- `C` ranges from `0` to `99`.
- A completed, committable code change increments `C` only for the component whose code changed.
- Documentation-only changes do not change any component version.
- After `C` reaches `99`, the next code change resets `C` to `0` and increments `B` by one.
- When the version has reached `0.9.99`, the next code change must not be versioned automatically. Ann must ask the project owner whether `A` should be increased before proceeding.

Examples:

```text
0.0.0 + code change = 0.0.1
0.0.99 + code change = 0.1.0
0.9.99 + code change = project-owner decision required
```

### `VERSION.md` Document Rules

`VERSION.md` is the single current-version reference for Ann. It must list Ann Core and every module currently included with Ann, with each module's current version. It must also retain the latest modification log for each listed module. Earlier version notes and the complete chronological project history belong in `CHANGELOG.md`. Ann `0.0.13` is the migration baseline for independent module versions; it does not imply that every module received a feature change in that release.

### Version Consistency

Ann Updater reads `catalog.json`, not README, to decide whether an Ann update is available. Every catalog entry must match its own component manifest and row in `VERSION.md`. Specifically, the `ann_core.version` value in `catalog.json` must match the Ann Core version declared in all of the following places:

- `Ann_core/manifest.json`
- `Ann_core/src/ann/__init__.py`
- `pyproject.toml`
- The Ann Core row in `VERSION.md`

Every catalog-managed module must declare its own version in `manifest.json` and must be listed in `VERSION.md`. Each catalog entry must match that module's manifest ID and version. A release must not be published until these values have been checked for consistency. Ann Core changes do not require version changes to Ann Updater or optional modules unless their own code changes.

### Updating `catalog.json`

`catalog.json` is the machine-readable release index used by Ann Updater. It must be updated in the same commit as every changed catalog-managed component, before that commit is pushed to GitHub.

For an Ann Core release:

1. Set `ann_core.version` in `catalog.json` to the new Ann Core version.
2. Keep `ann_core.archive_url` pointed at the GitHub archive for the release branch or tag.
3. Set the same Core version in `Ann_core/manifest.json`, `Ann_core/src/ann/__init__.py`, `pyproject.toml`, and the Ann Core row in `VERSION.md`.
4. Do not change another module's version unless that module's code also changed.
5. Add the release notes to `CHANGELOG.md`.
6. Commit and push all of these files together.

For example, Ann Core version `0.0.8` requires this catalog entry:

```json
{
  "ann_core": {
    "version": "0.0.8",
    "archive_url": "https://github.com/zohanlin2-ai/Ann/archive/refs/heads/master.zip"
  }
}
```

Ann Updater compares every catalog-managed module with its catalog version. If any listed version differs, Ann requires a complete project update; Ann is current only when every listed version matches exactly. Local custom modules that are not listed in `catalog.json` are not overwritten automatically.

Each `modules` entry in `catalog.json` must include the module ID, display name, version, and path to that module's manifest. The staged-project verifier checks that every catalog entry matches its manifest before Ann applies the update.

### Adding or Updating a Module

When a module is added or its code changes, first read and follow the **Module Development Contract** and this **Version and Release Management** chapter. Then update all of the following before publishing that module:

1. Keep the module implementation, `manifest.json`, and detailed module `README.md` in the same module directory.
2. Increment and set only that module's own version in its `manifest.json`.
3. Add the module to the **Current Modules** table in this README when it is newly included with Ann; do not add versions to that table.
4. Record the module's latest modification log in `VERSION.md`, add a module-specific release note to its README, and add a project-level note to `CHANGELOG.md`.
5. If the module is part of an Ann release, add its ID, display name, version, and manifest path to `catalog.json` so Ann Updater can verify it. Add archive URLs, compatibility requirements, and permissions when the module is independently distributed in the future.
6. Commit and push the module code, manifest, README when it is newly included, catalog entry when applicable, and version documentation together.

For example, the current Ann Security Monitor module is maintained in `modules/security_monitor/` with its implementation, `manifest.json`, detailed README, tests, and its current module version (`0.0.13`).

## Security Principles

- Modules should have the minimum permissions needed for their purpose.
- Permission requests should be explicit and visible to the user.
- The core should verify compatibility and package integrity before installing updates.
- Module updates should not be applied silently unless the user explicitly enables automatic updates.

## Status

Ann currently includes its first desktop UI milestone: a draggable status bubble with a glowing state ring and a command-only chat window. The Bubble starts in the primary screen's bottom-right corner. Its context menu provides Update, Modules, Security Center, About Ann, and Exit Ann actions. Security Center reports when Security Monitor is disabled or unavailable. The command core supports module and update commands as well as `exit` / `quit`.

## Requirements and Installation

### Technology and Dependency Record

Ann is currently written in **Python** and uses **PySide6** for its desktop interface. This table is the single human-readable record of the runtime environment. Whenever a dependency changes, this table, `requirements.txt`, and `pyproject.toml` must be updated in the same change.

| Item | Required version | Purpose |
| --- | --- | --- |
| Python | >=3.10, <3.13 | Ann core, module runtime, and launcher; required by the pinned PySide6 release |
| PySide6 | 6.8.0.2 | Desktop bubble, status ring, and command window |
| Scapy | 2.6.1 | Security Monitor packet-metadata capture support |

`requirements.txt` and `pyproject.toml` contain the same pinned dependency information in machine-readable form so installation and startup checks can use it reliably.

The root `requirements.txt` includes the bundled Security Monitor dependency file. When you manually run the normal installation command, pip installs Scapy together with Ann's other dependencies. Ann does not download or install Scapy automatically at startup. On Windows, packet capture additionally requires Npcap and an authorised environment that permits capture.

### Windows Development Setup

Use an official Windows CPython installation from Python 3.10 through 3.12 and create a virtual environment in the project directory. Python 3.13 is not supported by the pinned `PySide6==6.8.0.2` release. Do not use the MSYS2/MinGW Python for this installation workflow because PyPI does not provide a compatible PySide6 wheel for that platform.

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

The required **Ann Updater** module uses the configured GitHub catalog to check for and update the complete Ann project. It is always enabled. It is delivered with a full Ann update, but its version changes independently from Ann Core. Downloading optional modules is not supported yet.

For an Ann update, the Updater downloads the complete GitHub project into `backup_ann/` and runs a headless validation of the staged project. If validation succeeds, Ann closes and `launcher.py` automatically applies the update and restarts Ann. The updater preserves `.venv`, `.git`, and local module state; it also updates `launcher.py` as part of the managed project. Replaced managed project files are saved in `rollback_ann/`.

The complete staged verification, failure handling, rollback, diagnostics, and test checklist are documented in [Update Verification and Recovery](Ann_core/modules/updater/UPDATE_VERIFICATION.md).

If the updated Ann Core exits with a non-zero status before it reports `Ready`, the launcher automatically restores the managed project files from `rollback_ann/` and starts the previous version once. A non-zero exit after `Ready` is recorded as a runtime failure without rollback. The recovery state prevents repeated automatic rollback attempts. If the restored Core also fails before `Ready`, Ann stops and the update logs retain the diagnostic details.

### Launcher Migration

Ann `0.0.13` and later update `launcher.py` together with the rest of the managed project, so future launcher recovery improvements are delivered through Ann updates. Installations that first used Ann before `0.0.13` must manually sync the project once (for example, run `git pull` in the project directory) to receive the new launcher; earlier launchers intentionally preserved themselves during updates.

### Update Debug Log

Ann records update diagnostics in `logs/ann-update.log`. This file records the catalog URL and version comparison, archive download size and validation, staged-project verification output, launcher replacement steps, and full error stack traces. Log files rotate automatically at 1 MB and keep three previous files. The `logs/` directory is local diagnostic data and is not committed to Git.

### Module Debug Logs

Every loaded module has an individual debug log at `logs/modules/<module-id>.log`. Ann Core uses `ann.core.log`, Ann Updater uses `ann.updater.log`, and Ann Security Monitor uses `ann.security-monitor.log`. Module logs record startup and module-specific diagnostic events; Ann Updater additionally mirrors its update lifecycle events to `logs/ann-update.log`.

Available chat commands include:

```text
modules list
modules status
modules retry <module-id>
modules start <module-id>
modules stop <module-id>
modules restart <module-id>
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

## License

No license has been selected yet.

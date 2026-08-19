# Ann Core

Ann Core is Ann's required system module. It provides the desktop Bubble and chat UI, command routing, the Module Registry, and the runtime that loads other modules.

Ann Core is always enabled and cannot be disabled from Module List. The Ann Updater downloads a complete newer Ann project into `backup_ann/`, validates it without opening the normal UI, then requests a restart. `launcher.py` applies the verified project update while preserving local user data and is updated as part of the project. If the updated Core exits with an error before reporting `Ready`, the launcher restores `rollback_ann/` once and starts the previous Core. A non-zero exit after `Ready` is logged as a runtime failure and does not trigger rollback.

Ann Core writes its module log to `logs/modules/ann.core.log`. Update diagnostics are also written to `logs/ann-update.log`. Logs rotate automatically when they reach 1 MB and retain three older log files.

## Included Components

- `main.py` — Core entry point and dependency check.
- `src/ann/` — Core runtime and UI source code.
- `modules/updater/` — Required GitHub updater system module.

## Release History

### 0.0.18

- Bind each update request to the parent Launcher session instead of a Windows redirector-sensitive process ID.

### 0.0.17

- Apply verified updates from the parent Launcher and hand off to a new Launcher only when it changed.
- Restore the complete managed project once if updated Core fails before Ready.

### 0.0.16

- Add shared immediate module start, stop, and restart operations with runtime status reporting.
- Stop supported modules safely when Ann exits; retain each module's saved enabled preference.

### 0.0.13

- Include the launcher in full-project updates so automatic recovery is delivered to future installations.

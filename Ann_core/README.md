# Ann Core

Ann Core is Ann's required system module. It provides the desktop Bubble and chat UI, command routing, the Module Registry, and the runtime that loads other modules.

Ann Core is always enabled and cannot be disabled from Module List. The Ann Updater downloads a complete newer Ann project into `backup_ann/`, validates it without opening the normal UI, then requests a restart. The stable `launcher.py` applies the verified project update while preserving local user data. If the updated Core exits with an error, the launcher restores `rollback_ann/` once and starts the previous Core.

Ann Core writes its module log to `logs/modules/ann.core.log`. Update diagnostics are also written to `logs/ann-update.log`. Logs rotate automatically when they reach 1 MB and retain three older log files.

## Included Components

- `main.py` — Core entry point and dependency check.
- `src/ann/` — Core runtime and UI source code.
- `modules/updater/` — Required GitHub updater system module.

## Release History

### 0.0.12

- Add automatic one-time recovery from an updated Core startup failure.

# Ann Core

Ann Core is Ann's required system module. It provides the desktop Bubble and chat UI, command routing, the Module Registry, and the runtime that loads other modules.

Ann Core is always enabled and cannot be disabled from Module List. The Ann Updater downloads a newer Core into `backup_ann/`; `launcher.py` verifies it on the next start before promoting it to this `Ann_core/` directory.

## Included Components

- `main.py` — Core entry point and dependency check.
- `src/ann/` — Core runtime and UI source code.
- `modules/updater/` — Required GitHub updater system module.

# Ann Updater

Ann Updater is Ann's required system module. It is enabled by default and cannot be disabled.

It reads the GitHub catalog configured in the project root and stages a complete newer Ann project in `backup_ann/`. Ann Updater is bundled with Ann Core and is updated together with it. Downloading optional modules is not supported yet.

## Core Update Flow

1. `update ann` downloads the complete GitHub project into `backup_ann/`.
2. The staged project runs `Ann_core/main.py --verify-update` without opening the normal UI.
3. If validation succeeds, Ann closes and `launcher.py` automatically applies the staged project.
4. The launcher preserves `.venv`, `.git`, `modules/registry.json`, downloaded modules, and itself; it saves replaced project files in `rollback_ann/`.

## Commands

- `update check`
- `update ann`

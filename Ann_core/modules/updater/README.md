# Ann Updater

Ann Updater is Ann's required system module. It is enabled by default and cannot be disabled.

It reads the GitHub catalog configured in the project root and stages a complete newer Ann project in `backup_ann/`. Ann Updater is bundled with Ann Core and is updated together with it. Downloading optional modules is not supported yet.

`catalog.json` lists every catalog-managed module and its expected version. Ann Updater stages a complete project update whenever any listed installed module version differs from the catalog.

## Core Update Flow

1. `update ann` downloads the complete GitHub project into `backup_ann/`.
2. The staged project runs `Ann_core/main.py --verify-update` without opening the normal UI.
3. If validation succeeds, Ann closes and `launcher.py` automatically applies the staged project.
4. The launcher preserves `.venv`, `.git`, `modules/registry.json`, and downloaded modules; it updates itself with the project and saves replaced project files in `rollback_ann/`.
5. If the updated Core exits with an error, the launcher restores `rollback_ann/` once and starts the previous version. If that version also fails, it stops and records the failure.

Installations created before Ann `0.0.13` need a one-time manual project sync to receive the self-updating launcher, because earlier launchers preserved themselves during updates.

## Debug Log

Ann Updater writes its own module log to `logs/modules/ann.updater.log` and mirrors update diagnostics to `logs/ann-update.log`. When an update fails or appears stuck, inspect either log for the catalog URL, version comparison, download result, verification output, launcher activity, and any error stack trace.

## Commands

- `update check`
- `update ann`

## Release History

### 0.0.13

- Include `launcher.py` in the full-project update and rollback transaction.

# Ann Updater

Ann Updater is Ann's required system module. It is enabled by default and cannot be disabled, but Ann Core may temporarily stop and restart it during the current session. Its version evolves independently from Ann Core and optional modules.

It reads the GitHub catalog configured in the project root and stages a complete newer Ann project in `backup_ann/`. Ann Updater is delivered inside a complete Ann update, while retaining its own independent version. Downloading optional modules is not supported yet.

`catalog.json` lists every catalog-managed module and its expected version. Ann Updater stages a complete project update whenever any listed installed module version differs from the catalog.

## Core Update Flow

1. `update ann` downloads the complete GitHub project into `backup_ann/`.
2. The staged project runs `Ann_core/main.py --verify-update` without opening the normal UI.
3. If validation succeeds, Ann closes and `launcher.py` automatically applies the staged project.
4. The launcher preserves `.venv`, `.git`, `modules/registry.json`, and downloaded modules; it updates itself with the project and saves replaced project files in `rollback_ann/`.
5. If the updated Core exits with an error before reporting `Ready`, the launcher restores `rollback_ann/` once and starts the previous version. A failure after `Ready` is logged without rollback. If the restored Core also fails before `Ready`, it stops and records the failure.

Installations created before Ann `0.0.13` need a one-time manual project sync to receive the self-updating launcher, because earlier launchers preserved themselves during updates.

## Debug Log

Ann Updater writes its own module log to `logs/modules/ann.updater.log` and mirrors update diagnostics to `logs/ann-update.log`. When an update fails or appears stuck, inspect either log for the catalog URL, version comparison, download result, verification output, launcher activity, and any error stack trace.

## Verification and Recovery

See [Update Verification and Recovery](UPDATE_VERIFICATION.md) for the staged verification contract, failure paths, rollback behaviour, diagnostic locations, and release test checklist.

## Startup and Failure Handling

Ann Core calls `validate()` before `start()`. Validation checks that `ann_config.json` is readable and defines `catalog_url`; a failure marks only Ann Updater unavailable, leaving Ann Core and unrelated modules running. `start()` then records that the already validated Updater is ready. `health_check()` repeats validation, while `stop()` ends the module's current runtime state without changing its required enabled preference. Ann Core can use its generic start, stop, restart, and retry operations for the Updater. Validation failures and lifecycle events are recorded in `logs/modules/ann.updater.log`.

## Commands

- `update check`
- `update ann`

## Release History

### 0.0.15

- Separate validation from startup so the common Ann Core lifecycle is executed exactly once.

### 0.0.13

- Establish the independent-module-version migration baseline; no separate Updater feature change was made in this release.

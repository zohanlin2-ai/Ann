# Ann Updater

Ann Updater is Ann's required system module. It is enabled by default and cannot be disabled.

It reads the GitHub catalog configured in the project root, downloads new modules or module updates, and stages a newer Ann Core in `backup_ann/`. Ann does not use a downloaded module until the Ann Core enables it through the Module List.

## Core Update Flow

1. `update ann` downloads and validates a newer Core into `backup_ann/`.
2. On the next launch, `launcher.py` starts `backup_ann/` as a trial Core.
3. After the trial Core reports a healthy UI startup, the launcher promotes it to `Ann_core/` and retains the previous Core in `rollback_ann/`.

## Commands

- `update list`
- `update check`
- `update install <module-id>`
- `update apply <module-id>`
- `update ann`

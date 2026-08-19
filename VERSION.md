# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.20 | Validated cross-platform Launcher integrity and update handoff |
| Ann Updater | 0.0.18 | Catalog-backed Launcher update detection |
| Ann Security Monitor | 0.0.14 | Controlled lifecycle and isolated packet-capture failures |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Latest Module Change Logs

Only the latest modification log for each current module is retained here. See `CHANGELOG.md` for the complete chronological project history and each module's README for its detailed module history.

### Ann Core — 0.0.20

- Validate the staged Launcher's catalog SHA-256 before applying an update.
- Compare Launcher content using normalized line endings so Git's Windows checkout mode does not cause a false Launcher replacement.

### Ann Updater — 0.0.18

- Compare the local Launcher SHA-256 with the catalog and show its update status in `update check`.

### Ann Security Monitor — 0.0.14

- Migrate to the controlled module lifecycle with validation, health checks,
  idempotent stopping, and safe retry or restart recovery.
- Keep runtime packet-capture failures isolated from local login monitoring.

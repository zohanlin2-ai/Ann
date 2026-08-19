# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.14 | Ready handshake and startup-only update rollback |
| Ann Updater | 0.0.14 | Startup validation with unavailable-state isolation |
| Ann Security Monitor | 0.0.13 | Catalog-managed module with an independent version sequence |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Latest Module Change Logs

Only the latest modification log for each current module is retained here. See `CHANGELOG.md` for the complete chronological project history and each module's README for its detailed module history.

### Ann Core — 0.0.14

- Add a launcher/Core Ready handshake so rollback applies only to startup failures.
- Add shared module runtime states and generic module status and retry handling.

### Ann Updater — 0.0.14

- Add startup validation and lifecycle results so an unavailable Updater does not stop Ann Core.

### Ann Security Monitor — 0.0.13

- Establish the independent-module-version migration baseline; no separate Security Monitor feature change was made in this release.

# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.13 | Self-updating launcher with automatic rollback after a failed update |
| Ann Updater | 0.0.13 | Required system module with an independent version sequence |
| Ann Security Monitor | 0.0.13 | Catalog-managed module with an independent version sequence |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Latest Module Change Logs

Only the latest modification log for each current module is retained here. See `CHANGELOG.md` for the complete chronological project history and each module's README for its detailed module history.

### Ann Core — 0.0.13

- Update the stable launcher together with the Ann project so future recovery logic is delivered by Ann updates.
- Restore the pre-update project automatically when the updated Core exits with an error after installation.

### Ann Updater — 0.0.13

- Establish the independent-module-version migration baseline; no separate Updater feature change was made in this release.

### Ann Security Monitor — 0.0.13

- Establish the independent-module-version migration baseline; no separate Security Monitor feature change was made in this release.

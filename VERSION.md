# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.12 | Automatic rollback after an updated Core fails to start |
| Ann Updater | 0.0.12 | Required system module, bundled with Ann Core |
| Ann Security Monitor | 0.0.12 | Catalog-managed module included with this release |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Latest Module Change Logs

Only the latest modification log for each current module is retained here. See `CHANGELOG.md` for the complete chronological project history and each module's README for its detailed module history.

### Ann Core — 0.0.12

- Restore the pre-update project automatically when the updated Core exits with an error after installation.
- Limit automatic recovery to one rollback attempt and preserve local module data.

### Ann Updater — 0.0.12

- Use the stable launcher recovery path after a verified complete-project update.

### Ann Security Monitor — 0.0.12

- Align the module with the catalog-managed Ann `0.0.12` release.

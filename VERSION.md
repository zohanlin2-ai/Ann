# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.13 | Self-updating launcher with automatic rollback after a failed update |
| Ann Updater | 0.0.13 | Required system module, bundled with Ann Core |
| Ann Security Monitor | 0.0.13 | Catalog-managed module included with this release |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Latest Module Change Logs

Only the latest modification log for each current module is retained here. See `CHANGELOG.md` for the complete chronological project history and each module's README for its detailed module history.

### Ann Core — 0.0.13

- Update the stable launcher together with the Ann project so future recovery logic is delivered by Ann updates.
- Restore the pre-update project automatically when the updated Core exits with an error after installation.

### Ann Updater — 0.0.13

- Include the launcher in full-project update and rollback transactions.

### Ann Security Monitor — 0.0.13

- Align the module with the catalog-managed Ann `0.0.13` release.

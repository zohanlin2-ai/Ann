# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.11 | Catalog-managed full-module version checks |
| Ann Updater | 0.0.11 | Required system module, bundled with Ann Core |
| Ann Security Monitor | 0.0.11 | Catalog-managed module included with this release |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Latest Module Change Logs

Only the latest modification log for each current module is retained here. See `CHANGELOG.md` for the complete chronological project history and each module's README for its detailed module history.

### Ann Core — 0.0.11

- List every catalog-managed module and its latest version in `catalog.json`.
- Require a full Ann update whenever any catalog-managed module version differs.

### Ann Updater — 0.0.11

- Compare every catalog-managed module version exactly and stage a full Ann update when any version differs.

### Ann Security Monitor — 0.0.11

- Align the module with the catalog-managed Ann `0.0.11` release.
- Add a dedicated module debug log.

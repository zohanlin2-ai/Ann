# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.11 | Catalog-managed full-module version checks |
| Ann Updater | 0.0.11 | Required system module, bundled with Ann Core |
| Ann Security Monitor | 0.1.1 | Optional module included with this release |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Version History

Only the latest Ann Core release is summarized here. See `CHANGELOG.md` for the complete release history.

### 0.0.11

- List every catalog-managed module and its latest version in `catalog.json`.
- Require a full Ann update whenever any catalog-managed module version differs.

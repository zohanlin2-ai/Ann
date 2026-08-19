# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.16 | Generic module start, stop, and restart lifecycle operations |
| Ann Updater | 0.0.15 | Lifecycle-compatible validation and start separation |
| Ann Security Monitor | 0.0.14 | Controlled lifecycle and isolated packet-capture failures |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Latest Module Change Logs

Only the latest modification log for each current module is retained here. See `CHANGELOG.md` for the complete chronological project history and each module's README for its detailed module history.

### Ann Core — 0.0.16

- Add immediate start, stop, and restart actions for modules with runtime state reporting.
- Stop supported running modules during Ann shutdown without changing their enabled preference.

### Ann Updater — 0.0.15

- Separate validation from startup so Ann Core can consistently run `validate()` before `start()`.

### Ann Security Monitor — 0.0.14

- Migrate to the controlled module lifecycle with validation, health checks,
  idempotent stopping, and safe retry or restart recovery.
- Keep runtime packet-capture failures isolated from local login monitoring.

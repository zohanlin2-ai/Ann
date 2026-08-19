# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.18 | Session-bound parent-launcher update handoff |
| Ann Updater | 0.0.17 | Session-bound verified update requests |
| Ann Security Monitor | 0.0.14 | Controlled lifecycle and isolated packet-capture failures |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Latest Module Change Logs

Only the latest modification log for each current module is retained here. See `CHANGELOG.md` for the complete chronological project history and each module's README for its detailed module history.

### Ann Core — 0.0.18

- Use a Launcher-provided session ID to associate the verified update request with the correct Core process on Windows.

### Ann Updater — 0.0.17

- Record the parent Launcher session ID in the verified update request instead of comparing redirector-sensitive process IDs.

### Ann Security Monitor — 0.0.14

- Migrate to the controlled module lifecycle with validation, health checks,
  idempotent stopping, and safe retry or restart recovery.
- Keep runtime packet-capture failures isolated from local login monitoring.

# Ann Version Information

## Current Release

| Component | Version | Notes |
| --- | --- | --- |
| Ann Core | 0.0.17 | Parent-launcher update handoff and complete rollback transaction |
| Ann Updater | 0.0.16 | Verified update requests without a child helper process |
| Ann Security Monitor | 0.0.14 | Controlled lifecycle and isolated packet-capture failures |
| Python | >=3.10 | Development runtime |
| PySide6 | 6.8.0.2 | Desktop UI framework |
| Module Catalog Schema | 1 | GitHub catalog format |

## Latest Module Change Logs

Only the latest modification log for each current module is retained here. See `CHANGELOG.md` for the complete chronological project history and each module's README for its detailed module history.

### Ann Core — 0.0.17

- Apply updates from the parent Launcher, re-exec an updated Launcher, and retain staging until Core reports Ready.
- Restore the full managed project once when updated Core fails before Ready.

### Ann Updater — 0.0.16

- Write an atomic verified-update request for the parent Launcher instead of spawning a waiting helper process.

### Ann Security Monitor — 0.0.14

- Migrate to the controlled module lifecycle with validation, health checks,
  idempotent stopping, and safe retry or restart recovery.
- Keep runtime packet-capture failures isolated from local login monitoring.

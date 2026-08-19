# Ann Security Monitor

Ann Security Monitor is a local, read-only monitoring module. It detects suspicious
login patterns and can, after an explicit user action, observe network packet
metadata for simple scan patterns.

## Privacy and safety boundaries

- Network capture is off by default.
- No packet payload is retained, displayed, decrypted, forwarded, blocked, or altered.
- Login events and alerts remain in `data/security_monitor/` under the Ann project.
- The module never disables accounts, revokes sessions, or changes firewall rules.
- Live capture requires an authorised environment. On Windows it generally requires
  Npcap and administrator permissions.

The normal root installation command installs Scapy because the root requirements
file includes this module's requirements. Ann does not install Scapy automatically
when it starts. If you are updating an existing environment manually, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Commands

- `security open`
- `security status`
- `security alerts`
- `security pause` / `security resume`
- `security capture start [seconds]`
- `security capture stop`

## Data retention

The default retention period is 30 days. Change it in Security Center → Privacy & Data.

## Debug Log

Security Monitor writes diagnostic events to `logs/modules/ann.security-monitor.log`. The log records module startup, commands, pause/resume actions, and generated alerts. It rotates automatically when it reaches 1 MB and retains three older log files.

## Startup and Failure Handling

Security Monitor follows Ann's controlled module lifecycle: `validate()`,
`start()`, `health_check()`, and `stop()`. Its complete verification and recovery
procedure is in [STARTUP_VERIFICATION.md](STARTUP_VERIFICATION.md).

Before startup, the module requires a usable Ann project data location and a valid
existing `data/security_monitor/settings.json` file, if that file already exists.
At startup it creates or opens only its local SQLite database and settings, verifies
that local storage is usable, and records a successful startup in its module log.
It does not begin network capture automatically.

If validation or startup fails, Security Monitor records the failure and traceback in
`logs/modules/ann.security-monitor.log`, stops only resources it created, and reports
the module as unavailable. Ann Core and unrelated modules continue running. After the
underlying data-path or settings problem is corrected, use `modules retry
ann.security-monitor` or `modules restart ann.security-monitor` to recover.

Stopping the module stops any active capture and prevents later callbacks from storing
events. It does not change the saved Enabled preference. Session pause is different:
`security pause` stops monitoring only until the current Ann process exits, and the
next Ann launch starts the enabled module normally.

Scapy is installed by the normal root dependency installation. Npcap, a capture-capable
interface, and authorisation to capture are runtime requirements only when the user
explicitly starts packet-metadata capture. If that optional capture action fails, the
module remains available for local login monitoring and reports the actionable error
in the Security Center, chat response, and module log.

## Session pause

The Security Center's **Pause monitoring** control and `security pause` stop
monitoring only for the current Ann process. Ann automatically resumes the module
when it is launched again. Packet capture always remains explicitly started and
time-bounded.

## Module Versioning Rules

Security Monitor follows Ann's root [Version and Release Management](../../README.md#version-and-release-management) chapter.
It is a catalog-managed module with its own independent version sequence. Its
version changes only when Security Monitor code changes; an Ann Core release does
not by itself change this module's version.

- Every completed, committable Security Monitor code change increments Security
  Monitor's own version under the root `A.B.C` rules.
- Documentation-only changes do not change the module version.
- For a module release, update `manifest.json`, this README's Release History,
  `VERSION.md`, `catalog.json`, and add a project-level release note to
  `CHANGELOG.md` in the same commit. Update the root README only when the module
  is newly included or its summary changes.
- At `0.9.99`, do not automatically create the next release version; ask the
  project owner whether the major component may increase.

## Release History

### 0.0.14

- Migrate Security Monitor from the legacy compatibility path to Ann's controlled
  lifecycle, including validation, start, health checks, stop, and safe recovery.
- Prevent post-stop capture callbacks from recording data and keep packet-capture
  failures isolated from login monitoring.

### 0.0.13

- Establish the independent-module-version migration baseline; no separate
  Security Monitor feature change was made in this release.

### 0.0.11

- Align the module version with the catalog-managed Ann `0.0.11` release.
- Add the Security Monitor module debug log.

### 0.0.6

- Initial Security Monitor release with local alert storage, Security Center settings,
  session-only pause/resume controls, login anomaly rules, and optional time-bounded
  packet-metadata capture.

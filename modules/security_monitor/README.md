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

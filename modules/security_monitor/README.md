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

Security Monitor follows Ann's root [versioning rules](../../README.md#versioning-rules)
and uses the `A.B.C` format. `A` remains `0` unless the project owner authorises a
change; `B` ranges from `0` to `9`; and `C` ranges from `0` to `99`.

- Every completed, committable Security Monitor code change increments the module's
  `C` version by one. After `C` reaches `99`, the next code change resets `C` to
  `0` and increments `B` by one.
- Documentation-only changes do not change the module version.
- For a module release, update `manifest.json`, this README's Release History, the
  **Current Module Versions** table in the root README, and add a project-level
  release note to `CHANGELOG.md` in the same commit.
- Only when Ann Updater supports distributing Security Monitor must its version,
  archive URL, compatibility requirements, and permissions also be added to
  `catalog.json`.
- At `0.9.99`, do not automatically create the next module version; ask the project
  owner whether the major component may increase.

## Release History

### 0.1.1

- Add the Security Monitor module debug log.

### 0.1.0

- Initial Security Monitor release with local alert storage, Security Center settings,
  session-only pause/resume controls, login anomaly rules, and optional time-bounded
  packet-metadata capture.

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

To enable the optional capture integration in an existing Ann environment, install
Scapy separately:

```powershell
.\.venv\Scripts\python.exe -m pip install scapy==2.6.1
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

## Session pause

The Security Center's **Pause monitoring** control and `security pause` stop
monitoring only for the current Ann process. Ann automatically resumes the module
when it is launched again. Packet capture always remains explicitly started and
time-bounded.

# Security Monitor Startup Verification

This procedure verifies the controlled lifecycle for Ann Security Monitor. It is
written for development, release validation, and recovery diagnosis. It does not
authorise packet capture on a network.

## Preconditions

- Use supported Windows CPython 3.10 through 3.12 and install the root
  `requirements.txt` file.
- The Ann project data location must be writable, or a test-specific temporary
  project root must be used.
- An existing `data/security_monitor/settings.json` must contain valid JSON with
  `retention_days`, `failed_login_threshold`, and `syn_scan_threshold` values.
- Npcap and capture permission are not startup prerequisites. They are needed only
  after a user explicitly starts packet-metadata capture.

## Successful startup

1. Start Ann with `ann.security-monitor` enabled.
2. Confirm `modules status` reports `Ready` for `ann.security-monitor`.
3. Confirm `security status` reports read-only monitoring ready and an inactive
   network capture session.
4. Open Security Center and confirm dashboard values are available.
5. Confirm `logs/modules/ann.security-monitor.log` contains the successful startup
   and health-check record.

The module must create or use only `data/security_monitor/`. It must not start packet
capture, alter accounts, alter firewall settings, or inspect packet payloads.

## Controlled stopping and restarting

1. Start a test capture with a fake capture controller in automated tests, or use an
   authorised test environment for manual capture testing.
2. Run `modules stop ann.security-monitor`.
3. Confirm the capture controller is stopped, later capture callbacks are ignored,
   and `modules status` reports `Stopped`.
4. Confirm `security status` is unavailable while the module is stopped.
5. Run `modules start ann.security-monitor` or `modules restart
   ann.security-monitor` and confirm it returns to `Ready`.

Stopping is idempotent and leaves the saved Enabled preference unchanged. Ann shutdown
performs the same controlled stop. Session pause remains process-only: after Ann is
launched again, an enabled module starts unpaused.

## Startup failure and recovery

Use an isolated temporary project root for each failure case.

| Case | Expected result | Recovery |
| --- | --- | --- |
| Data directory path is a file | `validate()` or `start()` returns `Failed`; Ann remains running and logs details. | Restore a directory at that path, then retry or restart the module. |
| Existing settings JSON is malformed or missing required values | Startup returns `Failed`; no capture session remains active. | Correct or remove the settings file, then run `modules retry ann.security-monitor`. |
| Store creation raises an injected error | Startup returns `Failed`; partially created capture resources are stopped. | Remove the injected condition and retry. |
| Capture callback arrives after `stop()` | Callback is ignored and no new event is stored. | Start the module again if monitoring is needed. |

For every failure, inspect `logs/modules/ann.security-monitor.log`. The log must include
the user-visible failure context and technical traceback. Do not retry until the
underlying cause is understood or corrected.

## Optional packet-capture failure

Packet capture starts only through `security capture start [seconds]` or a confirmed
Security Center action. When Scapy is missing, Npcap is unavailable, the selected
interface is unusable, or capture permission is denied:

1. The capture command or Security Center shows an actionable runtime error.
2. The error is written to the Security Monitor module log.
3. The capture session remains stopped.
4. Security Monitor stays `Ready` for local login monitoring; Ann and other modules
   continue running.

Manual capture success testing is performed only on an authorised interface and checks
metadata handling only: source and destination addresses, protocol, port, and TCP
flags. It must not retain payload content.

## Automated test matrix

Run the module test suite without Npcap or live capture:

```powershell
..\\..\\.venv\\Scripts\\python.exe -m unittest discover -s modules/security_monitor/tests -v
```

The automated suite covers normal lifecycle startup, idempotent stopping, invalid data
paths, invalid settings, injected startup failure cleanup, ignored post-stop callbacks,
and isolated packet-capture failures using a fake capture controller. Core integration
tests additionally verify `modules start`, `stop`, `restart`, `retry`, and shutdown
delegation against the lifecycle contract.

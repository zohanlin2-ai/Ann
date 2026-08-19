# Update Verification and Recovery

This document defines how Ann verifies a complete project update before applying it, how it recovers when a newly applied update fails, and how to test those paths.

## Scope and Safety Boundary

Ann stages a candidate update in `backup_ann/` and verifies that staged project before replacing the active project. The verification process uses:

```text
ANN_PROJECT_ROOT=<project>/backup_ann
ANN_CORE_DIR=<project>/backup_ann/Ann_core
QT_QPA_PLATFORM=offscreen
```

This is staged-project isolation, not an operating-system sandbox. It prevents the normal Ann UI from opening and makes the staged project its own project root, but it does not restrict operating-system access available to the Python process. A candidate update must therefore be obtained only from the configured, trusted catalog source.

Before an update is applied, the active project is not replaced. The staged verification is designed not to write Module Registry state or module user data.

## Update Decision

`catalog.json` lists Ann Core and every catalog-managed module. Ann Updater compares each installed version with the catalog version. If every version matches exactly, Ann is current. If any managed component differs, Ann stages a complete project update; it does not download an optional module independently.

## Staged Verification Flow

1. Fetch the catalog configured by `ann_config.json`.
2. Download the complete project archive.
3. Verify the archive SHA-256 value when the catalog supplies one.
4. Reject ZIP entries that would extract outside the temporary extraction root.
5. Extract the archive and locate exactly one project containing `Ann_core/main.py`.
6. Copy that project to `backup_ann/`.
7. Run the following headless command from the staged project, with the staged environment variables shown above:

   ```powershell
   python Ann_core\main.py --verify-update
   ```

8. Treat exit code `0` as verified. Any non-zero exit code or a 30-second timeout fails verification.

## What `--verify-update` Checks

The staged verifier checks that:

- required project files exist, including `launcher.py`, `requirements.txt`, `VERSION.md`, `catalog.json`, and the required Core files;
- Ann Core's manifest ID and version match `catalog.json`;
- Ann Updater's manifest ID and version match its catalog entry;
- every catalog-managed module has an existing manifest whose ID and version match its catalog entry; and
- PySide6 and the Core module runtime can be imported in an offscreen Qt context.

Dependency version checking runs before the verifier through `Ann_core/main.py`. It also resolves nested `-r` requirement files, including Security Monitor's Scapy requirement.

## Verified Update Success

When all staged checks pass:

1. Ann Updater logs the staged command, its output, and the successful return code.
2. It starts `launcher.py --apply-update --wait-for <ann-process-id>`.
3. After Ann exits, the launcher copies the current managed project files to `rollback_ann/`, replaces them with the verified staged files, and starts the updated Core.
4. When the updated Core reports `Ready`, it has started successfully. When it later exits, the launcher clears update state; a non-zero exit after `Ready` is recorded as a runtime failure without rollback.

The launcher preserves `.venv`, `.git`, `modules/registry.json`, and downloaded modules while applying an update.

## Staged Verification Failure

The following conditions fail staged verification:

- catalog, manifest ID, version, or manifest path mismatch;
- missing required staged project file;
- unavailable or incompatible Python dependency;
- invalid archive, failed integrity check, or unsafe ZIP path;
- non-zero verifier exit code; or
- verifier timeout.

If archive download or extraction fails before staging, the active project remains untouched. If `backup_ann/` was created and verification fails, it is preserved for inspection. Ann does not apply the update, replace active project files, or roll back because the active project was never changed.

## Failure After Applying an Update

This is different from a staged verification failure. If verification passed but the newly applied Core exits with a non-zero status before reporting `Ready`:

1. The launcher records the failure and marks rollback as attempted.
2. The launcher restores managed files from `rollback_ann/`.
3. The previous Core starts once.
4. A second automatic rollback is refused to prevent a recovery loop. If the restored Core also fails, Ann stops and retains diagnostic logs.

## Diagnostics

| Purpose | Location |
| --- | --- |
| Aggregate update lifecycle | `logs/ann-update.log` |
| Updater diagnostics | `logs/modules/ann.updater.log` |
| Core diagnostics | `logs/modules/ann.core.log` |
| Security Monitor diagnostics | `logs/modules/ann.security-monitor.log` |
| Verified candidate after a staged failure | `backup_ann/` |
| Previous managed project after application | `rollback_ann/` |
| One-time rollback state | `.ann-update-state.json` |
| Core readiness handshake | `.ann-core-ready.json` |

## Test and Verification Checklist

### Automated checks

- Verify that every catalog entry matches its manifest ID, version, and path.
- Verify Ann Core version consistency across `catalog.json`, the Core manifest, `ann.__version__`, `pyproject.toml`, and `VERSION.md`.
- Verify nested requirements parsing with the root `requirements.txt` and module requirements files.
- Run Python syntax checks for Ann Core and bundled modules.
- Run Security Monitor storage-layer unit tests.

### Update-path tests

- Change a catalog-managed module version without changing its manifest; staged verification must fail and preserve `backup_ann/`.
- Remove a required staged file; verification must fail before application.
- Supply an archive with an unsafe ZIP path; extraction must be rejected.
- Make the staged verifier return non-zero or exceed its timeout; active Ann must remain unchanged.
- Make the newly applied Core exit non-zero before `Ready`; the launcher must restore once from `rollback_ann/` and must not loop.
- Make the newly applied Core report `Ready` and then exit non-zero; the launcher must record a runtime failure without rollback.

### Manual environment checks

- Start the PySide6 desktop UI after an update.
- Confirm that Scapy is installed when packet capture is required.
- Confirm that Windows Npcap and authorised administrator permissions are present before attempting live packet capture.
- Confirm Security Center pause, resume, and restart behaviour after an update.

Record the date, tested build versions, commands, result, and relevant log path for each release verification. Do not mark live packet capture as verified when only syntax or unit tests have been run.

# Release Checklist

This checklist applies to every paid-pilot build. Record the operator, date, commit SHA, application version, calculation-engine version, Windows image, and evidence location. A checked box without retained evidence is not validation.

## Release authorization

- [ ] Commercial license/EULA and pilot support terms are approved for the intended recipients.
- [ ] Third-party build and runtime licensing, including the current Inno Setup commercial-license guidance, has been reviewed and recorded.
- [ ] A qualified roadway engineer has approved the criteria/source traceability matrix and golden calculations for every enabled calculation path.
- [ ] Known limitations, supported inputs, and required independent checks are accepted by the pilot owner.
- [ ] `app_info.py` contains the intended semantic application version and calculation-engine version.
- [ ] Release notes identify calculation-impacting changes separately from application-only changes.

## Source and automated verification

- [ ] Worktree and commit SHA are recorded; release source is immutable and reviewable.
- [ ] `python -m unittest -v` passes without skipped, removed, or weakened tests.
- [ ] Dependency versions and security advisories are reviewed.
- [ ] No customer data, credentials, signing keys, Bentley files, or confidential fixtures are present in the repository or build context.

## Windows build and signing

- [ ] Build on the supported clean Windows x64 image with `scripts\build_windows.ps1 -BuildInstaller`.
- [ ] Confirm EXE ProductVersion/FileVersion matches `app_info.py`.
- [ ] Sign the EXE and installer with the approved Authenticode certificate; record whether the pilot self-signed certificate or a public certificate was used.
- [ ] Verify both signatures after signing and regenerate SHA-256 checksums for the signed artifacts.
- [ ] For a self-signed pilot, confirm each recipient independently verifies the public-certificate thumbprint before trusting it; never distribute the private key or a PFX.
- [ ] Scan release artifacts using the organization's approved malware controls.
- [ ] Install and uninstall using a standard (non-administrator) pilot account.
- [ ] Confirm Windows Defender/SmartScreen behavior is acceptable on each pilot Windows version.

## Built-application acceptance

- [ ] Launch the installed executable and confirm the displayed version.
- [ ] Run approved golden manual calculations and compare every numeric result and warning.
- [ ] Load sanitized LandXML covering lines/arcs, units, and station equations; verify names, stationing, radii, and direction.
- [ ] Confirm spiral LandXML produces the documented DXF block/warning and is not treated as supported geometry.
- [ ] Export PDF and verify version, engine, criteria warning, pagination, values, and legibility.
- [ ] Export ORD CSV and complete a real OpenRoads round trip; verify lanes, point types, station regions, slopes, and pivots.
- [ ] Export DXF and verify coordinates, units, levels/layers, text style, rotation, and placement in the target DGN.
- [ ] Save/reload a new project and approved v1/v2 compatibility fixtures; compare calculations and metadata.
- [ ] Force one failure for each file workflow and confirm the message, rotating log, and Open Log Folder action.

## Delivery and support

- [ ] Publish immutable, versioned EXE/installer/checksum assets and release notes to the approved private delivery channel.
- [ ] Verify downloaded hashes and signatures on a clean pilot machine.
- [ ] Provide installation, onboarding, limitations, privacy/log-sharing, backup, update, and rollback instructions.
- [ ] Record the 3–5 authorized pilot users, their application versions, and the support contact.
- [ ] Retain the prior signed installer for rollback; do not silently auto-update pilot machines.
- [ ] Archive test output, golden comparisons, screenshots, signatures, hashes, release notes, and approval records.

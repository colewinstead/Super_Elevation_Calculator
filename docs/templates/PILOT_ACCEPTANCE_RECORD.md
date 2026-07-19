# Paid-Pilot Release Acceptance Record

> Retain the completed record and its evidence in the controlled private evidence location. Do not store customer files, signing keys, private certificates, credentials, or confidential screenshots in the public repository.

## Release identity

- Acceptance record ID:
- Commit SHA:
- Application version:
- Calculation-engine version:
- Release candidate/build ID:
- Evidence root:
- Test start/end date:
- Release owner:
- Engineering acceptance owner:
- Pilot operations owner:

## Clean-machine Windows acceptance

- Windows edition/version/build and architecture:
- Standard-user test account:
- EXE/installer names and SHA-256 hashes:
- Authenticode subject, thumbprint, timestamp, and chain result:
- Malware-control product, definition date, and result:
- SmartScreen/Defender result:
- Install result:
- First-launch/version result:
- Uninstall and residue review result:
- `scripts/verify_windows_release.ps1 -RequireTimestamp` evidence ID:

## Browser acceptance

- Production build commit:
- Browsers and viewport widths:
- Free MDOT calculation result:
- Free gating/state-preservation result:
- Pro/Team entitlement result:
- Pyodide parity evidence ID:
- Network inspection confirming no engineering-file or calculation upload:
- Offline/grace/recovery result:

## Sanitized representative engineering acceptance

Record the file owner, written sanitization approval, retained private location, and hash for each input. Do not copy the input into this repository.

| Case ID | Sanitized input/hash | Scenario | Expected reference | Result | Evidence ID |
|:--|:--|:--|:--|:--:|:--|
| | | Lines/arcs, units, directions | | | |
| | | Station equations | | | |
| | | Coordinate declaration/zone | | | |
| | | Unsupported spiral rejection | | | |

### Deliverable checks

- [ ] LandXML names, stations, radii, directions, units, and coordinate metadata match the independent reference.
- [ ] ORD CSV completes a real OpenRoads round trip; lanes, point types, station regions, slopes, and pivots are independently checked.
- [ ] Overlay DXF is reviewed in the target DGN; coordinates, units, layers, text, rotations, and placements are independently checked.
- [ ] PDF values, warnings, profile/source revision, versions, pagination, and legibility are checked.
- [ ] Project save/open is checked in browser and desktop, including embedded LandXML integrity and provenance.
- [ ] Failure and recovery paths preserve entered work and provide understandable messages.

## Release and rollback rehearsal

- Current approved release:
- Prior retained signed release:
- Entitlement outage behavior tested:
- Rollback trigger exercised:
- Rollback package hash/signature verified:
- Recovery project copy verified:
- Customer communication draft evidence ID:
- Rollback decision owner:

## Open exceptions

| Exception | Risk owner | Pilot restriction | Due date | Closure evidence |
|:--|:--|:--|:--|:--|
| | | | | |

## Approval

- Engineering acceptance: name/signature/date
- Release acceptance: name/signature/date
- Pilot operations acceptance: name/signature/date
- Legal terms confirmed for these recipients: counsel/name/date/reference
- Final disposition: approved / restricted / rejected

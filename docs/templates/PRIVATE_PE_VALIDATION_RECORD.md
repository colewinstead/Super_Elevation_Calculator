# Private PE Validation Record

> Complete and retain this record outside the public repository. Do not commit a completed copy, reviewer identity, license information, signatures, confidential test vectors, or customer files.

## Record control

- Record ID:
- Evidence location:
- Review date:
- Supersedes record:
- Confidentiality/retention owner:

## Reviewer

- Name:
- License jurisdiction and number:
- License status checked on:
- Relationship to product:
- Signature and date:

## Validated release identity

Attach the generated `release-identity.json` and record:

- Commit SHA:
- Tracked worktree clean and untracked-file review:
- Application version:
- Calculation-engine version:
- Project schema version:
- MDOT profile ID and source revision:
- TDOT profile ID and source revision:
- Desktop/browser build identities:

## Scope reviewed

Mark each covered path and identify the retained evidence.

| Review area | Covered | Evidence ID | Limitations |
|:--|:--:|:--|:--|
| Manual single-curve calculations | | | |
| MDOT criteria selection and sources | | | |
| TDOT criteria selection and sources | | | |
| Transition stationing and lane events | | | |
| LandXML circular-curve ingestion | | | |
| Station equations | | | |
| Coordinate preservation/transformation | | | |
| Project save/open provenance | | | |
| PDF reports | | | |
| ORD CSV exports | | | |
| Overlay DXF exports | | | |
| Browser/Pyodide parity | | | |

## Test vectors and comparisons

For every vector, retain the input source, independently derived expected values, actual values, tolerance rationale, warnings, profile revision, and reviewer disposition.

| Vector ID | Path/profile | Independent reference | Result | Evidence ID |
|:--|:--|:--|:--:|:--|
| | | | | |

## Sources and limitations reviewed

- Governing-source copies and revision dates:
- Supported geometry, units, stationing, and classifications:
- Unsupported or blocked inputs:
- Known limitations and warnings:
- Project-specific checks that remain the responsible project PE's obligation:

## Change-control trigger

This record does not extend automatically to later changes. Renew engineering review before extending the validated scope after any change to formulas, criteria values, lookup tables, interpolation, rounding, branching, stationing, coordinate transformations, ORD mappings, or generated engineering results. Application-only changes still require regression and release acceptance.

## Disposition

- [ ] Approved for the stated scope and limitations.
- [ ] Approved with listed restrictions.
- [ ] Not approved.

Reviewer comments:

This internal product-validation record is not a seal or certification of a customer's project design. The licensed professional responsible for each project must independently verify criteria, inputs, stationing, coordinate systems, results, and deliverables against governing standards and project requirements.

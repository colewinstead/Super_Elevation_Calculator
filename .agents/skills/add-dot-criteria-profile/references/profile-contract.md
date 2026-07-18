# Criteria Profile Contract

Use this reference as the integration checklist for every state DOT profile. The state module owns agency-specific criteria; the surrounding files provide shared product behavior.

## Integration map

| Location | Responsibility | Required action |
|---|---|---|
| `<agency>_criteria.py` | Versioned tables, constants, validation, and deterministic lookups | Create one separate module per agency profile family. |
| `criteria_info.py` | Registry, aliases, provenance, source documents, applicable drawings, and calculation-source reporting | Register the canonical profile and keep returned metadata copy-safe. |
| `Super.py` | Shared calculation entry point and result contract | Dispatch by normalized profile ID and retain common result keys. |
| `super_service.py` | Desktop/browser-neutral manifest and profile-specific input choices | List the profile under both `criteria_profiles` and `options.profiles`. |
| `super_app.py` | Desktop selector and input restrictions | Display a friendly agency/revision label while saving the canonical profile ID. |
| `web/app/CalculatorApp.tsx` | Browser selector and profile-dependent inputs | Consume manifest data; do not implement engineering formulas in TypeScript. |
| `scripts/prepare_web_runtime.py` | Browser Python staging | Include every imported state criteria module. |
| `super_exports.py`, `super_pdf.py`, `super_dxf.py` | Lane events and deliverables | Verify agency labels, warnings, stations, and the absence of another agency's artifacts. |
| `super_project.py`, `super_batch.py` | Persistence and batch use | Preserve and route `criteria_profile`. |
| `test_<agency>_criteria.py` | Numeric, boundary, integration, and non-regression proof | Add published-example golden tests and explicit limitations. |
| `web/tests/pyodide-parity.mjs` | Browser/shared-engine parity | Add at least one golden calculation for the profile. |
| `app_info.py` | Product and engine version provenance | Follow `AGENTS.md` version rules. |

Some shared modules may require no code change when they already consume profile metadata dynamically. Inspect and test them anyway; do not add state-specific branches without a demonstrated need.

## Profile identity and metadata

Use a lowercase canonical ID that remains stable in saved projects, results, exports, and service calls:

```text
<agency>-<standards-family>-YYYY-MM-DD
```

Provide these metadata fields:

- `profile_id`
- `profile_name`
- `revision`
- `source_status`
- `governing_authority`
- `source_documents`
- `implementation_modules`
- `engineering_change_notice`

Each source document must include its title, official HTTPS URL, and the most specific available revision, issue date, edition, sheet, table, section, or library anchor. Distinguish controlling calculation criteria from supporting roadway-classification information.

The canonical profile ID date identifies the verified criteria set. If controlling values change, create a new versioned profile instead of silently relabeling old saved calculations.

## Calculation and result contract

Keep the public call routed through `Super.calculate_superelevation(..., criteria_profile=...)`. Results must continue to provide the shared fields consumed by lane rows, reports, projects, and browser services, including:

- `inputs.criteria_profile`
- `calculation_metadata.engine_version`
- `calculation_metadata.criteria`
- manual-override flags
- rate, runoff, tangent-runout, and transition values where applicable
- entering and exiting station values
- `warnings`
- `segments`

If an agency does not use a shared concept, return an explicit not-applicable value and explanation where the existing result contract permits it. Do not fabricate a value to satisfy an exporter.

## Selection rules

- Use exact agency table speeds unless the source defines interpolation.
- Define what happens at an exact radius, between radii, above normal-crown thresholds, and below minimum radius.
- Separate desirable, allowable, reconstruction, low-speed, or project-specific tables. Never select among them silently.
- Model lane-count factors and pivot location exactly as defined.
- Reject unsupported divided, undivided, spiral, multilane, or manual-override cases when the shared geometry cannot represent them safely.
- Preserve the current MDOT default and numeric outputs unless a separately explained defect authorizes a change.

## Verification evidence

For every published agency example, record the inputs, raw computed values, displayed rounding, and any stationing or geometry assumptions. A golden test should demonstrate the same sequence the source describes, not merely contain the expected final number.

When no published example exists, create an independent hand calculation tied to a cited equation and have it reviewed before calling the profile verified. Automated tests prove implementation consistency; they do not replace engineering approval.

The integration validator checks wiring and provenance only. It intentionally does not validate numeric tables or certify engineering correctness.

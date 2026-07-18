---
name: add-dot-criteria-profile
description: Add or update a versioned state DOT standards profile in the Superelevation Calculator, including official-source provenance, a separate state criteria module, shared-engine integration, desktop and browser selection, export traceability, and published-example regression tests. Use when the user asks to add another DOT, incorporate a state's roadway or superelevation standards, revise an existing agency profile, or verify that a profile is fully integrated.
---

# Add a DOT Criteria Profile

Add one state DOT at a time without changing existing engineering results. Treat official criteria transcription and calculation behavior as safety-sensitive work.

## Prepare

1. Read the repository `AGENTS.md` and [references/profile-contract.md](references/profile-contract.md) completely.
2. Inspect the branch, worktree, current application version, existing profiles, and latest release tag. Preserve unrelated work.
3. Confirm the state, agency acronym, standards family, requested roadway configurations, and official source URLs. If the user supplies only a library page, follow its links to the controlling drawings and manuals.
4. Use current primary agency sources. Use the PDF skill to inspect drawings or tables whose layout affects interpretation. Do not rely on search snippets or secondary summaries for numeric values.
5. Record document titles, revision or issue dates, sheet/table identifiers, URLs, and the exact scope being implemented. Keep downloads temporary unless the user explicitly asks to commit them.

Before editing calculations, report the active tables and formulas, excluded alternatives, unsupported configurations, assumptions, and any source ambiguity. Stop for direction when ambiguity could change an engineering result.

## Implement

1. Create a stable profile ID such as `<agency>-<standards-family>-YYYY-MM-DD`. The date must identify the verified governing revision, not the coding date.
2. Put the new state's numeric tables and deterministic lookup helpers in a separate `<agency>_criteria.py` module. Never append multiple states' tables to `Super.py` or to another state's module.
3. Transcribe values exactly and cite the controlling drawing, table, or equation in comments and profile metadata. Do not interpolate, round, select a conservative row, or combine criteria unless the source explicitly requires that behavior.
4. Register the profile, alias, selector summary, source metadata, applicable drawings, calculation sources, limitations, and engineering notice in `criteria_info.py`.
5. Route the profile through `Super.calculate_superelevation`. Keep all calculation logic in Python so desktop and browser use the same engine. Preserve the existing default profile unless the user explicitly changes it.
6. Add profile-specific input options to `super_service.application_manifest`. Expose a friendly agency/revision label in the desktop selector and verify the browser selector consumes the manifest.
7. Add the state module to `scripts/prepare_web_runtime.py`. Never copy calculation logic into TypeScript or checked-in browser output by hand.
8. Verify project save/load, batch calculation, lane events, PDF, ORD CSV, and DXF behavior. Surface agency identity, source provenance, and engineering warnings; remove or hide another agency's stamps or figures.
9. Block unsupported roadway geometry or criteria with a direct review-friendly error. Do not reuse a different configuration's signs, pivot model, stationing, or assumptions merely to return a result.
10. Increase `APP_VERSION` beyond the latest release for a new pull request. Increase `CALCULATION_ENGINE_VERSION` when calculation behavior changes.

## Prove the profile

Add focused tests that cover:

- every published agency example available for the implemented scope, comparing both raw and agency-rounded results;
- independent table transcription checks and row/column structure;
- exact boundaries, between-row selection policy, minimum radii, allowed speeds, lane factors, and normal-crown behavior;
- unsupported configurations and manual-override policy;
- default-profile non-regression;
- registry, manifest, desktop label, project, export warning, and browser-runtime exposure; and
- at least one Pyodide parity calculation using the new profile.

A passing formula test is not a complete validation when the agency example uses spiral geometry, divided-roadway pivots, or other inputs the application does not model. State that limitation and test the warning or rejection.

## Validate

Run the integration checker with the canonical profile ID:

```bash
python3 .agents/skills/add-dot-criteria-profile/scripts/validate_profile.py <profile-id>
```

Then run:

```bash
python3 -m unittest -v
git diff --check
cd web
npm exec tsc -- --noEmit
npm run lint
npm test
```

Use the repository's supported Node environment. Do not weaken tests or edit generated output to make validation pass.

## Finish

Review the diff for accidental changes to existing tables or outputs. Commit only intended source, skill, and test files; leave build artifacts untracked. Report:

- profile ID and supported scope;
- official sources and revision dates;
- published examples and exact matching results;
- unsupported or unverified behavior;
- all validation results; and
- commit and push status.

Do not describe a profile as engineering-verified solely because its automated tests pass. Preserve any required independent engineering-review status in metadata and user-facing output.

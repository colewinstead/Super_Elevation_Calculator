# Superelevation Calculator repository guidance

## Engineering safety

- Treat formulas, lookup tables, stationing, ORD mappings, coordinate transforms, and generated engineering results as frozen unless a clear defect is identified and explained first.
- Keep desktop and browser behavior on the shared Python engine; do not duplicate calculation logic in the browser UI.

## Versioned merges

- `main` is user-ready. Every pull request merged into `main` becomes a browser GitHub Release while the desktop edition is Coming soon.
- Increase `APP_VERSION` in `app_info.py` beyond the latest release in every pull request, including documentation-only changes.
- Do not merge when `validate-version` or any other required check is red.
- Use squash merges only.

## Validation

- Run `python3 -m unittest -v` on macOS/Linux or `python -m unittest -v` on Windows.
- From `web`, run the TypeScript check, lint, production build tests, and Pyodide parity tests before browser releases.
- Windows EXE and macOS DMG workflows are manual-only while desktop distribution is paused. Do not make them required PR checks or automatic `main` release jobs until the user resumes desktop releases.
- Preserve signing keys outside the repository. Automated GitHub executables are unsigned; signed pilot releases use the private Windows signing workflow and `scripts/verify_windows_release.ps1`.

## Website publishing

- After a successful merge and GitHub Release, invoke `$ship-main` or ask Codex to “Ship main.”
- Publish only to the existing ChatGPT Site identified by `web/.openai/hosting.json`. Never create a replacement site, change its slug, or change its access policy unless the user explicitly requests that change.

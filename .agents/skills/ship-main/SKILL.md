---
name: ship-main
description: Verify a merged Superelevation Calculator release and publish that exact main commit to the existing ChatGPT Site. Use when the user says "Ship main", asks to rebuild or republish the website after merging to main, or invokes $ship-main from this repository.
---

# Ship Main

Publish the exact released `main` source to the existing ChatGPT Site. Explicit invocation authorizes a new production deployment at the site's current access level; it does not authorize changing access, slug, domain, or project identity.

## Preconditions

1. Read the repository `AGENTS.md`, `app_info.py`, and `web/.openai/hosting.json`.
2. Confirm GitHub CLI authentication and access to `colewinstead/Super_Elevation_Calculator`.
3. Fetch `origin/main` and tags without discarding local work. If the current worktree is dirty, preserve it and use a clean temporary worktree at `origin/main`.
4. Read `APP_VERSION`, then verify all of the following:
   - Release tag `vAPP_VERSION` exists, is a full non-draft/non-prerelease release, and targets `origin/main`.
   - The Full Release workflow for `origin/main` succeeded.
   - Release assets include `SuperElevation.exe`, `SHA256SUMS.txt`, the versioned browser archive, and its checksum.
5. Stop with a plain-language blocker if the version, commit, workflow, or assets do not match. Do not repair the release or modify source as part of this skill.

## Validate the exact source

1. Work from the clean `origin/main` checkout.
2. Install declared dependencies only when absent.
3. Run the Python unit tests.
4. From `web`, stage the shared Python runtime, type-check, lint, build the Sites production output, run the rendered-shell tests, and run Pyodide parity.
5. Do not alter calculations or weaken tests to obtain a passing build.

## Publish the existing site

1. Use the available `sites-building` and `sites-hosting` skills and follow their current instructions.
2. Reuse the exact `project_id` in `web/.openai/hosting.json`. Never call create-site when it is present.
3. Obtain a fresh short-lived source credential when needed. Keep it out of output, remotes, files, and Git configuration.
4. Push an exact-tree source commit to the existing Sites source branch without rewriting its history.
5. Package the validated `web/dist` with the Sites packaging helper, save one version, and deploy that saved version at the existing public access level.
6. Poll until deployment succeeds or fails. On success, report the GitHub Release URL and deployed Sites URL. On failure, report the user-visible cause without exposing credentials.

## Cross-computer requirements

- Use the same GitHub account access and the same ChatGPT account or workspace that owns the existing Site.
- If the Sites connector or project access is unavailable, stop and ask the user to enable or authenticate it. Do not create another site as a fallback.

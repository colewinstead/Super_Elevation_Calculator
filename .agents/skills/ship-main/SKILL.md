---
name: ship-main
description: Verify a merged Superelevation Calculator release and publish that exact main commit to the existing ChatGPT Site. Use when the user says "Ship main", asks to rebuild or republish the website after merging to main, or invokes $ship-main from this repository.
---

# Ship Main

Publish the exact released `main` source to the existing ChatGPT Site. Explicit invocation authorizes a new production deployment at the site's current access level; it does not authorize changing access, slug, domain, or project identity.

Use `scripts/prepare_site_version.ps1` for the fragile Sites history and packaging steps on Windows. Do not reconstruct those commands manually unless the script is unavailable.

## Preconditions

1. Read the repository `AGENTS.md`, `app_info.py`, and `web/.openai/hosting.json`.
2. Confirm GitHub CLI authentication and access to `colewinstead/Super_Elevation_Calculator`.
3. Fetch `origin/main` and tags without discarding local work. If the current worktree is dirty, preserve it and use a clean temporary worktree at `origin/main`.
4. Read `APP_VERSION`, then verify all of the following:
   - Release tag `vAPP_VERSION` exists, is a full non-draft/non-prerelease release, and targets `origin/main`.
   - The Full Release workflow for `origin/main` succeeded.
   - Release assets include the versioned browser archive and its checksum.
   - Require Windows or macOS assets only when their workflows are enabled for automatic `main` releases. Manual-only desktop workflows mean those assets are intentionally deferred.
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
3. Inspect the Site and hosted environment-variable names. Never copy `.dev.vars`, tokens, signing secrets, or billing credentials into Sites without separate explicit authorization.
4. Obtain a fresh short-lived source credential. Keep it out of output, remotes, files, command history, and Git configuration.
5. In one shell process, place the credential's complete HTTP authorization header in the task-specific `SHIP_MAIN_SITE_AUTH_HEADER` environment variable and run:

   ```powershell
   .\.agents\skills\ship-main\scripts\prepare_site_version.ps1 `
     -RepositoryRoot <clean-worktree> `
     -ReleaseCommit <origin-main-sha> `
     -SiteRemoteUrl <credential-remote-url> `
     -ArchivePath <unique-temp-archive>
   ```

   The script verifies a clean exact checkout and deployable build, preserves the Sites source parent, pushes an exact-tree source commit, creates the archive, and verifies the remote head. It prints only sanitized JSON. Do not print the environment variable or full command when it contains the credential.
6. Pass the script's `source_commit` and `archive` to `save_site_version`. Deploy that saved version at the existing access level.
7. Poll until deployment succeeds or fails. Verify the custom domain and `/calculator` return HTTP 200 and expose the released app version.
8. Remove only the exact temporary worktree and archive after resolving and confirming that both are inside the operating-system temporary directory.

## Efficiency rules

- Run release checks and exact-source validation once. Reuse their results during the same invocation.
- Fetch the existing Sites branch before creating its exact-tree child; never attempt a blind push first.
- Request the short-lived Sites credential only after validation and the production build pass, so it does not expire during tests.
- Use the bundled PowerShell helper on Windows instead of the Bash packaging helper.
- Saving a Site version is not deployment. Save once, deploy once, and poll the returned deployment ID.

## Cross-computer requirements

- Use the same GitHub account access and the same ChatGPT account or workspace that owns the existing Site.
- If the Sites connector or project access is unavailable, stop and ask the user to enable or authenticate it. Do not create another site as a fallback.

# Commercial Readiness Status

## Current decision

The Superelevation Calculator has a browser-first branded authentication, payment, and entitlement implementation prepared for WorkOS and Stripe staging/test mode. Live charging remains locked until secure account values, callback and webhook destinations, D1 migrations, and final release acceptance are configured. The browser remains local-first: project JSON, LandXML, calculations, and exports stay on the user's device. Authentication and entitlement checks exchange account and license metadata only.

The owner reports that the calculator has been reviewed as a Professional Engineer for the recorded application, engine, and criteria scope. The detailed attestation, test vectors, reviewer identity, license information, and supporting evidence remain in a controlled private record outside this public repository. This repository does not make a named or personal PE-certification claim.

Engineering validation is version-specific. Any change to formulas, lookup tables, criteria values, interpolation, rounding, stationing, coordinate transforms, ORD mappings, or generated engineering results requires a renewed review before the validated scope can be extended.

## Before accepting payment

1. The owner reports that the commercial terms and privacy position were approved privately. Before live charging, verify that the clean public Terms and Privacy pages exactly match that private approval and that the seller identity and contact details displayed by Stripe are correct.
2. The internal PE record must identify the exact validated application version, calculation-engine version, criteria-profile revisions, reviewed branches, golden vectors, limitations, date, and change-control trigger.
3. The desktop edition remains Coming soon and is excluded from the browser paid pilot. Before any later paid desktop offering, a signed and timestamped Windows build and installer must pass clean-machine install, launch, uninstall, malware-scan, signature, and checksum acceptance.
4. Sanitized representative LandXML projects must pass real ORD CSV round trips, DXF-in-DGN overlay review, PDF review, and project save/open compatibility tests.
5. Pilot onboarding must define supported inputs, known limitations, independent-check requirements, local storage, backup/recovery, update/rollback, diagnostics, support response, and the release owner.

## Blocker closure status

| Blocker | Repository preparation | Remaining external completion |
|:--|:--|:--|
| Commercial terms and marketing language | Clean customer-facing Terms and Privacy routes are implemented; private legal-review material is intentionally not retained in the public repository. | Confirm the deployed pages and Stripe seller details match the privately approved record before enabling live mode. |
| Private owner-PE evidence | Versioned private-record template and outside-repository evidence generator are implemented. | Owner completes, signs, and retains the private record for the exact release scope. |
| Clean-machine desktop acceptance | Acceptance record, existing signed-build workflow, signature/hash verifier, and rollback evidence structure are ready. | Deferred while desktop is Coming soon. Complete before accepting payment for or promising desktop access; it does not block a browser-only pilot. |
| Representative LandXML/ORD/DXF/PDF acceptance | Sanitized-file protocol and deliverable checks are defined without committing customer files. | Authorized sanitized cases complete real OpenRoads and DGN round trips and receive engineering acceptance. |
| Privacy, support, onboarding, diagnostics, and rollback | `docs/PILOT_OPERATIONS.md` and a local redacted diagnostic tool define the process. | Assign named owners, counsel-approve external promises, rehearse, and sign the release record. |

Use `python scripts/create_pilot_evidence_bundle.py --output <private-directory>` to create an unapproved evidence workspace outside this repository. Generation prepares records; it does not approve them.

## Required for a controlled paid pilot

- Named pilot users and a controlled entitlement register.
- Version-pinned releases and immutable calculation provenance.
- Seven-day browser and thirty-day desktop offline grace policies.
- Local recovery of open work after entitlement failure or expiry.
- Redacted, opt-in diagnostics that never attach engineering files automatically.
- Published supported-input and compatibility limits.
- Acknowledgment that the responsible project PE independently verifies the work.
- Manual, controlled updates with a documented rollback release.

## Can wait until after the first pilot

- Team seat administration and organization billing.
- Silent or automatic software updates.
- Broad enterprise administration and directory synchronization.
- Product telemetry or automatic diagnostic uploads.
- A broad Windows/macOS/ORD compatibility matrix.
- Spiral workflows when pilot screening explicitly excludes spirals.
- Multi-administrator roles, bulk entitlement tools, and a general-purpose enterprise entitlement portal.

## Responsibility and private approval

Public product surfaces use this engineering-aid statement:

> The licensed professional responsible for the project must independently verify criteria, inputs, stationing, coordinate systems, results, and deliverables against governing standards and project requirements.

That statement describes the intended workflow and does not claim that the software owner can eliminate every possible responsibility for defects. The controlling approval record and any professional advice are retained privately rather than in this public repository.

## Capability model

The centralized commercial policy is separate from calculation and export code.

| Capability | Free | Pro | Team |
|:--|:--:|:--:|:--:|
| Manual MDOT single-curve calculation | Yes | Yes | Yes |
| Basic results, lane diagram, standards, and on-screen provenance | Yes | Yes | Yes |
| Synthetic sample calculation | Yes | Yes | Yes |
| LandXML and multi-curve workflows | No | Yes | Yes |
| All supported DOT profiles | No | Yes | Yes |
| Project files, PDF, ORD CSV, and overlay DXF | No | Yes | Yes |
| Formal provenance exports and priority support | No | Yes | Yes |
| Desktop edition | Coming soon | Coming soon | Coming soon |
| Named-user seat administration | No | No | Yes |

Entitlement checks authorize a workflow before it reaches engineering services. They never supply calculation inputs, select a fallback profile, change a result, or modify an export. If a requested profile is unavailable, the action fails with an explicit upgrade message and the prior inputs and results remain unchanged.

## Authentication and automatic Pro activation

The browser uses an `EntitlementProvider` interface so identity and billing vendors can be changed without modifying engineering modules. Public Free calculation remains anonymous. Paid account routes use branded WorkOS AuthKit sign-in, map the stable provider subject to a one-way internal user ID, and perform authorization on the server.

The implemented Stripe test-mode flow is:

1. The customer signs in before checkout.
2. Hosted checkout processes payment; the browser success redirect is not authorization.
3. A signature-verified webhook updates the D1 subscription and entitlement ledger.
4. The entitlement service issues a signed, versioned snapshot for that user or organization.
5. The browser refreshes the snapshot and unlocks Pro automatically.
6. A delayed webhook shows an activating state and retries without creating another charge.

Stripe documents asynchronous subscription webhooks, signature verification, and internal persistence of active entitlements:

- <https://docs.stripe.com/billing/entitlements>
- <https://docs.stripe.com/billing/subscriptions/webhooks>
- <https://docs.stripe.com/webhooks/signature>

The calculator never calls Stripe directly; only server payment routes do. The entitlement service stores identity, plan, subscription, token, acceptance, and audit metadata only. It does not receive project names, project JSON, LandXML, calculation inputs/results, PDFs, CSVs, or DXFs.

## Offline and service-failure behavior

- A valid signed Pro snapshot remains active for up to seven days in the browser. A future desktop edition will use a thirty-day policy after separate acceptance.
- First use without a service connection receives Free access.
- During grace, cached Pro workflows remain available.
- After grace, open inputs and results remain visible and locally recoverable; only new Pro actions are blocked.
- Cancellation, payment failure, identity mismatch, token failure, and entitlement-service outages never recalculate results, switch criteria profiles, or erase work.
- Future Team purchases will create an organization-admin entitlement. Other people will receive Pro only when assigned a named seat.

## Standards-profile updates and provenance

Each calculation records the application version, engine version, project schema, criteria-profile ID, source revision, calculation sources, and active overrides. Standards updates create a new immutable profile ID and require regression evidence plus renewed PE review when they affect engineering behavior. A saved project that requests an unavailable profile must identify that exact profile; the application must not silently substitute another agency or revision.

## Support and diagnostics

Future support bundles are explicit and opt-in. They may contain application/engine/profile versions, operating-system and build identity, entitlement status codes, and redacted logs. Project files and engineering exports are never selected automatically. Users choose every attachment before sharing it.

## Safe technical foundation implemented now

- Central Free/Pro/Team capability policy and provider interface.
- Localhost-only development states, including unavailable-service fallback.
- Browser and service checks for professional workflows.
- Accessible, feature-specific upgrade messages that preserve work.
- Browser-first homepage, supported-DOT section, plan comparison, and honest desktop Coming soon status.
- Branded WorkOS AuthKit sign-in for paid accounts, Stripe-hosted Checkout and customer portal routes, a signature-verified webhook, D1 subscription records, and signed offline entitlement snapshots.
- Owner-only complimentary Pro administration with stable-ID authorization, optional expiration, revocation, and a retained grant history.
- Clean public Terms and Privacy routes with private attorney material excluded from the repository.
- No live keys, production charging, trials, promotion codes, card-data handling, Team administration, or desktop entitlement activation.

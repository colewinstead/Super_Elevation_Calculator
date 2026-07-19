# Stripe Payment Setup

The browser application supports a $29 USD monthly Pro subscription through Stripe-hosted Checkout. This repository contains no Stripe keys, payment-card data, private legal-review records, or engineering files.

## Architecture

1. A customer signs in through the branded WorkOS AuthKit flow and accepts the current Terms and Privacy Policy.
2. The server creates or reuses a Stripe Customer and opens hosted Checkout.
3. The checkout success page displays an activation state but does not grant Pro.
4. Stripe sends a signature-verified webhook to `/api/stripe/webhook`.
5. The webhook updates the D1 subscription ledger and the browser refreshes its entitlement.
6. Stripe's hosted customer portal handles payment methods, invoices, and cancellation.

Authentication, billing, and entitlement services store account, plan, acceptance, transaction status, and audit metadata only. Project files, LandXML, calculations, project JSON, PDF, CSV, and DXF files remain on the user's device.

## Stripe test setup

1. In Stripe test mode, create one recurring product named `Superelevation Calculator Pro`.
2. Create one price for exactly `$29.00 USD` billed monthly.
3. Enable the Stripe customer portal with cancellation at the end of the current billing period. Leave plan switching, seat quantity changes, promotion codes, trials, and retention offers off for the first release.
4. Register the deployed webhook URL ending in `/api/stripe/webhook` for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
5. Configure these values as encrypted hosting secrets, never in source control:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`
   - `STRIPE_PRO_PRICE_ID`
   - `ENTITLEMENT_SIGNING_PRIVATE_JWK`
6. Keep `ALLOW_LIVE_PAYMENTS=false` throughout local and hosted test acceptance.

The application verifies the Stripe Price is active, USD 2900 cents, recurring monthly, and interval count one before it creates Checkout. A mismatch blocks checkout.

The entitlement private key is retained outside the repository. Its matching public verification key is safe to ship with the browser. Pro snapshots are signed before they are cached, and an invalid or edited cache fails closed to Free.

## Test acceptance

- Complete Stripe test checkout with a Stripe test card.
- Confirm the success page says `Activating Pro` until the webhook is processed.
- Confirm the account becomes Pro without a second payment or manual change.
- Open the calculator in the original tab and confirm it refreshes to Pro without losing entered work.
- Cancel in the Stripe customer portal and confirm access continues through the paid period.
- Exercise payment failure and confirm the seven-day entitlement grace behavior.
- Replay the same webhook and confirm it is treated as an idempotent duplicate.
- Temporarily disable the entitlement endpoint and confirm cached Pro continues only through its recorded offline expiry.
- Confirm Stripe, D1, logs, and diagnostics contain no engineering file content.

## Live activation gate

Do not add live keys or set `ALLOW_LIVE_PAYMENTS=true` until all of the following are complete:

- The deployed Terms and Privacy pages match the privately approved versions.
- Stripe displays the correct seller identity, receipt contact, cancellation method, refund rule, and statement descriptor.
- D1 migrations are applied and backed up.
- Webhook signature verification and replay tests pass against the live endpoint.
- A real low-value purchase, cancellation, refund handling, receipt, tax treatment, entitlement activation, grace, and support recovery are accepted by the release owner.
- The release is merged, released, and published through the repository's normal release workflow.

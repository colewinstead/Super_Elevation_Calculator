# Branded Authentication Setup

The browser application uses WorkOS AuthKit for branded account identity. Free manual calculations remain anonymous. WorkOS receives account identity and authentication events only; it does not receive project names, LandXML, engineering inputs, calculations, projects, or exports.

## WorkOS staging setup

1. Create a WorkOS account and a staging AuthKit application named `Superelevation Calculator`.
2. Enable Magic Auth and, when desired, Microsoft and Google OAuth in the WorkOS dashboard.
3. Set the application homepage to the local or hosted product URL.
4. Add `http://localhost:3000/auth/callback` as the local redirect URI.
5. Set the sign-in endpoint to `http://localhost:3000/auth/sign-in` for local testing.
6. Copy `web/.dev.vars.example` to the ignored `web/.dev.vars` and add the staging API key, client ID, a random cookie password of at least 32 characters, and redirect URI.
7. Brand the hosted AuthKit screen with the product name, logo, colors, support contact, Terms URL, and Privacy URL.

For the eventual custom domain, add the exact HTTPS callback and sign-in endpoints in WorkOS, for example:

- `https://example.com/auth/callback`
- `https://example.com/auth/sign-in`

Production keys belong in encrypted Sites environment values. Never commit them. The session cookie is encrypted, HTTP-only, secure in production, and protected by AuthKit's PKCE and CSRF verification.

## Account and billing linkage

The WorkOS user subject is hashed into the application's internal billing-user ID. Email changes therefore do not detach an account from its subscription. Stripe receives that internal ID in customer and subscription metadata. Only a verified Stripe webhook changes the subscription ledger or grants Pro.

## Launch acceptance

- Complete email-code, Microsoft, and Google sign-in tests for each enabled method.
- Confirm sign-out removes the local session and does not change saved calculator work.
- Confirm the account page returns to the same internal user after an email/profile update.
- Confirm an anonymous visitor receives Free and cannot call billing routes.
- Confirm WorkOS, Stripe, D1, logs, and diagnostics contain no engineering-file content.
- Confirm the deployed Privacy Policy names WorkOS and Stripe consistently with the privately approved notice.

declare namespace Cloudflare {
  interface Env {
    DB: D1Database;
    WORKOS_API_KEY?: string;
    WORKOS_CLIENT_ID?: string;
    WORKOS_COOKIE_PASSWORD?: string;
    NEXT_PUBLIC_WORKOS_REDIRECT_URI?: string;
    ADMIN_WORKOS_USER_IDS?: string;
    STRIPE_SECRET_KEY?: string;
    STRIPE_WEBHOOK_SECRET?: string;
    STRIPE_PRO_PRICE_ID?: string;
    ENTITLEMENT_SIGNING_PRIVATE_JWK?: string;
    ALLOW_LIVE_PAYMENTS?: string;
  }
}

declare module "cloudflare:workers" {
  export const env: Cloudflare.Env;
}

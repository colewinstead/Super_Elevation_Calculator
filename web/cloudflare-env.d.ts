declare namespace Cloudflare {
  interface Env {
    DB: D1Database;
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

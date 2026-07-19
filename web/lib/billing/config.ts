import { env } from "cloudflare:workers";

export type BillingConfig = {
  secretKey: string;
  webhookSecret: string;
  proPriceId: string;
  entitlementPrivateJwk: string;
  liveMode: boolean;
};

type RuntimeEnv = {
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  STRIPE_PRO_PRICE_ID?: string;
  ENTITLEMENT_SIGNING_PRIVATE_JWK?: string;
  ALLOW_LIVE_PAYMENTS?: string;
};

function runtimeEnv(): RuntimeEnv {
  return env as unknown as RuntimeEnv;
}

export function billingConfigurationStatus() {
  const values = runtimeEnv();
  const liveMode = values.STRIPE_SECRET_KEY?.startsWith("sk_live_") ?? false;
  const complete = Boolean(
    values.STRIPE_SECRET_KEY
      && values.STRIPE_WEBHOOK_SECRET
      && values.STRIPE_PRO_PRICE_ID
      && values.ENTITLEMENT_SIGNING_PRIVATE_JWK,
  );
  const liveAllowed = !liveMode || values.ALLOW_LIVE_PAYMENTS === "true";
  return {
    configured: complete && liveAllowed,
    mode: liveMode ? "live" : "test",
    reason: !complete
      ? "Stripe test configuration has not been connected."
      : !liveAllowed
        ? "Live charging is locked until ALLOW_LIVE_PAYMENTS is explicitly enabled."
        : null,
  } as const;
}

export function getBillingConfig(): BillingConfig {
  const status = billingConfigurationStatus();
  if (!status.configured) throw new Error(status.reason || "Billing is unavailable.");
  const values = runtimeEnv();
  return {
    secretKey: values.STRIPE_SECRET_KEY!,
    webhookSecret: values.STRIPE_WEBHOOK_SECRET!,
    proPriceId: values.STRIPE_PRO_PRICE_ID!,
    entitlementPrivateJwk: values.ENTITLEMENT_SIGNING_PRIVATE_JWK!,
    liveMode: status.mode === "live",
  };
}

export function getEntitlementPrivateJwk() {
  const value = runtimeEnv().ENTITLEMENT_SIGNING_PRIVATE_JWK;
  if (!value) throw new Error("Entitlement signing is unavailable.");
  return value;
}

import type { BillingAccess } from "./entitlement-policy";

export type StoredManualEntitlement = {
  revokedAt: string | null;
  expiresAt: number | null;
};

export function resolveManualAccess(
  grant: StoredManualEntitlement | null,
  nowSeconds = Math.floor(Date.now() / 1000),
  browserGraceDays = 7,
): BillingAccess | null {
  if (!grant || grant.revokedAt || (grant.expiresAt !== null && grant.expiresAt <= nowSeconds)) return null;
  const offlineWindow = nowSeconds + browserGraceDays * 86400;
  return {
    plan: "pro",
    status: "active",
    offlineExpiresAt: grant.expiresAt === null ? offlineWindow : Math.min(offlineWindow, grant.expiresAt),
  };
}

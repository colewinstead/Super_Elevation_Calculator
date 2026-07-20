import type { BillingAccess } from "./entitlement-policy";

export function resolveAdministratorAccess(
  isAdministrator: boolean,
  nowSeconds = Math.floor(Date.now() / 1000),
  browserGraceDays = 7,
): BillingAccess | null {
  if (!isAdministrator) return null;
  return {
    plan: "pro",
    status: "active",
    offlineExpiresAt: nowSeconds + browserGraceDays * 86400,
  };
}

export type StoredSubscription = {
  status: string;
  currentPeriodEnd: number;
  graceUntil: number;
  cancelAtPeriodEnd: boolean;
};

export type BillingAccess = {
  plan: "free" | "pro";
  status: "active" | "grace";
  offlineExpiresAt: number;
};

const ACTIVE_STATUSES = new Set(["active", "trialing"]);

export function resolveBillingAccess(
  subscription: StoredSubscription | null,
  nowSeconds = Math.floor(Date.now() / 1000),
  browserGraceDays = 7,
): BillingAccess {
  if (!subscription) {
    return { plan: "free", status: "active", offlineExpiresAt: nowSeconds };
  }

  const offlineWindow = nowSeconds + browserGraceDays * 86400;
  if (ACTIVE_STATUSES.has(subscription.status)) {
    return {
      plan: "pro",
      status: "active",
      offlineExpiresAt: Math.min(offlineWindow, subscription.graceUntil),
    };
  }

  if (subscription.graceUntil >= nowSeconds) {
    return {
      plan: "pro",
      status: "grace",
      offlineExpiresAt: Math.min(offlineWindow, subscription.graceUntil),
    };
  }

  return { plan: "free", status: "active", offlineExpiresAt: nowSeconds };
}

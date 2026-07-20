import commercialManifest from "@/app/generated/commercial-manifest.json";
import { getProductUser } from "@/app/product-auth";
import { isProductAdmin } from "@/lib/auth/admin";
import { resolveAdministratorAccess } from "@/lib/billing/admin-entitlement-policy";
import { billingConfigurationStatus } from "@/lib/billing/config";
import { resolveBillingAccess } from "@/lib/billing/entitlement-policy";
import { resolveManualAccess } from "@/lib/billing/manual-entitlement-policy";
import { getActiveManualEntitlement } from "@/lib/billing/manual-entitlements";
import { claimActivePreauthorizedEntitlement } from "@/lib/billing/preauthorized-entitlements";
import { signEntitlementSnapshot } from "@/lib/billing/entitlement-token";
import { billingUserId } from "@/lib/billing/identity";
import { getSubscriptionForUser, upsertBillingUser } from "@/lib/billing/store";

export const dynamic = "force-dynamic";

function snapshotFor(plan: "free" | "pro", status: "active" | "grace", offlineExpiresAt: number, source = "subscription-ledger") {
  return {
    plan,
    capabilities: [...commercialManifest.plans[plan].capabilities],
    source,
    status,
    browser_grace_days: commercialManifest.browser_grace_days,
    desktop_grace_days: commercialManifest.desktop_grace_days,
    issued_at: Math.floor(Date.now() / 1000),
    offline_expires_at: offlineExpiresAt,
  };
}

export async function GET() {
  const user = await getProductUser();
  const now = Math.floor(Date.now() / 1000);
  if (!user) {
    const entitlement = snapshotFor("free", "active", now);
    return Response.json({
      signed_in: false,
      entitlement,
      billing: billingConfigurationStatus(),
    }, { headers: { "Cache-Control": "private, no-store" } });
  }

  try {
    const id = await billingUserId(user);
    await upsertBillingUser({ id, email: user.email, displayName: user.displayName, identityProvider: user.provider, identitySubject: user.subject });
    const manualGrant = await getActiveManualEntitlement(id, now);
    const preauthorizedGrant = await claimActivePreauthorizedEntitlement({ userId: id, email: user.email, nowSeconds: now });
    const subscription = await getSubscriptionForUser(id);
    const administratorAccess = resolveAdministratorAccess(isProductAdmin(user), now, commercialManifest.browser_grace_days);
    const manualAccess = resolveManualAccess(manualGrant, now, commercialManifest.browser_grace_days);
    const preauthorizedAccess = resolveManualAccess(preauthorizedGrant, now, commercialManifest.browser_grace_days);
    const access = administratorAccess ?? manualAccess ?? preauthorizedAccess ?? resolveBillingAccess(subscription, now, commercialManifest.browser_grace_days);
    const source = administratorAccess ? "administrator" : manualAccess ? "manual-grant" : preauthorizedAccess ? "preauthorized-email" : "subscription-ledger";
    const entitlement = snapshotFor(access.plan, access.status, access.offlineExpiresAt, source);
    let entitlementToken: string | undefined;
    try {
      entitlementToken = await signEntitlementSnapshot(entitlement);
    } catch (error) {
      if (access.plan !== "free") throw error;
    }
    return Response.json({
      signed_in: true,
      user: { display_name: user.displayName },
      entitlement,
      entitlement_token: entitlementToken,
      billing: {
        ...billingConfigurationStatus(),
        subscription_status: subscription?.status ?? null,
        current_period_end: subscription?.currentPeriodEnd ?? null,
        cancel_at_period_end: subscription?.cancelAtPeriodEnd ?? false,
        manual_grant_expires_at: manualGrant?.expiresAt ?? null,
        preauthorized_grant_expires_at: preauthorizedGrant?.expiresAt ?? null,
      },
    }, { headers: { "Cache-Control": "private, no-store" } });
  } catch (error) {
    console.error("Entitlement resolution failed.", error);
    return Response.json({ error: "Entitlement service unavailable." }, {
      status: 503,
      headers: { "Cache-Control": "private, no-store" },
    });
  }
}

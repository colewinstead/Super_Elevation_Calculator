import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { getProductUser } from "../product-auth";
import { adminConfigurationStatus, isProductAdmin } from "@/lib/auth/admin";
import { listManualEntitlements } from "@/lib/billing/manual-entitlements";
import { listPreauthorizedEntitlements } from "@/lib/billing/preauthorized-entitlements";
import { emptyUsageAnalytics, loadUsageAnalytics } from "@/lib/analytics/store";
import AdminEntitlementsClient from "./AdminEntitlementsClient";

export const metadata: Metadata = { title: "Site Administration" };
export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const user = await getProductUser();
  if (!user) redirect("/login?return_to=%2Fadmin");
  const adminStatus = adminConfigurationStatus();
  const allowed = adminStatus.configured && isProductAdmin(user);
  const [grants, preauthorizations, analytics] = allowed
    ? await Promise.all([listManualEntitlements(), listPreauthorizedEntitlements(), loadUsageAnalytics().catch(() => emptyUsageAnalytics())])
    : [[], [], emptyUsageAnalytics()];
  return (
    <main className="admin-shell">
      <nav className="legal-nav" aria-label="Administration navigation">
        <Link href="/">Superelevation Calculator</Link>
        <div><Link href="/calculator">Calculator</Link><Link href="/account">Account</Link></div>
      </nav>
      <header className="admin-heading">
        <p className="marketing-eyebrow"><span /> Owner controls</p>
        <h1>Site administration</h1>
        <p>Review anonymous calculator activity and manage complimentary professional access.</p>
      </header>
      {allowed
        ? <AdminEntitlementsClient initialGrants={grants} initialPreauthorizations={preauthorizations} initialAnalytics={analytics} />
        : <section className="admin-card admin-access-denied"><h2>Administrator access is not enabled for this account</h2><p>Your signed-in WorkOS user ID must be added to the private administrator allowlist. No customer or entitlement data was shown.</p><Link className="marketing-button secondary-action" href="/account">Return to account</Link></section>}
    </main>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { getProductUser } from "../product-auth";
import { adminConfigurationStatus, isProductAdmin } from "@/lib/auth/admin";
import { listManualEntitlements } from "@/lib/billing/manual-entitlements";
import { listPreauthorizedEntitlements } from "@/lib/billing/preauthorized-entitlements";
import AdminEntitlementsClient from "./AdminEntitlementsClient";

export const metadata: Metadata = { title: "Pro Access Administration" };
export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const user = await getProductUser();
  if (!user) redirect("/login?return_to=%2Fadmin");
  const adminStatus = adminConfigurationStatus();
  const allowed = adminStatus.configured && isProductAdmin(user);
  const [grants, preauthorizations] = allowed
    ? await Promise.all([listManualEntitlements(), listPreauthorizedEntitlements()])
    : [[], []];
  return (
    <main className="admin-shell">
      <nav className="legal-nav" aria-label="Administration navigation">
        <Link href="/">Superelevation Calculator</Link>
        <div><Link href="/calculator">Calculator</Link><Link href="/account">Account</Link></div>
      </nav>
      <header className="admin-heading">
        <p className="marketing-eyebrow"><span /> Owner controls</p>
        <h1>Pro access administration</h1>
        <p>Grant or revoke complimentary professional access without collecting payment.</p>
      </header>
      {allowed
        ? <AdminEntitlementsClient initialGrants={grants} initialPreauthorizations={preauthorizations} />
        : <section className="admin-card admin-access-denied"><h2>Administrator access is not enabled for this account</h2><p>Your signed-in WorkOS user ID must be added to the private administrator allowlist. No customer or entitlement data was shown.</p><Link className="marketing-button secondary-action" href="/account">Return to account</Link></section>}
    </main>
  );
}

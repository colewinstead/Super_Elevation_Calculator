import type { Metadata } from "next";
import Link from "next/link";
import { signOut } from "@workos-inc/authkit-nextjs";
import { getProductUser } from "../product-auth";
import { isProductAdmin } from "@/lib/auth/admin";
import AccountClient from "./AccountClient";

export const metadata: Metadata = { title: "Account and Billing" };
export const dynamic = "force-dynamic";

export default async function AccountPage({
  searchParams,
}: {
  searchParams: Promise<{ checkout?: string }>;
}) {
  const user = await getProductUser();
  const { checkout } = await searchParams;
  return (
    <main className="account-shell">
      <nav className="legal-nav" aria-label="Account navigation">
        <Link href="/">Superelevation Calculator</Link>
        <div><Link href="/calculator">Calculator</Link><Link href="/terms">Terms</Link><Link href="/privacy">Privacy</Link>{user && isProductAdmin(user) && <Link href="/admin">Admin</Link>}{user && <form action={async () => { "use server"; await signOut({ returnTo: "/" }); }}><button className="legal-nav-button" type="submit">Sign out</button></form>}</div>
      </nav>
      <header className="account-heading"><p className="marketing-eyebrow"><span /> Named-user access</p><h1>Account & billing</h1><p>Identity and entitlement are verified online. Engineering work remains local.</p></header>
      {user
        ? <AccountClient checkoutState={checkout} />
        : <section className="account-card signed-out-card"><h2>Sign in to manage Pro</h2><p>Free manual calculations do not require an account. Sign in only when you want to purchase or manage Pro.</p><Link className="marketing-button primary-action" href="/login">Sign in securely</Link><Link className="marketing-button secondary-action" href="/calculator">Keep calculating free</Link></section>}
    </main>
  );
}

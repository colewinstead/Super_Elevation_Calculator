import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { getProductUser } from "../product-auth";
import { authenticationConfigurationStatus } from "@/lib/auth/config";

export const metadata: Metadata = { title: "Sign in" };
export const dynamic = "force-dynamic";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ setup?: string }>;
}) {
  if (await getProductUser()) redirect("/account");
  const { setup } = await searchParams;
  const auth = authenticationConfigurationStatus();
  return (
    <main className="login-shell">
      <nav className="legal-nav" aria-label="Sign-in navigation">
        <Link href="/">Superelevation Calculator</Link>
        <div><Link href="/calculator">Calculator</Link><Link href="/#plans">Plans</Link></div>
      </nav>
      <section className="login-card">
        <div className="login-mark" aria-hidden="true">SE</div>
        <p className="marketing-eyebrow"><span /> Secure account access</p>
        <h1>Sign in to Superelevation Calculator</h1>
        <p>Use your work email, Microsoft account, or Google account. Free manual calculations never require an account.</p>
        {auth.configured
          ? <Link className="marketing-button primary-action" href="/auth/sign-in?return_to=%2Faccount">Continue securely</Link>
          : <div className="activation-banner neutral" role="status"><strong>Sign-in setup is in progress</strong><span>No account or payment can be created yet. Free calculations remain available.</span></div>}
        {setup === "required" && <p className="billing-notice">The identity service has not been connected. No information was transmitted.</p>}
        <Link className="marketing-button secondary-action" href="/calculator">Keep calculating free</Link>
        <p className="login-privacy">Identity verification receives account details only. Engineering files and calculations stay on this device.</p>
      </section>
    </main>
  );
}

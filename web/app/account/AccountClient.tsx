"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { PRIVACY_VERSION, PRO_PRICE, TERMS_VERSION } from "@/lib/billing/legal";

type AccountState = {
  signed_in: boolean;
  user?: { display_name: string };
  entitlement: { plan: "free" | "pro" | "team"; status: string; source?: string };
  billing: {
    configured: boolean;
    mode: "test" | "live";
    reason?: string | null;
    subscription_status?: string | null;
    current_period_end?: number | null;
    cancel_at_period_end?: boolean;
    manual_grant_expires_at?: number | null;
    preauthorized_grant_expires_at?: number | null;
  };
};

async function postForRedirect(path: string, body?: object) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : "{}",
  });
  const payload = await response.json() as { url?: string; error?: string };
  if (!response.ok || !payload.url) throw new Error(payload.error || "Billing is temporarily unavailable.");
  window.location.assign(payload.url);
}

export default function AccountClient({ checkoutState }: { checkoutState?: string }) {
  const [account, setAccount] = useState<AccountState | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const response = await fetch("/api/entitlement", {
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) throw new Error("Account status is temporarily unavailable.");
    setAccount(await response.json() as AccountState);
    setError("");
  }, []);

  useEffect(() => {
    let stopped = false;
    let attempts = checkoutState === "success" ? 12 : 1;
    const poll = async () => {
      try {
        await refresh();
      } catch (reason) {
        if (!stopped) setError(reason instanceof Error ? reason.message : String(reason));
      }
      attempts -= 1;
      if (!stopped && attempts > 0) window.setTimeout(poll, 2500);
    };
    poll();
    return () => { stopped = true; };
  }, [checkoutState, refresh]);

  const startCheckout = async () => {
    setBusy("Opening secure checkout…");
    setError("");
    try {
      await postForRedirect("/api/billing/checkout", {
        accepted,
        terms_version: TERMS_VERSION,
        privacy_version: PRIVACY_VERSION,
        checkout_attempt_id: crypto.randomUUID(),
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
      setBusy("");
    }
  };

  const manageBilling = async () => {
    setBusy("Opening billing portal…");
    setError("");
    try {
      await postForRedirect("/api/billing/portal");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
      setBusy("");
    }
  };

  if (!account && error) return (
    <div className="account-loading account-load-error" role="alert">
      <strong>Account status is temporarily unavailable.</strong>
      <span>Your access check did not finish. No calculator inputs, results, or project files were changed.</span>
      <div>
        <button className="marketing-button primary-action" type="button" onClick={() => {
          setError("");
          refresh().catch((reason) => setError(reason instanceof Error ? reason.message : String(reason)));
        }}>Retry account check</button>
        <Link className="marketing-button secondary-action" href="/calculator">Open calculator</Link>
      </div>
    </div>
  );
  if (!account) return <div className="account-loading" role="status">Checking account and entitlement…</div>;
  const isPro = account.entitlement.plan === "pro" || account.entitlement.plan === "team";
  const isManual = account.entitlement.source === "manual-grant";
  const isAdministrator = account.entitlement.source === "administrator";
  const isPreauthorized = account.entitlement.source === "preauthorized-email";
  const accessEnd = isManual
    ? account.billing.manual_grant_expires_at
    : isPreauthorized
      ? account.billing.preauthorized_grant_expires_at
      : account.billing.current_period_end;
  const periodEnd = accessEnd
    ? new Date(accessEnd * 1000).toLocaleDateString()
    : null;

  return (
    <div className="account-grid">
      <section className="account-card account-status-card">
        <p className="marketing-eyebrow"><span /> Account status</p>
        <h2>{isPro ? "Pro is active" : "Free plan"}</h2>
        <p>{isPro
          ? `Professional workflows are available${periodEnd ? ` through ${periodEnd}` : ""}.`
          : "Manual MDOT calculations remain available without payment."}</p>
        <dl>
          <div><dt>Plan</dt><dd>{account.entitlement.plan.toUpperCase()}</dd></div>
          <div><dt>Entitlement</dt><dd>{account.entitlement.status}</dd></div>
          {isAdministrator && <div><dt>Access</dt><dd>Administrator Pro</dd></div>}
          {isManual && <div><dt>Access</dt><dd>Complimentary Pro</dd></div>}
          {isPreauthorized && <div><dt>Access</dt><dd>Preauthorized Pro</dd></div>}
          {account.billing.subscription_status && <div><dt>Subscription</dt><dd>{account.billing.subscription_status}</dd></div>}
          {account.billing.cancel_at_period_end && <div><dt>Renewal</dt><dd>Cancels after paid period</dd></div>}
        </dl>
        {isPro && account.billing.subscription_status && <button className="marketing-button primary-action" onClick={manageBilling} disabled={Boolean(busy)}>{busy || "Manage billing"}</button>}
      </section>

      {!isPro && <section className="account-card checkout-card">
        <p className="marketing-eyebrow"><span /> Upgrade</p>
        <h2>Start Pro</h2>
        <strong className="account-price">{PRO_PRICE.display}<small> USD · renews monthly</small></strong>
        <ul><li>LandXML and multiple curves</li><li>All supported DOT profiles</li><li>Project files, PDF, ORD CSV, and DXF</li><li>Seven-day offline entitlement grace</li></ul>
        <label className="legal-acceptance"><input type="checkbox" checked={accepted} onChange={(event) => setAccepted(event.target.checked)} /><span>I agree to the <Link href="/terms" target="_blank">Terms of Service</Link> and acknowledge the <Link href="/privacy" target="_blank">Privacy Policy</Link>. Pro renews monthly until canceled. Payments are nonrefundable except where required by law.</span></label>
        <button className="marketing-button primary-action" onClick={startCheckout} disabled={!accepted || !account.billing.configured || Boolean(busy)}>{busy || `Continue to Stripe · ${PRO_PRICE.display}`}</button>
        {!account.billing.configured && <p className="billing-notice">Secure checkout is not connected yet. No payment can be submitted.</p>}
        {account.billing.configured && account.billing.mode === "test" && <p className="billing-notice">Stripe test mode is active. Test cards only; no real charge will be created.</p>}
      </section>}

      <section className="account-card local-data-card">
        <p className="marketing-eyebrow"><span /> Local by design</p>
        <h2>Billing never receives project files.</h2>
        <p>Stripe receives payment and billing details. The entitlement service receives account, plan, and status information. LandXML, calculations, projects, PDFs, CSVs, and DXFs stay on your device.</p>
        <Link href="/calculator" className="marketing-button secondary-action">Open calculator</Link>
      </section>

      {checkoutState === "success" && !isPro && <div className="activation-banner" role="status"><strong>Activating Pro</strong><span>Payment confirmation is being verified. This page will refresh automatically—do not pay again.</span></div>}
      {checkoutState === "canceled" && <div className="activation-banner neutral" role="status"><strong>Checkout canceled</strong><span>No plan change was made and no calculator work was affected.</span></div>}
      {error && <div className="activation-banner error" role="alert"><strong>Action needed</strong><span>{error}</span><button onClick={refresh}>Retry</button></div>}
    </div>
  );
}

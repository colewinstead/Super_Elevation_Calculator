"use client";

import { FormEvent, useCallback, useState } from "react";

export type GrantRecord = {
  id: string;
  userId: string;
  email: string;
  displayName: string | null;
  reason: string;
  expiresAt: number | null;
  grantedAt: string;
  revokedAt: string | null;
  status: "active" | "expired" | "revoked";
};

export type PreauthorizationRecord = {
  id: string;
  email: string;
  reason: string;
  expiresAt: number | null;
  grantedAt: string;
  claimedAt: string | null;
  revokedAt: string | null;
  status: "pending" | "claimed" | "expired" | "revoked";
};

function formatDate(value: number | string | null) {
  if (value === null) return "No expiration";
  const date = typeof value === "number" ? new Date(value * 1000) : new Date(value);
  return Number.isNaN(date.valueOf()) ? "Unknown" : date.toLocaleString();
}

export default function AdminEntitlementsClient({
  initialGrants,
  initialPreauthorizations,
}: {
  initialGrants: GrantRecord[];
  initialPreauthorizations: PreauthorizationRecord[];
}) {
  const [grants, setGrants] = useState<GrantRecord[]>(initialGrants);
  const [preauthorizations, setPreauthorizations] = useState<PreauthorizationRecord[]>(initialPreauthorizations);
  const [email, setEmail] = useState("");
  const [reason, setReason] = useState("Complimentary access");
  const [expiresAt, setExpiresAt] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    const response = await fetch("/api/admin/entitlements", { cache: "no-store" });
    const payload = await response.json() as { grants?: GrantRecord[]; preauthorizations?: PreauthorizationRecord[]; error?: string };
    if (!response.ok) throw new Error(payload.error || "Unable to load complimentary access records.");
    setGrants(payload.grants || []);
    setPreauthorizations(payload.preauthorizations || []);
  }, []);

  async function submit(action: "grant" | "revoke", event?: FormEvent) {
    event?.preventDefault();
    setBusy(true);
    setNotice("");
    try {
      const expires = expiresAt ? Math.floor(new Date(expiresAt).getTime() / 1000) : null;
      const response = await fetch("/api/admin/entitlements", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, email, reason, expires_at: expires, acceptance_confirmed: accepted }),
      });
      const payload = await response.json() as { message?: string; error?: string };
      if (!response.ok) throw new Error(payload.error || "The access change was not saved.");
      setNotice(payload.message || "Access updated.");
      if (action === "grant") { setAccepted(false); setExpiresAt(""); }
      await refresh();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "The access change was not saved.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="admin-grid">
      <section className="admin-card">
        <h2>Grant complimentary Pro</h2>
        <p>Enter the exact verified work email. If no account exists yet, Pro is preauthorized and activates after the first matching WorkOS sign-in.</p>
        <form className="admin-form" onSubmit={(event) => submit("grant", event)}>
          <label>Customer account email<input type="email" required value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="off" /></label>
          <label>Reason<input type="text" required minLength={3} maxLength={200} value={reason} onChange={(event) => setReason(event.target.value)} /></label>
          <label>Expiration <span>(optional)</span><input type="datetime-local" value={expiresAt} onChange={(event) => setExpiresAt(event.target.value)} /></label>
          <label className="admin-confirm"><input type="checkbox" checked={accepted} onChange={(event) => setAccepted(event.target.checked)} /><span>I confirm the required customer Terms and Privacy acceptance is already on file.</span></label>
          <div className="admin-actions"><button className="marketing-button primary-action" disabled={busy} type="submit">Grant Pro</button><button className="marketing-button danger-action" disabled={busy || !email} type="button" onClick={() => submit("revoke")}>Revoke Pro access</button></div>
        </form>
        {notice && <p className="admin-notice" role="status" aria-live="polite">{notice}</p>}
      </section>
      <section className="admin-card admin-history">
        <div className="admin-card-heading"><div><h2>Preauthorized users</h2><p>Pending access activates only for the exact verified email listed here.</p></div></div>
        {preauthorizations.length === 0
          ? <p className="admin-empty">No users are waiting for their first sign-in.</p>
          : <div className="admin-table-wrap"><table><thead><tr><th>Email</th><th>Reason</th><th>Created</th><th>Expiration</th><th>Status</th></tr></thead><tbody>{preauthorizations.map((grant) => <tr key={grant.id}><td><strong>{grant.email}</strong></td><td>{grant.reason}</td><td>{formatDate(grant.grantedAt)}</td><td>{formatDate(grant.expiresAt)}</td><td><span className={`admin-status ${grant.status}`}>{grant.status}</span></td></tr>)}</tbody></table></div>}
      </section>
      <section className="admin-card admin-history admin-history-wide">
        <div className="admin-card-heading"><div><h2>Grant history</h2><p>Recent grants and revocations are retained for accountability.</p></div><button type="button" onClick={() => refresh().catch((error) => setNotice(error instanceof Error ? error.message : "Unable to refresh."))}>Refresh</button></div>
        {grants.length === 0
          ? <p className="admin-empty">No complimentary Pro grants have been recorded.</p>
          : <div className="admin-table-wrap"><table><thead><tr><th>Customer</th><th>Reason</th><th>Granted</th><th>Expiration</th><th>Status</th></tr></thead><tbody>{grants.map((grant) => <tr key={grant.id}><td><strong>{grant.displayName || grant.email}</strong><span>{grant.email}</span></td><td>{grant.reason}</td><td>{formatDate(grant.grantedAt)}</td><td>{formatDate(grant.expiresAt)}</td><td><span className={`admin-status ${grant.status}`}>{grant.status}</span></td></tr>)}</tbody></table></div>}
      </section>
      <aside className="admin-local-note"><strong>Engineering data stays separate.</strong><span>This page stores account, access, and audit details only. It cannot view customer project files, LandXML, calculations, or exports.</span></aside>
    </div>
  );
}

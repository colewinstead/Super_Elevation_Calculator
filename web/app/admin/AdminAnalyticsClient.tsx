"use client";

import { useState } from "react";
import type { AnalyticsReport } from "@/lib/analytics/store";

const CALCULATOR_LABELS = {
  superelevation: "Superelevation",
  crushed_stone_base: "Crushed stone base",
} as const;

function Metric({ label, value, note }: { label: string; value: number; note: string }) {
  return <article><span>{label}</span><strong>{value.toLocaleString()}</strong><small>{note}</small></article>;
}

export default function AdminAnalyticsClient({ initialReport }: { initialReport: AnalyticsReport }) {
  const [report, setReport] = useState(initialReport);
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setBusy(true);
    setNotice("");
    try {
      const response = await fetch("/api/admin/analytics", { cache: "no-store" });
      const payload = await response.json() as AnalyticsReport & { error?: string };
      if (!response.ok) throw new Error(payload.error || "Unable to load usage analytics.");
      setReport(payload);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to load usage analytics.");
    } finally {
      setBusy(false);
    }
  }

  const conversion = report.summary.openedSessions
    ? Math.round(report.summary.calculatingSessions / report.summary.openedSessions * 100)
    : 0;

  return (
    <section className="admin-card admin-analytics admin-history-wide">
      <div className="admin-card-heading"><div><h2>Calculator usage</h2><p>Anonymous, privacy-preserving activity from the last {report.days} days.</p></div><button type="button" disabled={busy} onClick={refresh}>{busy ? "Refreshing…" : "Refresh"}</button></div>
      {!report.available && <p className="admin-empty">Usage analytics are temporarily unavailable. Complimentary access controls remain available.</p>}
      {report.available && <><div className="admin-analytics-metrics">
        <Metric label="Opened sessions" value={report.summary.openedSessions} note="Browser sessions opening a calculator" />
        <Metric label="Calculating sessions" value={report.summary.calculatingSessions} note={`${conversion}% of opened sessions`} />
        <Metric label="Calculations" value={report.summary.calculations} note="Successful calculation states" />
        <Metric label="Exports" value={report.summary.exports} note="Successful PDF, CSV, or DXF exports" />
        <Metric label="Errors" value={report.summary.errors} note="Calculation runtime failures" />
      </div>
      <div className="admin-analytics-tables">
        <div className="admin-table-wrap"><table><caption>By calculator</caption><thead><tr><th>Calculator</th><th>Sessions</th><th>Calculating</th><th>Calculations</th><th>Exports</th><th>Errors</th></tr></thead><tbody>{report.calculators.length ? report.calculators.map((row) => <tr key={row.calculator}><td><strong>{CALCULATOR_LABELS[row.calculator]}</strong></td><td>{row.openedSessions}</td><td>{row.calculatingSessions}</td><td>{row.calculations}</td><td>{row.exports}</td><td>{row.errors}</td></tr>) : <tr><td colSpan={6}>No calculator usage has been recorded yet.</td></tr>}</tbody></table></div>
        <div className="admin-table-wrap"><table><caption>Recent days</caption><thead><tr><th>Date</th><th>Sessions</th><th>Calculations</th><th>Exports</th></tr></thead><tbody>{report.daily.slice(0, 14).map((row) => <tr key={row.day}><td><strong>{row.day}</strong></td><td>{row.openedSessions}</td><td>{row.calculations}</td><td>{row.exports}</td></tr>)}</tbody></table></div>
      </div></>}
      <p className="admin-analytics-privacy">No project names, engineering inputs, stationing, coordinates, uploaded files, calculated results, IP addresses, or browser details are stored. Daily anonymous identifiers and counters are deleted after 90 days.</p>
      {notice && <p className="admin-notice" role="status">{notice}</p>}
    </section>
  );
}

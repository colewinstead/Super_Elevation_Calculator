"use client";

import type { AnalyticsCalculator, AnalyticsEventName } from "./events";

const SESSION_KEY = "vericivil_usage_session";
let memorySessionToken = "";

function sessionToken() {
  if (memorySessionToken) return memorySessionToken;
  try {
    const existing = window.sessionStorage.getItem(SESSION_KEY);
    if (existing) return (memorySessionToken = existing);
    const created = window.crypto.randomUUID();
    window.sessionStorage.setItem(SESSION_KEY, created);
    return (memorySessionToken = created);
  } catch {
    return (memorySessionToken ||= window.crypto.randomUUID());
  }
}

export function trackCalculatorEvent(
  calculator: AnalyticsCalculator,
  event: AnalyticsEventName,
  detail = "",
) {
  if (typeof window === "undefined" || navigator.doNotTrack === "1") return;
  const body = JSON.stringify({ session_token: sessionToken(), calculator, event, detail });
  void fetch("/api/analytics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    credentials: "same-origin",
    keepalive: true,
  }).catch(() => undefined);
}

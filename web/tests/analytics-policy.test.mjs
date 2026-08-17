import assert from "node:assert/strict";
import test from "node:test";
import { parseAnalyticsEvent } from "../lib/analytics/events.ts";

const base = {
  session_token: "018f47a2-9b2d-7cc1-8db1-6e9f8f81b218",
  calculator: "superelevation",
};

test("analytics accepts only bounded product events", () => {
  assert.deepEqual(parseAnalyticsEvent({ ...base, event: "calculation_completed", detail: "" }), {
    sessionToken: base.session_token,
    calculator: "superelevation",
    event: "calculation_completed",
    detail: "",
  });
  assert.equal(parseAnalyticsEvent({ ...base, event: "export_completed", detail: "pdf" })?.detail, "pdf");
  assert.equal(parseAnalyticsEvent({ ...base, calculator: "crushed_stone_base", event: "calculator_opened", detail: "" })?.calculator, "crushed_stone_base");
});

test("analytics rejects engineering inputs and unbounded details", () => {
  assert.equal(parseAnalyticsEvent({ ...base, event: "calculation_completed", detail: "55 mph" }), null);
  assert.equal(parseAnalyticsEvent({ ...base, event: "calculation_completed", detail: "", radius: 1450 }), null);
  assert.equal(parseAnalyticsEvent({ ...base, event: "export_completed", detail: "project-name.pdf" }), null);
  assert.equal(parseAnalyticsEvent({ ...base, event: "unknown", detail: "" }), null);
  assert.equal(parseAnalyticsEvent({ ...base, session_token: "not-a-session", event: "calculator_opened", detail: "" }), null);
});

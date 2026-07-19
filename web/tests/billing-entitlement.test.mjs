import assert from "node:assert/strict";
import test from "node:test";
import { resolveBillingAccess } from "../lib/billing/entitlement-policy.ts";
import { billingUserId } from "../lib/billing/identity.ts";

const now = 2_000_000_000;

test("Free is the default when no subscription exists", () => {
  assert.deepEqual(resolveBillingAccess(null, now), {
    plan: "free",
    status: "active",
    offlineExpiresAt: now,
  });
});

test("Active and trialing subscriptions grant identical Pro access", () => {
  for (const status of ["active", "trialing"]) {
    assert.deepEqual(resolveBillingAccess({
      status,
      currentPeriodEnd: now + 30 * 86400,
      graceUntil: now + 37 * 86400,
      cancelAtPeriodEnd: status === "active",
    }, now), {
      plan: "pro",
      status: "active",
      offlineExpiresAt: now + 7 * 86400,
    });
  }
});

test("Payment failure and cancellation use a bounded grace period", () => {
  const graceUntil = now + 3 * 86400;
  for (const status of ["past_due", "unpaid", "canceled"]) {
    assert.deepEqual(resolveBillingAccess({
      status,
      currentPeriodEnd: now - 86400,
      graceUntil,
      cancelAtPeriodEnd: false,
    }, now), {
      plan: "pro",
      status: "grace",
      offlineExpiresAt: graceUntil,
    });
  }
});

test("Expired grace fails closed to Free without changing calculation input", () => {
  const engineeringInput = Object.freeze({ profile: "mdot-rdsd-2026-04-22", radius: 1450, speed: 55 });
  const before = JSON.stringify(engineeringInput);
  const access = resolveBillingAccess({
    status: "canceled",
    currentPeriodEnd: now - 10 * 86400,
    graceUntil: now - 3 * 86400,
    cancelAtPeriodEnd: false,
  }, now);
  assert.equal(access.plan, "free");
  assert.equal(JSON.stringify(engineeringInput), before);
});

test("Billing identity follows the WorkOS subject instead of a changeable email address", async () => {
  const original = {
    provider: "workos",
    subject: "user_01JABC123",
    displayName: "Roadway Engineer",
    email: "first@example.com",
    fullName: "Roadway Engineer",
  };
  const renamed = { ...original, email: "updated@example.com" };
  const otherAccount = { ...renamed, subject: "user_01JXYZ789" };
  assert.equal(await billingUserId(original), await billingUserId(renamed));
  assert.notEqual(await billingUserId(original), await billingUserId(otherAccount));
});

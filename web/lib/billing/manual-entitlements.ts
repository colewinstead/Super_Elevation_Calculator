import { and, desc, eq, gt, isNull, or } from "drizzle-orm";
import { getDb } from "@/db";
import { billingUsers, manualEntitlements } from "@/db/schema";

export async function findBillingUserByEmail(email: string) {
  const normalized = email.trim().toLowerCase();
  const [row] = await getDb().select().from(billingUsers).where(eq(billingUsers.email, normalized)).limit(1);
  return row ?? null;
}

export async function getActiveManualEntitlement(userId: string, nowSeconds = Math.floor(Date.now() / 1000)) {
  const [row] = await getDb().select().from(manualEntitlements).where(and(
    eq(manualEntitlements.userId, userId),
    isNull(manualEntitlements.revokedAt),
    or(isNull(manualEntitlements.expiresAt), gt(manualEntitlements.expiresAt, nowSeconds)),
  )).orderBy(desc(manualEntitlements.grantedAt)).limit(1);
  return row ?? null;
}

export async function grantManualPro(input: {
  userId: string;
  reason: string;
  expiresAt: number | null;
  grantedBy: string;
  termsVersion: string;
  privacyVersion: string;
}) {
  const now = new Date().toISOString();
  const db = getDb();
  await db.batch([
    db.update(manualEntitlements).set({ revokedAt: now, revokedBy: input.grantedBy })
      .where(and(eq(manualEntitlements.userId, input.userId), isNull(manualEntitlements.revokedAt))),
    db.insert(manualEntitlements).values({
      id: crypto.randomUUID(),
      userId: input.userId,
      plan: "pro",
      reason: input.reason,
      expiresAt: input.expiresAt,
      grantedBy: input.grantedBy,
      termsVersion: input.termsVersion,
      privacyVersion: input.privacyVersion,
    }),
  ]);
}

export async function revokeManualPro(userId: string, revokedBy: string) {
  await getDb().update(manualEntitlements).set({
    revokedAt: new Date().toISOString(),
    revokedBy,
  }).where(and(eq(manualEntitlements.userId, userId), isNull(manualEntitlements.revokedAt)));
}

export async function listManualEntitlements() {
  const rows = await getDb().select({
    id: manualEntitlements.id,
    userId: manualEntitlements.userId,
    email: billingUsers.email,
    displayName: billingUsers.displayName,
    reason: manualEntitlements.reason,
    expiresAt: manualEntitlements.expiresAt,
    grantedAt: manualEntitlements.grantedAt,
    revokedAt: manualEntitlements.revokedAt,
  }).from(manualEntitlements)
    .innerJoin(billingUsers, eq(manualEntitlements.userId, billingUsers.id))
    .orderBy(desc(manualEntitlements.grantedAt))
    .limit(100);
  const now = Math.floor(Date.now() / 1000);
  return rows.map((row) => ({
    ...row,
    status: row.revokedAt ? "revoked" as const : row.expiresAt !== null && row.expiresAt <= now ? "expired" as const : "active" as const,
  }));
}

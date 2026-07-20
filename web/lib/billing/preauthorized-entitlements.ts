import { and, desc, eq, gt, isNull, or } from "drizzle-orm";
import { getDb } from "@/db";
import { preauthorizedEntitlements } from "@/db/schema";
import { normalizeEntitlementEmail } from "./preauthorization-policy";

function activeAt(nowSeconds: number) {
  return and(
    isNull(preauthorizedEntitlements.revokedAt),
    or(isNull(preauthorizedEntitlements.expiresAt), gt(preauthorizedEntitlements.expiresAt, nowSeconds)),
  );
}

export async function grantPreauthorizedPro(input: {
  email: string;
  reason: string;
  expiresAt: number | null;
  grantedBy: string;
  termsVersion: string;
  privacyVersion: string;
}) {
  const email = normalizeEntitlementEmail(input.email);
  const now = new Date().toISOString();
  const db = getDb();
  await db.batch([
    db.update(preauthorizedEntitlements).set({ revokedAt: now, revokedBy: input.grantedBy })
      .where(and(eq(preauthorizedEntitlements.email, email), isNull(preauthorizedEntitlements.revokedAt))),
    db.insert(preauthorizedEntitlements).values({
      id: crypto.randomUUID(),
      email,
      plan: "pro",
      reason: input.reason,
      expiresAt: input.expiresAt,
      grantedBy: input.grantedBy,
      termsVersion: input.termsVersion,
      privacyVersion: input.privacyVersion,
    }),
  ]);
}

export async function revokePreauthorizedPro(email: string, revokedBy: string) {
  await getDb().update(preauthorizedEntitlements).set({
    revokedAt: new Date().toISOString(),
    revokedBy,
  }).where(and(
    eq(preauthorizedEntitlements.email, normalizeEntitlementEmail(email)),
    isNull(preauthorizedEntitlements.revokedAt),
  ));
}

export async function claimActivePreauthorizedEntitlement(input: {
  userId: string;
  email: string;
  nowSeconds?: number;
}) {
  const nowSeconds = input.nowSeconds ?? Math.floor(Date.now() / 1000);
  const email = normalizeEntitlementEmail(input.email);
  const db = getDb();
  const [existingClaim] = await db.select().from(preauthorizedEntitlements).where(and(
    eq(preauthorizedEntitlements.claimedByUserId, input.userId),
    activeAt(nowSeconds),
  )).orderBy(desc(preauthorizedEntitlements.grantedAt)).limit(1);
  if (existingClaim) return existingClaim;

  const [pending] = await db.select().from(preauthorizedEntitlements).where(and(
    eq(preauthorizedEntitlements.email, email),
    isNull(preauthorizedEntitlements.claimedByUserId),
    activeAt(nowSeconds),
  )).orderBy(desc(preauthorizedEntitlements.grantedAt)).limit(1);
  if (!pending) return null;

  await db.update(preauthorizedEntitlements).set({
    claimedAt: new Date().toISOString(),
    claimedByUserId: input.userId,
  }).where(and(
    eq(preauthorizedEntitlements.id, pending.id),
    isNull(preauthorizedEntitlements.claimedByUserId),
    isNull(preauthorizedEntitlements.revokedAt),
  ));
  const [claimed] = await db.select().from(preauthorizedEntitlements)
    .where(and(eq(preauthorizedEntitlements.id, pending.id), eq(preauthorizedEntitlements.claimedByUserId, input.userId)))
    .limit(1);
  return claimed ?? null;
}

export async function listPreauthorizedEntitlements() {
  const rows = await getDb().select().from(preauthorizedEntitlements)
    .orderBy(desc(preauthorizedEntitlements.grantedAt))
    .limit(100);
  const now = Math.floor(Date.now() / 1000);
  return rows.map((row) => ({
    ...row,
    status: row.revokedAt
      ? "revoked" as const
      : row.expiresAt !== null && row.expiresAt <= now
        ? "expired" as const
        : row.claimedByUserId
          ? "claimed" as const
          : "pending" as const,
  }));
}

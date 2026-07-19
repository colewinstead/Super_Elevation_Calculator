import { desc, eq } from "drizzle-orm";
import { getDb } from "@/db";
import { billingUsers, legalAcceptances, stripeEvents, subscriptions } from "@/db/schema";

export type BillingUserRecord = typeof billingUsers.$inferSelect;
export type SubscriptionRecord = typeof subscriptions.$inferSelect;

export async function upsertBillingUser(input: {
  id: string;
  email: string;
  displayName: string;
}) {
  const db = getDb();
  await db.insert(billingUsers).values({
    id: input.id,
    email: input.email.trim().toLowerCase(),
    displayName: input.displayName,
  }).onConflictDoUpdate({
    target: billingUsers.id,
    set: {
      email: input.email.trim().toLowerCase(),
      displayName: input.displayName,
      updatedAt: new Date().toISOString(),
    },
  });
  return getBillingUser(input.id);
}

export async function getBillingUser(id: string) {
  const [row] = await getDb().select().from(billingUsers).where(eq(billingUsers.id, id)).limit(1);
  return row ?? null;
}

export async function getBillingUserByCustomer(stripeCustomerId: string) {
  const [row] = await getDb().select().from(billingUsers)
    .where(eq(billingUsers.stripeCustomerId, stripeCustomerId)).limit(1);
  return row ?? null;
}

export async function setStripeCustomer(id: string, stripeCustomerId: string) {
  await getDb().update(billingUsers).set({
    stripeCustomerId,
    updatedAt: new Date().toISOString(),
  }).where(eq(billingUsers.id, id));
}

export async function recordLegalAcceptance(input: {
  userId: string;
  termsVersion: string;
  privacyVersion: string;
}) {
  await getDb().insert(legalAcceptances).values({
    id: crypto.randomUUID(),
    userId: input.userId,
    termsVersion: input.termsVersion,
    privacyVersion: input.privacyVersion,
  });
}

export async function getSubscriptionForUser(userId: string) {
  const [row] = await getDb().select().from(subscriptions)
    .where(eq(subscriptions.userId, userId))
    .orderBy(desc(subscriptions.eventCreated))
    .limit(1);
  return row ?? null;
}

export async function upsertSubscription(input: typeof subscriptions.$inferInsert) {
  const [existing] = await getDb().select({ eventCreated: subscriptions.eventCreated })
    .from(subscriptions)
    .where(eq(subscriptions.stripeSubscriptionId, input.stripeSubscriptionId))
    .limit(1);
  if (existing && existing.eventCreated > input.eventCreated) return;
  await getDb().insert(subscriptions).values(input).onConflictDoUpdate({
    target: subscriptions.stripeSubscriptionId,
    set: {
      userId: input.userId,
      stripeCustomerId: input.stripeCustomerId,
      priceId: input.priceId,
      plan: input.plan,
      status: input.status,
      currentPeriodEnd: input.currentPeriodEnd,
      graceUntil: input.graceUntil,
      cancelAtPeriodEnd: input.cancelAtPeriodEnd,
      eventCreated: input.eventCreated,
      updatedAt: new Date().toISOString(),
    },
  });
}

export async function hasProcessedStripeEvent(eventId: string) {
  const [row] = await getDb().select({ id: stripeEvents.eventId }).from(stripeEvents)
    .where(eq(stripeEvents.eventId, eventId)).limit(1);
  return Boolean(row);
}

export async function markStripeEventProcessed(event: {
  id: string;
  type: string;
  created: number;
}) {
  await getDb().insert(stripeEvents).values({
    eventId: event.id,
    eventType: event.type,
    eventCreated: event.created,
  }).onConflictDoNothing();
}

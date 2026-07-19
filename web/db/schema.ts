import { sql } from "drizzle-orm";
import { index, integer, sqliteTable, text, uniqueIndex } from "drizzle-orm/sqlite-core";

export const billingUsers = sqliteTable("billing_users", {
  id: text("id").primaryKey(),
  email: text("email").notNull(),
  displayName: text("display_name"),
  stripeCustomerId: text("stripe_customer_id"),
  createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
}, (table) => [
  uniqueIndex("billing_users_email_idx").on(table.email),
  uniqueIndex("billing_users_stripe_customer_idx").on(table.stripeCustomerId),
]);

export const subscriptions = sqliteTable("subscriptions", {
  stripeSubscriptionId: text("stripe_subscription_id").primaryKey(),
  userId: text("user_id").notNull(),
  stripeCustomerId: text("stripe_customer_id").notNull(),
  priceId: text("price_id").notNull(),
  plan: text("plan").notNull().default("pro"),
  status: text("status").notNull(),
  currentPeriodEnd: integer("current_period_end").notNull(),
  graceUntil: integer("grace_until").notNull(),
  cancelAtPeriodEnd: integer("cancel_at_period_end", { mode: "boolean" }).notNull().default(false),
  eventCreated: integer("event_created").notNull(),
  updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
}, (table) => [
  index("subscriptions_user_idx").on(table.userId),
  index("subscriptions_customer_idx").on(table.stripeCustomerId),
]);

export const legalAcceptances = sqliteTable("legal_acceptances", {
  id: text("id").primaryKey(),
  userId: text("user_id").notNull(),
  termsVersion: text("terms_version").notNull(),
  privacyVersion: text("privacy_version").notNull(),
  acceptedAt: text("accepted_at").notNull().default(sql`CURRENT_TIMESTAMP`),
});

export const stripeEvents = sqliteTable("stripe_events", {
  eventId: text("event_id").primaryKey(),
  eventType: text("event_type").notNull(),
  eventCreated: integer("event_created").notNull(),
  processedAt: text("processed_at").notNull().default(sql`CURRENT_TIMESTAMP`),
});

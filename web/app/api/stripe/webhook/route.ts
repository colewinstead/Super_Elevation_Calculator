import Stripe from "stripe";
import { getBillingConfig } from "@/lib/billing/config";
import { billingRouteError } from "@/lib/billing/route-error";
import {
  getBillingUserByCustomer,
  hasProcessedStripeEvent,
  markStripeEventProcessed,
  upsertSubscription,
} from "@/lib/billing/store";
import {
  getStripe,
  stripeCustomerId,
  stripeSubscriptionPeriodEnd,
} from "@/lib/billing/stripe";

export const dynamic = "force-dynamic";

async function syncSubscription(subscription: Stripe.Subscription, eventCreated: number) {
  const customerId = stripeCustomerId(subscription.customer);
  if (!customerId) throw new Error("Stripe subscription is missing a customer.");
  const user = await getBillingUserByCustomer(customerId);
  const metadataUserId = subscription.metadata.internal_user_id;
  if (user && metadataUserId && user.id !== metadataUserId) {
    throw new Error("Stripe subscription identity does not match the billing customer.");
  }
  const userId = user?.id || metadataUserId;
  if (!userId) throw new Error("Stripe subscription is not mapped to a local user.");
  const periodEnd = stripeSubscriptionPeriodEnd(subscription);
  const priceId = subscription.items.data[0]?.price.id;
  if (!priceId) throw new Error("Stripe subscription is missing a price.");
  const expectedPriceId = getBillingConfig().proPriceId;
  const recognizedPrice = priceId === expectedPriceId;
  await upsertSubscription({
    stripeSubscriptionId: subscription.id,
    userId,
    stripeCustomerId: customerId,
    priceId,
    plan: recognizedPrice ? "pro" : "free",
    status: recognizedPrice ? subscription.status : "unrecognized_price",
    currentPeriodEnd: periodEnd,
    graceUntil: recognizedPrice ? periodEnd + 7 * 86400 : 0,
    cancelAtPeriodEnd: subscription.cancel_at_period_end,
    eventCreated,
  });
}

async function subscriptionFromEvent(event: Stripe.Event, stripe: Stripe) {
  if (event.type.startsWith("customer.subscription.")) {
    return event.data.object as Stripe.Subscription;
  }
  if (event.type === "checkout.session.completed") {
    const session = event.data.object as Stripe.Checkout.Session;
    const subscriptionId = typeof session.subscription === "string"
      ? session.subscription
      : session.subscription?.id;
    return subscriptionId ? stripe.subscriptions.retrieve(subscriptionId) : null;
  }
  if (event.type === "invoice.paid" || event.type === "invoice.payment_failed") {
    const invoice = event.data.object as Stripe.Invoice;
    const details = invoice.parent?.subscription_details;
    const subscriptionId = typeof details?.subscription === "string"
      ? details.subscription
      : details?.subscription?.id;
    return subscriptionId ? stripe.subscriptions.retrieve(subscriptionId) : null;
  }
  return null;
}

export async function POST(request: Request) {
  try {
    const signature = request.headers.get("stripe-signature");
    if (!signature) return new Response("Missing Stripe signature.", { status: 400 });
    const rawBody = await request.text();
    const config = getBillingConfig();
    const stripe = getStripe();
    const event = await stripe.webhooks.constructEventAsync(
      rawBody,
      signature,
      config.webhookSecret,
      undefined,
      Stripe.createSubtleCryptoProvider(),
    );
    if (await hasProcessedStripeEvent(event.id)) return Response.json({ received: true, duplicate: true });
    const subscription = await subscriptionFromEvent(event, stripe);
    if (subscription) await syncSubscription(subscription, event.created);
    await markStripeEventProcessed(event);
    return Response.json({ received: true });
  } catch (error) {
    const response = billingRouteError(error);
    return new Response(await response.text(), { status: response.status === 503 ? 400 : response.status });
  }
}

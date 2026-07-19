import { getChatGPTUser } from "@/app/chatgpt-auth";
import releaseInfo from "@/app/generated/release-info.json";
import { getBillingConfig } from "@/lib/billing/config";
import { billingUserId } from "@/lib/billing/identity";
import { PRIVACY_VERSION, TERMS_VERSION } from "@/lib/billing/legal";
import { requireSameOrigin, safeReturnOrigin } from "@/lib/billing/request-security";
import { billingRouteError } from "@/lib/billing/route-error";
import {
  getSubscriptionForUser,
  recordLegalAcceptance,
  setStripeCustomer,
  upsertBillingUser,
} from "@/lib/billing/store";
import { getStripe, verifyConfiguredProPrice } from "@/lib/billing/stripe";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    requireSameOrigin(request);
    const user = await getChatGPTUser();
    if (!user) return Response.json({ error: "Sign in before starting Pro." }, { status: 401 });

    const body = await request.json() as {
      accepted?: boolean;
      terms_version?: string;
      privacy_version?: string;
      checkout_attempt_id?: string;
    };
    if (!body.accepted || body.terms_version !== TERMS_VERSION || body.privacy_version !== PRIVACY_VERSION) {
      return Response.json({ error: "Accept the current Terms and Privacy Policy before checkout." }, { status: 400 });
    }
    if (!body.checkout_attempt_id || !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu.test(body.checkout_attempt_id)) {
      return Response.json({ error: "Start a new secure checkout attempt." }, { status: 400 });
    }

    const id = await billingUserId(user);
    const billingUser = await upsertBillingUser({ id, email: user.email, displayName: user.displayName });
    if (!billingUser) throw new Error("Billing storage is unavailable.");
    const existingSubscription = await getSubscriptionForUser(id);
    if (existingSubscription && ["active", "trialing", "past_due"].includes(existingSubscription.status)) {
      return Response.json({ error: "This account already has a Pro subscription. Use Manage billing instead." }, { status: 409 });
    }

    const config = getBillingConfig();
    const stripe = getStripe();
    await verifyConfiguredProPrice(stripe, config.proPriceId);

    let customerId = billingUser.stripeCustomerId;
    if (!customerId) {
      const customer = await stripe.customers.create({
        email: user.email,
        name: user.fullName || undefined,
        metadata: { internal_user_id: id },
      }, { idempotencyKey: `customer:${id}` });
      customerId = customer.id;
      await setStripeCustomer(id, customerId);
    }

    await recordLegalAcceptance({
      userId: id,
      termsVersion: TERMS_VERSION,
      privacyVersion: PRIVACY_VERSION,
    });

    const origin = safeReturnOrigin(request);
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      customer: customerId,
      client_reference_id: id,
      line_items: [{ price: config.proPriceId, quantity: 1 }],
      allow_promotion_codes: false,
      billing_address_collection: "auto",
      customer_update: { address: "auto", name: "auto" },
      metadata: {
        internal_user_id: id,
        plan: "pro",
        terms_version: TERMS_VERSION,
        privacy_version: PRIVACY_VERSION,
        application_version: releaseInfo.application_version,
        calculation_engine_version: releaseInfo.calculation_engine_version,
      },
      subscription_data: { metadata: {
        internal_user_id: id,
        plan: "pro",
        application_version: releaseInfo.application_version,
        calculation_engine_version: releaseInfo.calculation_engine_version,
      } },
      success_url: `${origin}/account?checkout=success`,
      cancel_url: `${origin}/account?checkout=canceled`,
    }, { idempotencyKey: `checkout:${id}:${body.checkout_attempt_id}` });
    if (!session.url) throw new Error("Stripe did not return a checkout URL.");
    return Response.json({ url: session.url });
  } catch (error) {
    return billingRouteError(error);
  }
}

import { getChatGPTUser } from "@/app/chatgpt-auth";
import { billingUserId } from "@/lib/billing/identity";
import { requireSameOrigin, safeReturnOrigin } from "@/lib/billing/request-security";
import { billingRouteError } from "@/lib/billing/route-error";
import { getBillingUser } from "@/lib/billing/store";
import { getStripe } from "@/lib/billing/stripe";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    requireSameOrigin(request);
    const user = await getChatGPTUser();
    if (!user) return Response.json({ error: "Sign in to manage billing." }, { status: 401 });
    const record = await getBillingUser(await billingUserId(user));
    if (!record?.stripeCustomerId) {
      return Response.json({ error: "No billing account was found." }, { status: 404 });
    }
    const session = await getStripe().billingPortal.sessions.create({
      customer: record.stripeCustomerId,
      return_url: `${safeReturnOrigin(request)}/account`,
    });
    return Response.json({ url: session.url });
  } catch (error) {
    return billingRouteError(error);
  }
}

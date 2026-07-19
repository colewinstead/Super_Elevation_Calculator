import { getProductUser } from "@/app/product-auth";
import { isProductAdmin } from "@/lib/auth/admin";
import { TERMS_VERSION, PRIVACY_VERSION } from "@/lib/billing/legal";
import { billingUserId } from "@/lib/billing/identity";
import { requireSameOrigin } from "@/lib/billing/request-security";
import {
  findBillingUserByEmail,
  grantManualPro,
  listManualEntitlements,
  revokeManualPro,
} from "@/lib/billing/manual-entitlements";

export const dynamic = "force-dynamic";

async function authorizedAdmin() {
  const user = await getProductUser();
  return user && isProductAdmin(user) ? user : null;
}

function adminRouteError(error: unknown) {
  if (error instanceof Response) return error;
  return Response.json({ error: "Administration is temporarily unavailable. No access change was made." }, { status: 503 });
}

export async function GET() {
  try {
    if (!await authorizedAdmin()) return Response.json({ error: "Not authorized." }, { status: 403 });
    return Response.json({ grants: await listManualEntitlements() }, { headers: { "Cache-Control": "private, no-store" } });
  } catch (error) {
    return adminRouteError(error);
  }
}

export async function POST(request: Request) {
  try {
    requireSameOrigin(request);
  const admin = await authorizedAdmin();
  if (!admin) return Response.json({ error: "Not authorized." }, { status: 403 });
  const body = await request.json() as {
    action?: string;
    email?: string;
    reason?: string;
    expires_at?: number | null;
    acceptance_confirmed?: boolean;
  };
  const email = body.email?.trim().toLowerCase() || "";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/u.test(email)) {
    return Response.json({ error: "Enter the customer's complete account email." }, { status: 400 });
  }
  const customer = await findBillingUserByEmail(email);
  if (!customer) {
    return Response.json({ error: "No account was found. Ask the customer to sign in once, then try again." }, { status: 404 });
  }
  const adminId = await billingUserId(admin);
  if (body.action === "revoke") {
    await revokeManualPro(customer.id, adminId);
    return Response.json({ ok: true, message: `Complimentary Pro was revoked for ${email}.` });
  }
  if (body.action !== "grant") return Response.json({ error: "Unsupported admin action." }, { status: 400 });
  const reason = body.reason?.trim() || "";
  if (reason.length < 3 || reason.length > 200) {
    return Response.json({ error: "Give a short reason between 3 and 200 characters." }, { status: 400 });
  }
  if (!body.acceptance_confirmed) {
    return Response.json({ error: "Confirm that the required customer acceptance is already on file." }, { status: 400 });
  }
  const expiresAt = body.expires_at === null || body.expires_at === undefined ? null : Number(body.expires_at);
  const now = Math.floor(Date.now() / 1000);
  if (expiresAt !== null && (!Number.isInteger(expiresAt) || expiresAt <= now)) {
    return Response.json({ error: "The expiration must be a future date and time." }, { status: 400 });
  }
  await grantManualPro({
    userId: customer.id,
    reason,
    expiresAt,
    grantedBy: adminId,
    termsVersion: TERMS_VERSION,
    privacyVersion: PRIVACY_VERSION,
  });
    return Response.json({ ok: true, message: `Complimentary Pro is active for ${email}.` });
  } catch (error) {
    return adminRouteError(error);
  }
}

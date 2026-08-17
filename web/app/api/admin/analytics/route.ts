import { getProductUser } from "@/app/product-auth";
import { isProductAdmin } from "@/lib/auth/admin";
import { loadUsageAnalytics } from "@/lib/analytics/store";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const user = await getProductUser();
    if (!user || !isProductAdmin(user)) return Response.json({ error: "Not authorized." }, { status: 403 });
    return Response.json(await loadUsageAnalytics(), { headers: { "Cache-Control": "private, no-store" } });
  } catch {
    return Response.json({ error: "Usage analytics are temporarily unavailable." }, { status: 503 });
  }
}

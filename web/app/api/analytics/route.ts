import { requireSameOrigin } from "@/lib/billing/request-security";
import { parseAnalyticsEvent } from "@/lib/analytics/events";
import { recordUsageEvent } from "@/lib/analytics/store";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    requireSameOrigin(request);
    const length = Number(request.headers.get("content-length") || 0);
    if (length > 1024) return Response.json({ error: "Invalid analytics event." }, { status: 400 });
    const event = parseAnalyticsEvent(await request.json());
    if (!event) return Response.json({ error: "Invalid analytics event." }, { status: 400 });
    await recordUsageEvent(event);
    return new Response(null, { status: 202, headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    if (error instanceof Response) return error;
    return Response.json({ error: "Usage event was not recorded." }, { status: 503 });
  }
}

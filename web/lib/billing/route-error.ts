export function billingRouteError(error: unknown) {
  if (error instanceof Response) return error;
  const message = error instanceof Error ? error.message : "Billing is temporarily unavailable.";
  const safe = message.includes("configured Stripe price")
    || message.includes("not been connected")
    || message.includes("locked")
    || message.includes("Billing storage")
    ? message
    : "Billing is temporarily unavailable. Your calculator work is unchanged.";
  return Response.json({ error: safe }, { status: 503 });
}

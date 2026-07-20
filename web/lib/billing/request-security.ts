export function requireSameOrigin(request: Request) {
  const origin = request.headers.get("origin");
  if (!origin || origin !== new URL(request.url).origin) {
    throw new Response("Cross-site request rejected.", { status: 403 });
  }
}

export function safeReturnOrigin(request: Request) {
  return new URL(request.url).origin;
}

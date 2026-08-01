export function GET(request: Request) {
  const incoming = new URL(request.url);
  const destination = new URL("/calculators/superelevation", incoming);
  destination.search = incoming.search;
  return Response.redirect(destination, 308);
}

import { getSignInUrl } from "@workos-inc/authkit-nextjs";
import { authenticationConfigurationStatus, safeAuthReturnPath } from "@/lib/auth/config";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const status = authenticationConfigurationStatus();
  if (!status.configured) {
    return Response.redirect(new URL("/login?setup=required", request.url));
  }
  const returnTo = safeAuthReturnPath(new URL(request.url).searchParams.get("return_to"));
  return Response.redirect(await getSignInUrl({ returnTo }));
}

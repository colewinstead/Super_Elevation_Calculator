import { handleAuth } from "@workos-inc/authkit-nextjs";

export const dynamic = "force-dynamic";
export const GET = handleAuth({ returnPathname: "/account" });

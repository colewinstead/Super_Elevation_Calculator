import { withAuth } from "@workos-inc/authkit-nextjs";
import { authenticationConfigurationStatus } from "@/lib/auth/config";

export type ProductUser = {
  provider: "workos";
  subject: string;
  displayName: string;
  email: string;
  fullName: string | null;
};

export async function getProductUser(): Promise<ProductUser | null> {
  if (!authenticationConfigurationStatus().configured) return null;
  const { user } = await withAuth();
  if (!user) return null;
  const fullName = [user.firstName, user.lastName].filter(Boolean).join(" ") || null;
  return {
    provider: "workos",
    subject: user.id,
    displayName: fullName || user.email,
    email: user.email,
    fullName,
  };
}

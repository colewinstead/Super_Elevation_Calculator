import { env } from "cloudflare:workers";
import type { ProductUser } from "@/app/product-auth";

type AdminRuntimeEnv = { ADMIN_WORKOS_USER_IDS?: string };

function configuredAdminSubjects() {
  const values = env as unknown as AdminRuntimeEnv;
  return new Set(
    (values.ADMIN_WORKOS_USER_IDS || process.env.ADMIN_WORKOS_USER_IDS || "")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean),
  );
}

export function isProductAdmin(user: ProductUser) {
  return configuredAdminSubjects().has(user.subject);
}

export function adminConfigurationStatus() {
  return { configured: configuredAdminSubjects().size > 0 } as const;
}

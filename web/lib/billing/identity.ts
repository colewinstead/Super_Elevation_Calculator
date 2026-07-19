import type { ProductUser } from "@/app/product-auth";

export async function billingUserId(user: ProductUser) {
  const identity = `${user.provider}:${user.subject}`;
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(identity));
  return `usr_${Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}

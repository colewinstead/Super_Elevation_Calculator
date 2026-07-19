import type { ChatGPTUser } from "@/app/chatgpt-auth";

export async function billingUserId(user: ChatGPTUser) {
  const normalized = user.email.trim().toLowerCase();
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(normalized));
  return `usr_${Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}

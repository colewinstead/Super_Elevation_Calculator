import { env } from "cloudflare:workers";

type AuthRuntimeEnv = {
  WORKOS_API_KEY?: string;
  WORKOS_CLIENT_ID?: string;
  WORKOS_COOKIE_PASSWORD?: string;
  NEXT_PUBLIC_WORKOS_REDIRECT_URI?: string;
};

export function authenticationConfigurationStatus() {
  const values = env as unknown as AuthRuntimeEnv;
  const configured = Boolean(
    (values.WORKOS_API_KEY || process.env.WORKOS_API_KEY)
      && (values.WORKOS_CLIENT_ID || process.env.WORKOS_CLIENT_ID)
      && (values.WORKOS_COOKIE_PASSWORD || process.env.WORKOS_COOKIE_PASSWORD)
      && (values.NEXT_PUBLIC_WORKOS_REDIRECT_URI || process.env.NEXT_PUBLIC_WORKOS_REDIRECT_URI),
  );
  return {
    configured,
    reason: configured ? null : "Branded sign-in has not been connected yet.",
  } as const;
}

export function safeAuthReturnPath(value: string | null, fallback = "/account") {
  if (!value?.startsWith("/") || value.startsWith("//")) return fallback;
  try {
    const url = new URL(value, "https://app.local");
    if (url.origin !== "https://app.local") return fallback;
    if (["/auth/callback", "/auth/sign-in", "/auth/sign-out"].includes(url.pathname)) return fallback;
    return `${url.pathname}${url.search}${url.hash}`;
  } catch {
    return fallback;
  }
}

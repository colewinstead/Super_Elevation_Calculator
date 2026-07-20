import { getEntitlementPrivateJwk } from "./config";

function base64Url(bytes: Uint8Array) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

export async function signEntitlementSnapshot(snapshot: object) {
  const privateJwk = JSON.parse(getEntitlementPrivateJwk()) as JsonWebKey;
  // RFC 8037 identifies Ed25519 JWKs with the EdDSA "alg" value. Normalize
  // legacy development keys before Web Crypto validates the curve.
  privateJwk.alg = "EdDSA";
  const key = await crypto.subtle.importKey("jwk", privateJwk, { name: "Ed25519" }, false, ["sign"]);
  const payload = base64Url(new TextEncoder().encode(JSON.stringify(snapshot)));
  const signature = await crypto.subtle.sign("Ed25519", key, new TextEncoder().encode(`v1.${payload}`));
  return `v1.${payload}.${base64Url(new Uint8Array(signature))}`;
}

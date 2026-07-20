export function normalizeEntitlementEmail(email: string) {
  return email.trim().toLowerCase();
}

export function matchesPreauthorizedEmail(authorizedEmail: string, signedInEmail: string) {
  return normalizeEntitlementEmail(authorizedEmail) === normalizeEntitlementEmail(signedInEmail);
}

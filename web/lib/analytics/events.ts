export const ANALYTICS_CALCULATORS = ["superelevation", "crushed_stone_base"] as const;
export const ANALYTICS_EVENTS = ["calculator_opened", "calculation_completed", "calculation_failed", "export_completed"] as const;

export type AnalyticsCalculator = typeof ANALYTICS_CALCULATORS[number];
export type AnalyticsEventName = typeof ANALYTICS_EVENTS[number];

export type AnalyticsEventInput = {
  sessionToken: string;
  calculator: AnalyticsCalculator;
  event: AnalyticsEventName;
  detail: string;
};

const ALLOWED_KEYS = new Set(["session_token", "calculator", "event", "detail"]);
const SESSION_TOKEN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu;

const EVENT_DETAILS: Record<AnalyticsEventName, ReadonlySet<string>> = {
  calculator_opened: new Set([""]),
  calculation_completed: new Set([""]),
  calculation_failed: new Set(["runtime"]),
  export_completed: new Set(["pdf", "csv", "dxf"]),
};

export function parseAnalyticsEvent(value: unknown): AnalyticsEventInput | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const body = value as Record<string, unknown>;
  if (Object.keys(body).some((key) => !ALLOWED_KEYS.has(key))) return null;
  const sessionToken = typeof body.session_token === "string" ? body.session_token.trim() : "";
  const calculator = typeof body.calculator === "string" ? body.calculator : "";
  const event = typeof body.event === "string" ? body.event : "";
  const detail = typeof body.detail === "string" ? body.detail : "";
  if (!SESSION_TOKEN.test(sessionToken)) return null;
  if (!ANALYTICS_CALCULATORS.includes(calculator as AnalyticsCalculator)) return null;
  if (!ANALYTICS_EVENTS.includes(event as AnalyticsEventName)) return null;
  if (!EVENT_DETAILS[event as AnalyticsEventName].has(detail)) return null;
  return {
    sessionToken,
    calculator: calculator as AnalyticsCalculator,
    event: event as AnalyticsEventName,
    detail,
  };
}

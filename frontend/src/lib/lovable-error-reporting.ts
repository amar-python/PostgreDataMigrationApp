// BUG-029: previously this always forwarded errors to a global
// window.__lovableEvents hook. Now gated on VITE_ENABLE_LOVABLE_ANALYTICS
// (default: false) so a self-hosted deployment doesn't leak stack traces to
// whatever code happens to define that global. Set the flag to "true" in
// frontend/.env only if you know you're on lovable.dev's platform and want
// their error-reporting integration.

type LovableErrorOptions = {
  mechanism?: "manual" | "onerror" | "unhandledrejection" | "react_error_boundary";
  handled?: boolean;
  severity?: "error" | "warning" | "info";
};

type LovableEvents = {
  captureException?: (
    error: unknown,
    context?: Record<string, unknown>,
    options?: LovableErrorOptions,
  ) => void;
};

declare global {
  interface Window {
    __lovableEvents?: LovableEvents;
  }
}

const ANALYTICS_ENABLED: boolean =
  (import.meta.env.VITE_ENABLE_LOVABLE_ANALYTICS as string | undefined) === "true";

export function reportLovableError(error: unknown, context: Record<string, unknown> = {}) {
  if (typeof window === "undefined") return;
  if (!ANALYTICS_ENABLED) return;
  window.__lovableEvents?.captureException?.(
    error,
    {
      source: "react_error_boundary",
      route: window.location.pathname,
      ...context,
    },
    {
      mechanism: "react_error_boundary",
      handled: false,
      severity: "error",
    },
  );
}

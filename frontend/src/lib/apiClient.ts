import { supabase } from "./supabase";

/** Base URL of the FastAPI backend. Override with VITE_API_BASE_URL. */
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/** Optional provider that resolves the current auth token (set by AuthContext). */
let tokenProvider: (() => Promise<string | null>) | null = null;

export function setTokenProvider(fn: () => Promise<string | null>): void {
  tokenProvider = fn;
}

/**
 * Turn a FastAPI error body into one readable line.
 *
 * A 4xx raised via HTTPException carries `detail` as a string, but a 422
 * validation failure carries an *array* of `{loc, msg, type}` objects. Passing
 * that array through String() yields "[object Object]", which is what every
 * form in the app used to show. `loc` starts with the request part ("body",
 * "query"), so drop the first element to leave the field path.
 */
function formatDetail(detail: unknown, fallback: string): string {
  if (!detail || typeof detail !== "object" || !("detail" in detail)) {
    return fallback;
  }
  const inner = (detail as { detail: unknown }).detail;
  if (Array.isArray(inner)) {
    const lines = inner.map((item) => {
      if (!item || typeof item !== "object") return String(item);
      const { loc, msg } = item as { loc?: unknown; msg?: unknown };
      const field = Array.isArray(loc) ? loc.slice(1).join(".") : "";
      const message = typeof msg === "string" ? msg : JSON.stringify(item);
      return field ? `${field}: ${message}` : message;
    });
    return lines.length ? lines.join("; ") : fallback;
  }
  return String(inner);
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function resolveToken(): Promise<string | null> {
  if (tokenProvider) return tokenProvider();
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }
  return null;
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await resolveToken();
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text().catch(() => null);
    }
    const message = formatDetail(
      detail,
      res.statusText || `Request failed (${res.status})`,
    );
    throw new ApiError(res.status, message, detail);
  }

  if (res.status === 204) return undefined as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

import type { ApiErrorBody } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function apiRequest<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorBody;
    const code = payload.error?.code;
    const message = payload.error?.message ?? `Request failed with HTTP ${response.status}.`;
    throw new Error(code ? `${code}: ${message}` : message);
  }

  return (await response.json()) as T;
}

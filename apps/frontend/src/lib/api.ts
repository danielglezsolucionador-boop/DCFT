const configuredApiUrl = (import.meta.env.VITE_DCFT_API_URL || "").replace(/\/$/, "");
export const API_URL = configuredApiUrl || (import.meta.env.DEV ? "http://127.0.0.1:8200" : "");

export type Session = {
  access_token: string;
  token_type: string;
};

export class ApiError extends Error {
  status: number;
  code?: string;
  detail?: unknown;

  constructor(status: number, message: string, detail?: unknown, code?: string) {
    super(message);
    this.status = status;
    this.detail = detail;
    this.code = code;
  }
}

const REQUEST_TIMEOUT_MS = 12000;

export async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const attempts = options.method && options.method !== "GET" ? 1 : 2;
  let lastError: unknown;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await requestOnce<T>(path, options, token);
    } catch (error) {
      lastError = error;
      if (!(error instanceof ApiError) || error.status !== 0 || attempt === attempts) {
        throw error;
      }
    }
  }
  throw lastError instanceof Error ? lastError : new ApiError(0, "Backend offline or unreachable");
}

async function requestOnce<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  if (!API_URL) {
    throw new ApiError(0, "Backend API URL is not configured");
  }
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {})
      }
    });
  } catch (error) {
    throw new ApiError(0, error instanceof DOMException && error.name === "AbortError" ? "Backend request timed out" : "Backend offline or unreachable");
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) {
    const rawDetail = await response.text();
    const parsedDetail = parseJsonDetail(rawDetail);
    throw new ApiError(
      response.status,
      extractMessage(parsedDetail, rawDetail || response.statusText),
      parsedDetail,
      extractCode(parsedDetail)
    );
  }
  return response.json() as Promise<T>;
}

function parseJsonDetail(rawDetail: string): unknown {
  if (!rawDetail) return null;
  try {
    return JSON.parse(rawDetail);
  } catch {
    return null;
  }
}

function extractCode(detail: unknown): string | undefined {
  if (!detail || typeof detail !== "object") return undefined;
  const body = detail as { detail?: unknown; error?: unknown };
  if (typeof body.error === "string") return body.error;
  if (body.detail && typeof body.detail === "object" && typeof (body.detail as { error?: unknown }).error === "string") {
    return (body.detail as { error: string }).error;
  }
  return undefined;
}

function extractMessage(detail: unknown, fallback: string): string {
  if (!detail || typeof detail !== "object") return fallback;
  const body = detail as { detail?: unknown; message?: unknown };
  if (typeof body.message === "string") return body.message;
  if (typeof body.detail === "string") return body.detail;
  if (body.detail && typeof body.detail === "object") {
    const nested = body.detail as { message?: unknown; error?: unknown };
    if (typeof nested.message === "string") return nested.message;
    if (typeof nested.error === "string") return nested.error;
  }
  return fallback;
}

export function post<T>(path: string, body: unknown, token?: string): Promise<T> {
  return request<T>(
    path,
    {
      method: "POST",
      body: JSON.stringify(body)
    },
    token
  );
}

export function patch<T>(path: string, body: unknown, token?: string): Promise<T> {
  return request<T>(
    path,
    {
      method: "PATCH",
      body: JSON.stringify(body)
    },
    token
  );
}

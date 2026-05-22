export const API_URL = import.meta.env.VITE_DCFT_API_URL || "http://127.0.0.1:8200";

export type Session = {
  access_token: string;
  token_type: string;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
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
    const detail = await response.text();
    throw new ApiError(response.status, detail || response.statusText);
  }
  return response.json() as Promise<T>;
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

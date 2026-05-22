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

export async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {})
      }
    });
  } catch (error) {
    throw new ApiError(0, "Backend offline or unreachable");
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

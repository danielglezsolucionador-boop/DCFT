export const API_URL = import.meta.env.VITE_DCFT_API_URL || "http://127.0.0.1:8200";

export type Session = {
  access_token: string;
  token_type: string;
};

export async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${detail}`);
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
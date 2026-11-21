import { env } from '../config/env';
import type { AuthResponse } from './types';

/**
 * Access tokens live in memory only (never localStorage), per the Genopedia
 * API security contract. The HttpOnly refresh cookie restores the session.
 */
let accessToken: string | null = null;
let onUserChange: ((user: AuthResponse['user'] | null) => void) | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}
export function getAccessToken() {
  return accessToken;
}
export function setUserListener(listener: typeof onUserChange) {
  onUserChange = listener;
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function rawRequest(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
  return fetch(`${env.apiBaseUrl}${path}`, { ...init, headers, credentials: 'include' });
}

export async function refreshSession(): Promise<AuthResponse['user'] | null> {
  const response = await rawRequest('/auth/refresh', { method: 'POST' });
  if (!response.ok) {
    accessToken = null;
    onUserChange?.(null);
    return null;
  }
  const data = (await response.json()) as AuthResponse;
  accessToken = data.access_token;
  onUserChange?.(data.user);
  return data.user;
}

export async function api<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  let response = await rawRequest(path, init);
  if (response.status === 401 && retry) {
    const user = await refreshSession();
    if (user) response = await rawRequest(path, init);
  }
  if (response.status === 204) return undefined as T;
  const text = await response.text();
  let data: unknown = undefined;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  if (!response.ok) {
    const detail = typeof data === 'object' && data !== null ? (data as { detail?: unknown }).detail : data;
    const message =
      typeof detail === 'string'
        ? detail
        : typeof detail === 'object' && detail !== null && 'message' in (detail as Record<string, unknown>)
          ? String((detail as Record<string, unknown>).message)
          : `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message, detail);
  }
  return data as T;
}

export function jsonBody(payload: unknown): RequestInit {
  return {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  };
}

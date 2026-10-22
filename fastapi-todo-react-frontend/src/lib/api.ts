import { clearSession, getToken, SESSION_EXPIRED_EVENT } from './session';

// Same-origin by default: nginx proxies /api -> backend (see docker/nginx).
// For `npm run dev`, vite.config.ts proxies /api to http://localhost:8085.
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? '/api';

export interface ApiResponse<T> {
    status: number;
    message: string;
    data: T;
}

export class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

interface RequestOptions {
    method?: string;
    body?: unknown;
    auth?: boolean; // default true
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, auth = true } = opts;

    const headers: Record<string, string> = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (auth) {
        const token = getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE_URL}${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
    });

    // Error bodies are not guaranteed to be JSON (e.g. a proxy 502 page).
    let json: Partial<ApiResponse<T>> & { detail?: unknown } = {};
    try { json = await res.json(); } catch { /* ignore */ }

    if (!res.ok) {
        if (res.status === 401 && auth) {
            clearSession();
            window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
        }
        const message =
            json.message ??
            (typeof json.detail === 'string' ? json.detail : undefined) ??
            `Request failed (${res.status})`;
        throw new ApiError(message, res.status);
    }
    return json.data as T;
}

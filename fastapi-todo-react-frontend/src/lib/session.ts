// Minimal, framework-free session storage shared by the API layer and React.
// NOTE: a bearer token in localStorage is readable by any script on the page
// (XSS). Acceptable for this app; for stricter setups move to an httpOnly cookie.

export interface SessionUser {
    id: number;
    email: string;
    full_name: string | null;
    role: string;
}

export interface Session {
    token: string;
    user: SessionUser;
    expiresAt: number; // epoch ms
}

const KEY = 'todo.session.v1';
export const SESSION_EXPIRED_EVENT = 'auth:expired';

export function loadSession(): Session | null {
    try {
        const raw = localStorage.getItem(KEY);
        if (!raw) return null;
        const s = JSON.parse(raw) as Session;
        if (!s.token || Date.now() >= s.expiresAt) {
            localStorage.removeItem(KEY);
            return null;
        }
        return s;
    } catch {
        return null;
    }
}

export function saveSession(s: Session): void {
    try { localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* storage unavailable */ }
}

export function clearSession(): void {
    try { localStorage.removeItem(KEY); } catch { /* storage unavailable */ }
}

export function getToken(): string | null {
    return loadSession()?.token ?? null;
}

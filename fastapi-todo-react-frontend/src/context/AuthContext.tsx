import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { authService } from '../services/authService';
import {
    clearSession, loadSession, saveSession, SESSION_EXPIRED_EVENT,
    type Session, type SessionUser,
} from '../lib/session';

interface AuthContextValue {
    user: SessionUser | null;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [session, setSession] = useState<Session | null>(() => loadSession());

    const login = useCallback(async (email: string, password: string) => {
        const s = await authService.login(email, password);
        saveSession(s);
        setSession(s);
    }, []);

    const logout = useCallback(() => {
        clearSession();
        setSession(null);
    }, []);

    // The API layer fires this when the backend answers 401 (expired token).
    useEffect(() => {
        const onExpired = () => setSession(null);
        window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
        return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
    }, []);

    const value = useMemo<AuthContextValue>(
        () => ({ user: session?.user ?? null, isAuthenticated: session !== null, login, logout }),
        [session, login, logout],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
    return ctx;
}

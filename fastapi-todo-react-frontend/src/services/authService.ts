import { request } from '../lib/api';
import type { Session, SessionUser } from '../lib/session';

interface LoginPayload {
    access_token: string;
    token_type: string;
    expires_in: number;
    user: SessionUser;
}

export const authService = {
    async login(email: string, password: string): Promise<Session> {
        const data = await request<LoginPayload>('/auth/login', {
            method: 'POST',
            body: { email, password },
            auth: false,
        });
        return {
            token: data.access_token,
            user: data.user,
            expiresAt: Date.now() + data.expires_in * 1000,
        };
    },
}

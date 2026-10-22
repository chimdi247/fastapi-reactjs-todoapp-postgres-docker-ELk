import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('todo-frontend.ui');

export default function Login() {
    const { login, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const from = (location.state as { from?: string } | null)?.from ?? '/todos';

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (isAuthenticated) return <Navigate to={from} replace />;

    const handleSubmit = async (e: React.SubmitEvent) => {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);
        // Manual instrumentation: one span per login attempt (user journey).
        await tracer.startActiveSpan('ui.login', async (span) => {
            try {
                await login(email.trim(), password);
                span.setAttribute('ui.login.outcome', 'success');
                navigate(from, { replace: true });
            } catch (err: unknown) {
                const message = err instanceof Error ? err.message : 'Login failed';
                span.setAttribute('ui.login.outcome', 'failure');
                span.setStatus({ code: SpanStatusCode.ERROR, message });
                setError(message);
            } finally {
                span.end();
                setIsSubmitting(false);
            }
        });
    };

    return (
        <div className="form-page">
            <div className="form-page__card">
                <h1 className="form-page__title">Sign in</h1>
                <p className="form-page__desc">Log in to manage your tasks.</p>

                {error && <div className="form-page__error" role="alert">{error}</div>}

                <form onSubmit={handleSubmit} className="form-page__form" data-testid="login-form">
                    <div className="form-page__group">
                        <label htmlFor="email" className="form-page__label">Email</label>
                        <input id="email" name="email" type="email" autoComplete="username" className="form-page__input"
                            placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
                    </div>
                    <div className="form-page__group">
                        <label htmlFor="password" className="form-page__label">Password</label>
                        <input id="password" name="password" type="password" autoComplete="current-password" className="form-page__input"
                            value={password} onChange={(e) => setPassword(e.target.value)} required />
                    </div>
                    <div className="form-page__actions">
                        <button type="submit" disabled={isSubmitting} className="form-page__btn form-page__btn--primary">
                            {isSubmitting ? 'Signing in...' : 'Sign in'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

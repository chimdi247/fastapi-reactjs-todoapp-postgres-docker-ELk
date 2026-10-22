import asyncio
import hashlib
import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import telemetry
from app.core.security import create_access_token, verify_password
from app.models.users import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

logger = logging.getLogger("app.auth")

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password",
    headers={"WWW-Authenticate": "Bearer"},
)


def _email_fingerprint(email: str) -> str:
    """Log a stable pseudonym instead of the raw e-mail address."""
    return hashlib.sha256(email.encode()).hexdigest()[:12]


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate(db: AsyncSession, creds: LoginRequest) -> TokenResponse:
    with telemetry.tracer.start_as_current_span("auth.authenticate") as span:
        user = await get_user_by_email(db, creds.email)

        # bcrypt is CPU bound (~250 ms): keep it off the event loop. It also runs
        # when the user does not exist, to equalise timing.
        password_ok = await asyncio.to_thread(
            verify_password, creds.password, user.password_hash if user else None
        )

        fingerprint = _email_fingerprint(creds.email)
        if user is None or not password_ok or not user.is_active:
            reason = (
                "unknown_user"
                if user is None
                else "inactive"
                if not user.is_active
                else "bad_password"
            )
            telemetry.auth_logins.add(1, {"outcome": "failure", "reason": reason})
            span.set_attribute("auth.outcome", "failure")
            logger.warning(
                "login failed",
                extra={"event": "auth.login", "outcome": "failure", "reason": reason,
                       "email_fingerprint": fingerprint},
            )
            raise _INVALID_CREDENTIALS

        await db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login_at=datetime.now(timezone.utc).replace(tzinfo=None))
        )
        await db.commit()
        await db.refresh(user)

        token, expires_in = create_access_token(
            str(user.id), {"email": user.email, "role": user.role}
        )
        telemetry.auth_logins.add(1, {"outcome": "success", "reason": "ok"})
        span.set_attribute("auth.outcome", "success")
        span.set_attribute("enduser.id", str(user.id))
        logger.info(
            "login succeeded",
            extra={"event": "auth.login", "outcome": "success", "user_id": user.id,
                   "role": user.role},
        )
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user=UserResponse.model_validate(user),
        )

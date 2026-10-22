"""Password hashing and JWT helpers.

bcrypt is used directly (passlib is unmaintained and breaks with bcrypt >= 4.1).
Hashes produced by PHP / Postgres pgcrypto (`$2y$` / `$2a$`) are accepted.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# Used to burn the same CPU time when the e-mail is unknown, so response timing
# does not reveal whether an account exists. The result is always discarded.
_TIMING_DUMMY_HASH = "$2y$12$lz2pomi4cBo6.DYDlTGFdeLUN3PO4WsNnFd745QnkMowmOjul9RBa"

# bcrypt only considers the first 72 bytes of the password.
BCRYPT_MAX_BYTES = 72


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str | None) -> bool:
    """Constant-ish time verification. Never raises."""
    candidate = hashed or _TIMING_DUMMY_HASH
    try:
        ok = bcrypt.checkpw(plain.encode("utf-8"), candidate.encode("utf-8"))
    except ValueError:  # malformed hash or >72 byte password on bcrypt>=5
        return False
    return ok and hashed is not None


def create_access_token(
    subject: str, extra_claims: dict[str, Any] | None = None
) -> tuple[str, int]:
    """Returns (token, expires_in_seconds)."""
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        **(extra_claims or {}),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError on any problem (expired, bad signature, ...)."""
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "sub"]},
    )

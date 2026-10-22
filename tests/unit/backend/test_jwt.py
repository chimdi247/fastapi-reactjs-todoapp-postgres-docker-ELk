import time

import jwt
import pytest

from app.core import security
from app.core.config import settings


@pytest.mark.unit
def test_token_roundtrip_carries_claims():
    token, expires_in = security.create_access_token("42", {"email": "a@b.c", "role": "admin"})
    claims = security.decode_access_token(token)
    assert claims["sub"] == "42" and claims["role"] == "admin" and claims["email"] == "a@b.c"
    assert expires_in == settings.JWT_EXPIRE_MINUTES * 60


@pytest.mark.unit
def test_expired_token_rejected(monkeypatch):
    monkeypatch.setattr(settings, "JWT_EXPIRE_MINUTES", -1)
    token, _ = security.create_access_token("1")
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_access_token(token)


@pytest.mark.unit
def test_tampered_signature_rejected():
    token, _ = security.create_access_token("1")
    head, payload, sig = token.split(".")
    forged = ".".join([head, payload, sig[:-2] + ("AA" if not sig.endswith("AA") else "BB")])
    with pytest.raises(jwt.PyJWTError):
        security.decode_access_token(forged)


@pytest.mark.unit
def test_token_signed_with_other_secret_rejected():
    forged = jwt.encode({"sub": "1", "exp": int(time.time()) + 60}, "x" * 40, algorithm="HS256")
    with pytest.raises(jwt.InvalidSignatureError):
        security.decode_access_token(forged)


@pytest.mark.unit
def test_alg_none_rejected():
    forged = jwt.encode({"sub": "1", "exp": int(time.time()) + 60}, key="", algorithm="none")
    with pytest.raises(jwt.PyJWTError):
        security.decode_access_token(forged)


@pytest.mark.unit
def test_token_without_sub_rejected():
    forged = jwt.encode({"exp": int(time.time()) + 60}, settings.JWT_SECRET, algorithm="HS256")
    with pytest.raises(jwt.MissingRequiredClaimError):
        security.decode_access_token(forged)

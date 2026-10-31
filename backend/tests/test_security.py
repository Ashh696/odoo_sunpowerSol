import pytest
from datetime import timedelta
import time

from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    TokenExpiredError,
    TokenInvalidError,
)


def test_password_hashing_and_verification():
    plain = "SunPower2026!#Secure"
    hashed = hash_password(plain)

    # Hash should not equal plain
    assert hashed != plain
    assert hashed.startswith("$2b$")

    # Correct password verifies
    assert verify_password(plain, hashed) is True

    # Incorrect password fails
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(plain, "") is False


def test_jwt_token_generation_and_decoding():
    payload_data = {
        "sub": "42",
        "email": "testuser@sunpower.local",
        "role": "SUPER_ADMIN",
    }
    token = create_access_token(payload_data, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded["sub"] == "42"
    assert decoded["email"] == "testuser@sunpower.local"
    assert decoded["role"] == "SUPER_ADMIN"
    assert "exp" in decoded
    assert "iat" in decoded


def test_jwt_token_expiration():
    payload_data = {"sub": "99", "email": "expired@sunpower.local"}
    # Token that expired 5 seconds ago
    token = create_access_token(payload_data, expires_delta=timedelta(seconds=-5))

    with pytest.raises(TokenExpiredError) as exc_info:
        decode_access_token(token)
    assert "expired" in str(exc_info.value).lower()


def test_jwt_invalid_token_rejection():
    with pytest.raises(TokenInvalidError):
        decode_access_token("this.is.a.completely.invalid.token")

    with pytest.raises(TokenInvalidError):
        decode_access_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature")

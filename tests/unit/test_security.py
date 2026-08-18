import base64
from datetime import timedelta

import jwt
import pytest

from src.auth.security import (
    create_access_token,
    create_jwt,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.config import settings


pytestmark = [pytest.mark.unit, pytest.mark.auth, pytest.mark.security]


def test_password_is_hashed_and_verified() -> None:
    password = "generated-at-test-runtime"
    hashed = hash_password(password)

    assert hashed != password
    assert password not in hashed
    assert verify_password(password, hashed) is True
    assert verify_password(f"{password}-wrong", hashed) is False


@pytest.mark.parametrize(
    ("factory", "token_type"),
    [
        (create_access_token, "access"),
        (create_refresh_token, "refresh"),
    ],
)
def test_token_factories_set_subject_type_expiration_and_jti(
    factory,
    token_type: str,
) -> None:
    claims = decode_token(factory(42))

    assert claims["sub"] == "42"
    assert claims["token_type"] == token_type
    assert isinstance(claims["exp"], int)
    assert claims["jti"]


def test_expired_token_is_rejected() -> None:
    expired = create_jwt(
        subject=1,
        expires_delta=timedelta(seconds=-1),
        token_type="access",
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired)


def test_changed_signature_is_rejected() -> None:
    token = create_access_token(1)
    header, payload, signature = token.split(".")
    padding = "=" * (-len(signature) % 4)
    signature_bytes = base64.urlsafe_b64decode(f"{signature}{padding}")
    changed_bytes = bytes([signature_bytes[0] ^ 1]) + signature_bytes[1:]
    changed_signature = (
        base64.urlsafe_b64encode(changed_bytes).rstrip(b"=").decode()
    )
    changed = ".".join((header, payload, changed_signature))

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(changed)


def test_token_signed_with_another_key_is_rejected() -> None:
    foreign = jwt.encode(
        {"sub": "1", "token_type": "access"},
        "different-signing-key-with-safe-test-length",
        algorithm=settings.algorithm,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(foreign)

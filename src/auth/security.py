from datetime import timedelta, datetime, timezone
from typing import Literal
from src.config import settings
from pwdlib import PasswordHash
import jwt

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    valid, _ = password_hash.verify_and_update(password, hashed_password)
    return valid

def create_jwt(
    subject: str | int,
    expires_delta: timedelta,
    token_type: Literal["access", "refresh"],
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": str(subject),
        "exp": expire,
        "token_type": token_type,
    }

    return jwt.encode(
        payload=payload,
        key=settings.secret_key,
        algorithm=settings.algorithm,
    )

def create_access_token(subject: str | int) -> str:
    return create_jwt(
        subject=subject,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        token_type="access",
    )

def create_refresh_token(subject: str | int) -> str:
    return create_jwt(
        subject=subject,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        token_type="refresh",
    )

def decode_token(token: str) -> dict:
    return jwt.decode(
        jwt=token,
        key=settings.secret_key,
        algorithms=[settings.algorithm],
    )

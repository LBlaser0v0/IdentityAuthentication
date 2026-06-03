from datetime import datetime, timedelta, timezone
import secrets

import jwt

from config.settings import AUTH_SERVER_BASE, DEFAULT_CLIENT_ID, JWT_ALGORITHM, JWT_SECRET


def create_access_token(payload: dict, expires_delta: timedelta):
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update(
        {
            "iss": AUTH_SERVER_BASE,
            "aud": DEFAULT_CLIENT_ID,
            "iat": int(now.timestamp()),
            "exp": expire,
            "jti": secrets.token_urlsafe(12),
        }
    )
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], audience=DEFAULT_CLIENT_ID)

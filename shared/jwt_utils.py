from datetime import datetime, timedelta, timezone

import jwt

from config.settings import JWT_ALGORITHM, JWT_SECRET


def create_access_token(payload: dict, expires_delta: timedelta):
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

from datetime import datetime, timedelta
import secrets

from sqlalchemy.orm import Session

from config.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    AUTH_CODE_EXPIRE_MINUTES,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_SECRET,
    DEFAULT_REDIRECT_URI,
)
from shared.jwt_utils import create_access_token
from shared.models import AccessToken, AuthorizationCode, OAuthClient, User
from shared.security import hash_password


def seed_initial_data(db: Session):
    if not db.query(User).filter_by(username="alice").first():
        db.add(
            User(
                username="alice",
                password_hash=hash_password("alice123"),
                role="user",
                allowed_scopes="read:profile read:email",
            )
        )
    if not db.query(User).filter_by(username="admin").first():
        db.add(
            User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
                allowed_scopes="read:profile read:email admin:panel",
            )
        )
    if not db.query(OAuthClient).filter_by(client_id=DEFAULT_CLIENT_ID).first():
        db.add(
            OAuthClient(
                client_id=DEFAULT_CLIENT_ID,
                client_secret=DEFAULT_CLIENT_SECRET,
                client_name="Course Demo Client",
                redirect_uri=DEFAULT_REDIRECT_URI,
            )
        )
    db.commit()


def create_authorization_code(
    db: Session,
    user: User,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    code_challenge: str = "",
    code_challenge_method: str = "",
):
    code = secrets.token_urlsafe(32)
    record = AuthorizationCode(
        code=code,
        user_id=user.id,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        expires_at=datetime.utcnow() + timedelta(minutes=AUTH_CODE_EXPIRE_MINUTES),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def issue_access_token(db: Session, code_record: AuthorizationCode):
    user = db.query(User).filter_by(id=code_record.user_id).first()
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "scope": code_record.scope,
        "client_id": code_record.client_id,
    }
    token = create_access_token(
        payload, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    token_record = AccessToken(
        token=token,
        user_id=user.id,
        client_id=code_record.client_id,
        scope=code_record.scope,
        expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    code_record.used = True
    db.add(token_record)
    db.commit()
    return token, user

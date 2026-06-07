from sqlalchemy.orm import Session

from shared.models import OAuthClient, User
from shared.security import verify_password


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter_by(username=username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_client_or_none(db: Session, client_id: str):
    return db.query(OAuthClient).filter_by(client_id=client_id).first()

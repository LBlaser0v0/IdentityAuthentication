from urllib.parse import parse_qs, urlparse

from auth_server.routes import authorize_submit, token
from config.settings import DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET, DEFAULT_REDIRECT_URI
from shared.database import Base, SessionLocal, engine
from shared.seed_data import seed_initial_data
import shared.models  # noqa: F401


def ensure_seeded_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()


def test_authorize_and_token_flow_for_alice():
    ensure_seeded_db()
    db = SessionLocal()
    try:
        response = authorize_submit(
            username="alice",
            password="alice123",
            client_id=DEFAULT_CLIENT_ID,
            redirect_uri=DEFAULT_REDIRECT_URI,
            scope="read:profile read:email",
            state="demo-state",
            code_challenge="",
            code_challenge_method="",
            db=db,
        )

        assert response.status_code == 302
        location = response.headers["location"]
        parsed = urlparse(location)
        query = parse_qs(parsed.query)
        assert query["state"] == ["demo-state"]
        code = query["code"][0]

        token_response = token(
            grant_type="authorization_code",
            code=code,
            client_id=DEFAULT_CLIENT_ID,
            client_secret=DEFAULT_CLIENT_SECRET,
            redirect_uri=DEFAULT_REDIRECT_URI,
            code_verifier="",
            db=db,
        )

        assert token_response.access_token
        assert token_response.scope == "read:profile read:email"
        assert token_response.token_type == "bearer"
    finally:
        db.close()

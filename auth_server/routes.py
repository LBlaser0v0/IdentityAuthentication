from datetime import datetime
import hashlib
import base64
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth_server.services import authenticate_user, get_client_or_none
from config.settings import ALLOWED_PKCE_METHODS, AUTH_SERVER_BASE, DEFAULT_CLIENT_ID, ENABLE_PKCE
from shared.database import get_db
from shared.models import AuthorizationCode
from shared.schemas import TokenResponse
from shared.seed_data import create_authorization_code, issue_access_token

router = APIRouter()
templates = Jinja2Templates(directory="auth_server/templates")


def _pkce_hint(code_challenge: str, code_challenge_method: str) -> str:
    if not code_challenge:
        return "当前未启用 PKCE，本次流程更适合做授权码截获对照实验。"
    return f"已附带 PKCE 参数，method = {code_challenge_method or 'plain'}。"


def _encode_s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


@router.get("/")
def root():
    return {"service": "authorization-server", "status": "ok", "pkce_enabled": ENABLE_PKCE}


@router.get("/authorize", response_class=HTMLResponse)
def authorize_page(
    request: Request,
    client_id: str,
    redirect_uri: str,
    scope: str = "read:profile",
    state: str = "",
    code_challenge: str = "",
    code_challenge_method: str = "",
):
    return templates.TemplateResponse(
        "authorize.html",
        {
            "request": request,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "state_hint": state or "本次请求已携带 state 参数",
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "pkce_hint": _pkce_hint(code_challenge, code_challenge_method),
            "default_client_id": DEFAULT_CLIENT_ID,
        },
    )


@router.post("/authorize")
def authorize_submit(
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form("read:profile"),
    state: str = Form(""),
    code_challenge: str = Form(""),
    code_challenge_method: str = Form(""),
    db: Session = Depends(get_db),
):
    client = get_client_or_none(db, client_id)
    if not client or client.redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="invalid client or redirect uri")
    if not state:
        raise HTTPException(status_code=400, detail="missing state")
    if code_challenge_method and code_challenge_method not in ALLOWED_PKCE_METHODS:
        raise HTTPException(status_code=400, detail="unsupported_code_challenge_method")
    if ENABLE_PKCE and not code_challenge:
        raise HTTPException(status_code=400, detail="missing_code_challenge")

    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")

    code = create_authorization_code(
        db,
        username=user.username,
        role=user.role,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )
    query = urlencode({"code": code, "state": state})
    return RedirectResponse(url=f"{redirect_uri}?{query}", status_code=302)


@router.post("/token", response_model=TokenResponse)
def token(
    grant_type: str = Form(...),
    code: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    redirect_uri: str = Form(...),
    code_verifier: str = Form(""),
    db: Session = Depends(get_db),
):
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

    client = get_client_or_none(db, client_id)
    if not client or client.client_secret != client_secret:
        raise HTTPException(status_code=401, detail="invalid_client")

    code_record = db.query(AuthorizationCode).filter_by(code=code).first()
    if not code_record:
        raise HTTPException(status_code=400, detail="invalid_code")
    if code_record.used:
        raise HTTPException(status_code=400, detail="code_already_used")
    if code_record.redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="redirect_uri_mismatch")
    if datetime.utcnow() > code_record.expires_at:
        raise HTTPException(status_code=400, detail="code_expired")

    if code_record.code_challenge:
        if not code_verifier:
            raise HTTPException(status_code=400, detail="invalid_code_verifier")
        if code_record.code_challenge_method == "S256":
            expected = _encode_s256(code_verifier)
        else:
            expected = code_verifier
        if expected != code_record.code_challenge:
            raise HTTPException(status_code=400, detail="invalid_code_verifier")

    access_token = issue_access_token(code_record)
    code_record.used = True
    db.commit()
    return TokenResponse(access_token=access_token, scope=code_record.scope, expires_in=1800)

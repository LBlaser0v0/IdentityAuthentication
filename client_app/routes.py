from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx

from client_app.services import build_authorize_url
from config.settings import AUTH_SERVER_BASE, DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET, DEFAULT_REDIRECT_URI, RESOURCE_SERVER_BASE

router = APIRouter()
templates = Jinja2Templates(directory="client_app/templates")


def build_status_card(title: str, response: httpx.Response, success_hint: str):
    ok = response.status_code == 200
    status_class = "status-card success" if ok else "status-card warning"
    badge_text = "访问成功" if ok else "访问受限"
    summary = success_hint if ok else "当前账号或权限范围无法访问该资源。"
    return f"""
    <section class='{status_class}'>
      <div class='status-card__head'>
        <div>
          <p class='status-card__eyebrow'>{title}</p>
          <h3>{badge_text}</h3>
        </div>
        <span class='status-badge'>{response.status_code}</span>
      </div>
      <p class='status-card__summary'>{summary}</p>
      <pre>{response.text}</pre>
    </section>
    """


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login")
def login(scope: str = "read:profile read:email"):
    url, state = build_authorize_url(scope)
    response = RedirectResponse(url=url, status_code=302)
    response.set_cookie("oauth_state", state, httponly=True)
    return response


@router.get("/callback", response_class=HTMLResponse)
def callback(request: Request, code: str, state: str = ""):
    saved_state = request.cookies.get("oauth_state", "")
    if saved_state and state and saved_state != state:
        raise HTTPException(status_code=400, detail="state mismatch")

    token_response = httpx.post(
        f"{AUTH_SERVER_BASE}/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": DEFAULT_CLIENT_ID,
            "client_secret": DEFAULT_CLIENT_SECRET,
            "redirect_uri": DEFAULT_REDIRECT_URI,
        },
        timeout=10.0,
    )
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail=token_response.text)

    token_data = token_response.json()
    access_token = token_data["access_token"]

    profile_response = httpx.get(
        f"{RESOURCE_SERVER_BASE}/profile",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )
    admin_response = httpx.get(
        f"{RESOURCE_SERVER_BASE}/admin",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )

    result_cards = "".join(
        [
            build_status_card("/profile", profile_response, "基础身份信息已成功返回。"),
            build_status_card("/admin", admin_response, "当前账号具备管理员权限，可访问后台资源。"),
        ]
    )

    response = templates.TemplateResponse(
        "callback.html",
        {
            "request": request,
            "code": code,
            "granted_scope": token_data["scope"],
            "access_token": access_token,
            "profile_status": profile_response.status_code,
            "admin_status": admin_response.status_code,
            "result_cards": result_cards,
        },
    )
    response.delete_cookie("oauth_state")
    return response

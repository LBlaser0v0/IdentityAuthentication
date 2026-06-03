from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
import jwt

from client_app.services import build_authorize_url
from config.settings import AUTH_SERVER_BASE, DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET, DEFAULT_REDIRECT_URI, ENABLE_PKCE, RESOURCE_SERVER_BASE

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


@router.get("/guide", response_class=HTMLResponse)
def guide(request: Request):
    quick_options = [
        {"label": "基础 scope", "value": "read:profile read:email"},
        {"label": "管理员 scope", "value": "read:profile read:email admin:panel"},
        {"label": "仅资料读取", "value": "read:profile"},
    ]
    experiment_cards = [
        {
            "title": "标准登录",
            "description": "请求基础 scope，验证普通登录链路和 /profile 成功结果。",
            "href": "/login",
            "meta": "read:profile read:email",
        },
        {
            "title": "高权限实验",
            "description": "额外申请 admin:panel，观察 role + scope 双重控制。",
            "href": "/login?scope=read:profile%20read:email%20admin:panel",
            "meta": "read:profile read:email admin:panel",
        },
        {
            "title": "PKCE 对照实验",
            "description": "启用 PKCE 参数，观察 callback 与 token 交换差异。",
            "href": "/login?scope=read:profile%20read:email&pkce=on",
            "meta": "S256 / code_verifier",
        },
    ]
    account_cards = [
        {
            "icon": "U",
            "title": "普通用户",
            "name": "alice / alice123",
            "description": "适合演示 read:email 生效，以及 admin 资源被拒绝的情况。",
            "admin": False,
        },
        {
            "icon": "A",
            "title": "管理员",
            "name": "admin / admin123",
            "description": "适合演示 admin:panel scope 与管理员角色同时满足时的访问结果。",
            "admin": True,
        },
    ]
    return templates.TemplateResponse(
        "guide.html",
        {
            "request": request,
            "quick_options": quick_options,
            "experiment_cards": experiment_cards,
            "account_cards": account_cards,
        },
    )


@router.get("/login")
def login(scope: str = "read:profile read:email", pkce: str = Query(default="auto")):
    use_pkce = ENABLE_PKCE if pkce == "auto" else pkce.lower() == "on"
    url, state, pkce_payload = build_authorize_url(scope, use_pkce=use_pkce)
    response = RedirectResponse(url=url, status_code=302)
    response.set_cookie("oauth_state", state, httponly=True)
    response.set_cookie("oauth_pkce_mode", "enabled" if pkce_payload else "disabled", httponly=True)
    if pkce_payload:
        response.set_cookie("oauth_code_verifier", pkce_payload["code_verifier"], httponly=True)
        response.set_cookie("oauth_code_challenge_method", pkce_payload["code_challenge_method"], httponly=True)
    return response


@router.get("/callback", response_class=HTMLResponse)
def callback(request: Request, code: str, state: str = ""):
    saved_state = request.cookies.get("oauth_state", "")
    if not saved_state:
        raise HTTPException(status_code=400, detail="missing saved state")
    if not state:
        raise HTTPException(status_code=400, detail="missing state")
    if saved_state != state:
        raise HTTPException(status_code=400, detail="state mismatch")

    token_request = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": DEFAULT_CLIENT_ID,
        "client_secret": DEFAULT_CLIENT_SECRET,
        "redirect_uri": DEFAULT_REDIRECT_URI,
    }
    verifier = request.cookies.get("oauth_code_verifier", "")
    if verifier:
        token_request["code_verifier"] = verifier

    token_response = httpx.post(
        f"{AUTH_SERVER_BASE}/token",
        data=token_request,
        timeout=10.0,
    )
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail=token_response.text)

    token_data = token_response.json()
    access_token = token_data["access_token"]
    decoded_payload = jwt.decode(access_token, options={"verify_signature": False})

    profile_response = httpx.get(
        f"{RESOURCE_SERVER_BASE}/profile",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )
    email_response = httpx.get(
        f"{RESOURCE_SERVER_BASE}/email",
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
            build_status_card("/email", email_response, "邮箱接口已按 read:email scope 正常返回。"),
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
            "email_status": email_response.status_code,
            "admin_status": admin_response.status_code,
            "result_cards": result_cards,
            "pkce_mode": request.cookies.get("oauth_code_challenge_method", "enabled") if verifier else request.cookies.get("oauth_pkce_mode", "disabled"),
            "expires_in": token_data.get("expires_in", 0),
            "decoded_payload": decoded_payload,
        },
    )
    response.delete_cookie("oauth_state")
    response.delete_cookie("oauth_code_verifier")
    response.delete_cookie("oauth_code_challenge_method")
    response.delete_cookie("oauth_pkce_mode")
    return response

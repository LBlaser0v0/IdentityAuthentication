from datetime import datetime
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from auth_server.services import authenticate_user, get_client_or_none
from shared.database import get_db
from shared.models import AuthorizationCode
from shared.schemas import TokenResponse
from shared.seed_data import create_authorization_code, issue_access_token

router = APIRouter()


@router.get("/")
def root():
    return {"service": "authorization-server", "status": "ok"}


@router.get("/authorize", response_class=HTMLResponse)
def authorize_page(
    client_id: str,
    redirect_uri: str,
    scope: str = "read:profile",
    state: str = "",
):
    html = f"""
    <!DOCTYPE html>
    <html lang='zh-CN'>
      <head>
        <meta charset='UTF-8' />
        <meta name='viewport' content='width=device-width, initial-scale=1.0' />
        <title>Authorization Server Login</title>
        <style>
          :root {{
            --bg: #0a1020;
            --panel: rgba(16, 24, 54, 0.82);
            --line: rgba(154, 178, 255, 0.16);
            --text: #f4f7ff;
            --muted: #aab6d9;
            --primary: #4f7cff;
            --accent: #6ef2d0;
            --shadow: 0 24px 70px rgba(1, 7, 20, 0.48);
          }}

          * {{ box-sizing: border-box; }}

          body {{
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 20px;
            font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
            color: var(--text);
            background:
              radial-gradient(circle at 12% 12%, rgba(79, 124, 255, 0.22), transparent 24%),
              radial-gradient(circle at 86% 14%, rgba(110, 242, 208, 0.16), transparent 22%),
              linear-gradient(135deg, #05070f 0%, #0a1020 45%, #0d1430 100%);
          }}

          .login-shell {{
            width: min(960px, 100%);
            display: grid;
            grid-template-columns: 1.05fr 0.95fr;
            gap: 22px;
            align-items: stretch;
          }}

          .panel {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 26px;
            background: var(--panel);
            backdrop-filter: blur(18px);
            box-shadow: var(--shadow);
          }}

          .panel::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.08), transparent 45%, rgba(255,255,255,0.03));
            pointer-events: none;
          }}

          .intro {{
            padding: 30px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
          }}

          .eyebrow {{
            margin: 0 0 10px;
            color: var(--accent);
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
          }}

          h1 {{
            margin: 0;
            font-size: clamp(30px, 4vw, 42px);
            line-height: 1.08;
          }}

          .intro p {{
            color: var(--muted);
            line-height: 1.8;
          }}

          .intro-grid {{
            display: grid;
            gap: 14px;
            margin-top: 22px;
          }}

          .intro-card {{
            padding: 16px 18px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.05);
          }}

          .intro-card strong {{
            display: block;
            margin-bottom: 6px;
            font-size: 15px;
          }}

          .form-panel {{
            padding: 30px;
          }}

          .top-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 18px;
          }}

          .chip {{
            display: inline-flex;
            align-items: center;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            color: #eaf0ff;
            font-size: 12px;
            font-weight: 700;
          }}

          .meta {{
            margin: 0 0 18px;
            padding: 14px 16px;
            border-radius: 16px;
            background: rgba(79,124,255,0.1);
            border: 1px solid rgba(79,124,255,0.16);
            color: var(--muted);
            line-height: 1.75;
          }}

          .meta strong {{
            color: var(--text);
          }}

          form {{
            display: grid;
            gap: 14px;
          }}

          label {{
            display: grid;
            gap: 8px;
            font-size: 14px;
            color: #dce5ff;
          }}

          input {{
            width: 100%;
            min-height: 48px;
            padding: 0 14px;
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 14px;
            background: rgba(255,255,255,0.06);
            color: var(--text);
            outline: none;
          }}

          input:focus {{
            border-color: rgba(110,242,208,0.42);
            box-shadow: 0 0 0 3px rgba(110,242,208,0.12);
          }}

          button {{
            min-height: 50px;
            border: 0;
            border-radius: 999px;
            font-size: 15px;
            font-weight: 800;
            color: #fff;
            cursor: pointer;
            background: linear-gradient(135deg, #4f7cff 0%, #7d58ff 100%);
            box-shadow: 0 16px 32px rgba(79,124,255,0.28);
          }}

          .demo-accounts {{
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid rgba(255,255,255,0.08);
            color: var(--muted);
            line-height: 1.8;
          }}

          @media (max-width: 860px) {{
            .login-shell {{
              grid-template-columns: 1fr;
            }}
          }}
        </style>
      </head>
      <body>
        <div class='login-shell'>
          <section class='panel intro'>
            <div>
              <p class='eyebrow'>Authorization Server</p>
              <h1>登录并完成授权</h1>
              <p>输入演示账号后，系统会签发 authorization code 并跳回客户端继续完成 token 交换。</p>
            </div>

            <div class='intro-grid'>
              <div class='intro-card'>
                <strong>当前流程</strong>
                <span>Identity Check → Code → Redirect</span>
              </div>
              <div class='intro-card'>
                <strong>安全参数</strong>
                <span>state 与 scope 已随授权请求传入。</span>
              </div>
            </div>
          </section>

          <section class='panel form-panel'>
            <div class='top-row'>
              <p class='eyebrow'>Sign In</p>
              <span class='chip'>Course Demo</span>
            </div>

            <div class='meta'>
              <div><strong>client_id：</strong>{client_id}</div>
              <div><strong>scope：</strong>{scope}</div>
            </div>

            <form method='post' action='/authorize'>
              <input type='hidden' name='client_id' value='{client_id}' />
              <input type='hidden' name='redirect_uri' value='{redirect_uri}' />
              <input type='hidden' name='scope' value='{scope}' />
              <input type='hidden' name='state' value='{state}' />

              <label>
                用户名
                <input name='username' placeholder='请输入用户名' />
              </label>

              <label>
                密码
                <input name='password' type='password' placeholder='请输入密码' />
              </label>

              <button type='submit'>登录并授权</button>
            </form>

            <div class='demo-accounts'>
              <div><strong>普通用户：</strong>alice / alice123</div>
              <div><strong>管理员：</strong>admin / admin123</div>
            </div>
          </section>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.post("/authorize")
def authorize_submit(
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form("read:profile"),
    state: str = Form(""),
    db: Session = Depends(get_db),
):
    client = get_client_or_none(db, client_id)
    if not client or client.redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="invalid client or redirect uri")

    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid username or password")

    granted_scopes = sorted(set(scope.split()) & set(user.allowed_scopes.split()))
    final_scope = " ".join(granted_scopes) if granted_scopes else "read:profile"

    code_record = create_authorization_code(
        db=db,
        user=user,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=final_scope,
        state=state,
    )
    params = {"code": code_record.code}
    if state:
        params["state"] = state
    return RedirectResponse(url=f"{redirect_uri}?{urlencode(params)}", status_code=302)


@router.post("/token", response_model=TokenResponse)
def exchange_token(
    grant_type: str = Form(...),
    code: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    redirect_uri: str = Form(...),
    db: Session = Depends(get_db),
):
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="unsupported grant_type")

    client = get_client_or_none(db, client_id)
    if not client or client.client_secret != client_secret:
        raise HTTPException(status_code=401, detail="invalid client credentials")

    code_record = db.query(AuthorizationCode).filter_by(code=code, client_id=client_id).first()
    if not code_record:
        raise HTTPException(status_code=400, detail="invalid code")
    if code_record.used:
        raise HTTPException(status_code=400, detail="code already used")
    if code_record.redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="redirect uri mismatch")
    if code_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="code expired")

    access_token, _ = issue_access_token(db, code_record)
    return TokenResponse(access_token=access_token, scope=code_record.scope)

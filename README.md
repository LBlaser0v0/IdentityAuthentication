# Identity Authentication — OAuth 2.0 攻击与防御实验系统

基于 OAuth 2.0 授权码模式的 Web 身份认证实验系统，包含**攻击模拟器**和**浏览器端攻击复现面板**，用于教学演示三类典型攻击及其防御机制。

## 系统架构

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Auth Server      │     │  Client App       │     │  Resource Server  │
│  :8000            │     │  :8001            │     │  :8002            │
│  授权码签发        │     │  前端 + 代理接口    │     │  受保护资源        │
│  Token 签发        │     │  攻击演示面板      │     │  /profile         │
│  PKCE 验证         │     │  State CSRF 校验   │     │  /email           │
│  Scope 裁剪        │     │                   │     │  /admin           │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### 实验账号

| 用户名 | 密码 | 角色 | 允许的 Scope |
|--------|------|------|-------------|
| alice | alice123 | user | read:profile read:email |
| admin | admin123 | admin | read:profile read:email admin:panel |

## 快速启动

### 环境要求

- Python 3.10+
- Windows / macOS / Linux

### 安装依赖

```bash
cd identity_final
python -m venv .venv
.venv\Scripts\activate      # Windows
# 或 source .venv/bin/activate  # macOS/Linux

pip install fastapi uvicorn httpx sqlalchemy pyjwt
```

### 初始化数据库并启动服务

```bash
# 1. 初始化数据库（创建 sqlite 和测试账号）
python scripts/init_db.py

# 2. 启动三个服务（需要三个终端窗口）

# 终端1 —— 授权服务器
python -m uvicorn auth_server.main:app --host 127.0.0.1 --port 8000

# 终端2 —— 客户端（含攻击演示面板）
python -m uvicorn client_app.main:app --host 127.0.0.1 --port 8001

# 终端3 —— 资源服务器
python -m uvicorn resource_server.main:app --host 127.0.0.1 --port 8002
```

> 或一键启动：`python scripts/run_all.py`

### 验证服务

```bash
curl http://127.0.0.1:8000/   # → {"service":"authorization-server","status":"ok","pkce_enabled":false}
curl http://127.0.0.1:8001/   # → 返回首页 HTML
curl http://127.0.0.1:8002/   # → {"service":"resource-server","status":"ok"}
```

## ⚔️ 攻击复现

### 方式一：浏览器攻击面板（推荐）

> ⚠️ **不能直接双击 HTML 文件打开！** 浏览器从 `file://` 协议打开时禁止向 `http://` 发请求。

**正确打开方式**：启动三个服务后，在浏览器地址栏输入：

```
http://127.0.0.1:8001/static/attack_demo.html
```

这个页面通过客户端服务的**同源代理接口**（`/attack-proxy/*`）转发所有请求，完全避免浏览器跨域限制。

**操作步骤**：依次点击 ① → ② → ③ 按钮，或直接点「一键完整攻击」。

### 方式二：命令行攻击模拟器

```bash
python scripts/run_c_experiments.py
```

输出每个实验的攻击是否成功、HTTP 状态码、耗时。结果保存在 `attack_simulator/results/`。

### 方式三：curl 手动复现

```bash
# 1. 截获 authorization_code
CODE=$(curl -s -X POST http://127.0.0.1:8000/authorize \
  -d "username=alice" -d "password=alice123" \
  -d "client_id=demo-client" \
  -d "redirect_uri=http://127.0.0.1:8001/callback" \
  -d "scope=read:profile read:email" \
  -d "state=test" -i 2>&1 | grep "location:" | grep -oP "code=\K[^&]+")

# 2. 攻击者用截获的 code 换 token（注意：没有 code_verifier！）
curl -s -X POST http://127.0.0.1:8000/token \
  -d "grant_type=authorization_code" \
  -d "code=$CODE" \
  -d "client_id=demo-client" \
  -d "client_secret=course-client-secret" \
  -d "redirect_uri=http://127.0.0.1:8001/callback"
# → 返回 access_token！攻击成功！
```

## 三类攻击说明

### 攻击一：授权码截获（Code Interception）

**原理**：攻击者截获 302 重定向 URL 中的 `authorization_code`，直接去换 token。

**防御**：PKCE（Proof Key for Code Exchange）。授权时带一个哈希挑战值（`code_challenge`），换 token 时必须提交原文（`code_verifier`），攻击者没有原文就换不了。

**开关**：`config/settings.py` 中的 `ENABLE_PKCE`（当前默认 `False`）

### 攻击二：登录 CSRF

**原理**：攻击者构造恶意回调链接，把自己的 code 绑定到受害者的会话上。

**防御**：State 参数绑定。`/login` 时生成随机 state 写入 HttpOnly cookie，`/callback` 时严格比对 cookie 和 URL 中的 state。

### 攻击三：Scope 权限滥用

**原理**：普通用户故意申请管理员 scope（如 `admin:panel`）。

**防御**：两道防线——
1. 授权服务器裁剪 scope（取用户 `allowed_scopes` 的交集）
2. 资源服务器独立校验 role + scope

## 防御开关

所有配置在 `config/settings.py`：

```python
ENABLE_PKCE = False           # 是否启用 PKCE（改为 True 后攻击一立刻失败）
DEFAULT_PKCE_METHOD = "S256"  # PKCE 方法: "S256" 或 "plain"
```

## 目录结构

```
identity_final/
├── config/settings.py          # 全局配置（端口、密钥、PKCE开关）
├── shared/                     # 共享模块（数据库、JWT、数据模型）
├── auth_server/                # 授权服务器（/authorize, /token）
├── client_app/                 # 客户端 + 攻击代理 + 演示面板
│   ├── routes.py               # 包含 /attack-proxy/* 代理接口
│   └── static/
│       └── attack_demo.html    # 浏览器攻击演示面板
├── resource_server/            # 资源服务器（/profile, /email, /admin）
├── attack_simulator/           # C 同学的黑盒攻击实验脚本
├── scripts/
│   ├── init_db.py              # 数据库初始化
│   ├── run_all.py              # 一键启动三个服务
│   └── run_c_experiments.py    # 运行攻击实验
├── tests/                      # 测试用例
├── 攻击与防御_零基础图解.md      # 新手友好的图解说明
└── README.md                   # 本文件
```

## 常见问题

**Q: `attack_demo.html` 双击打开后点按钮没反应？**
A: 不能直接双击打开。必须在浏览器输入 `http://127.0.0.1:8001/static/attack_demo.html`，确保三个服务都已启动。

**Q: 攻击一为什么能成功？**
A: 因为 `ENABLE_PKCE=False`，`/token` 端点不验证 `code_verifier`。在 `config/settings.py` 里把 `ENABLE_PKCE` 改成 `True` 并重启服务，攻击立刻失败。

**Q: 端口被占用怎么办？**
A: 修改 `config/settings.py` 中的 `AUTH_SERVER_PORT`、`CLIENT_APP_PORT`、`RESOURCE_SERVER_PORT`。

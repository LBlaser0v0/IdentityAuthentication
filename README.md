# OAuth2/OIDC 身份认证与访问控制课程项目

这是一个适合课程论文、课堂汇报与小组协作开发的本地多服务模拟项目，围绕 **OAuth2 授权码模式、状态绑定、PKCE、防止过度授权、Role + Scope 访问控制** 展开。

当前系统保持本机局域网访问方式，默认开放端口：

- Authorization Server：`http://127.0.0.1:8000`
- Client App：`http://127.0.0.1:8001`
- Resource Server：`http://127.0.0.1:8002`

---

## 当前已完成

- 三服务基础骨架
- 授权码模式最小闭环
- JWT access token
- `/profile`、`/email`、`/admin` 资源接口
- role + scope 双重访问控制
- 严格 state 校验
- PKCE 参数预埋与校验逻辑
- SQLite 初始化脚本
- 面向课程演示的前端页面
- 面向 C 同学实验的契约补强

---

## 目录结构

```text
config/             配置
shared/             公共数据库、模型、JWT、安全工具、种子数据
auth_server/        认证授权服务器
client_app/         客户端应用、模板、静态资源
resource_server/    资源服务器
scripts/            初始化、启动、环境检查脚本
data/               SQLite 数据库文件
docs/               文档草稿
report_assets/      论文和 PPT 图表素材
attack_simulator/   预留给 C 同学的攻击与实验脚本目录
```

---

## 环境要求

- Python 3.8+

项目目录下已创建本地虚拟环境：

```text
.venv/
```

后续运行脚本时，**优先使用项目内的 Python**，不要直接依赖系统全局 Python。

推荐命令：

```bash
.venv/Scripts/python --version
.venv/Scripts/python scripts/check_contract_env.py
.venv/Scripts/python scripts/init_db.py
.venv/Scripts/python scripts/run_all.py
```

如果你直接运行系统 Python，编辑器或终端可能提示缺少运行库。出现这种情况时，请确认解释器已经切换到：

```text
.venv\Scripts\python.exe
```

---

## 安装依赖

首次使用或换设备时，运行：

```bash
scripts/install_deps.bat
```

脚本会：

1. 创建 `.venv`
2. 安装 `requirements.txt`
3. 安装 `requirements-lock.txt`

如果你想严格还原已经验证通过的完整依赖版本，也可以单独执行：

```bash
.venv/Scripts/pip install -r requirements-lock.txt
```

---

## 初始化数据库

如果你修改了：

- 默认账号
- 默认角色或 scope
- `client_id`
- `client_secret`
- `redirect_uri`
- 其他种子数据

建议重新初始化数据库。

运行：

```bash
scripts/init_db.bat
```

如果之前已经有旧数据库，最稳妥的课程项目做法是：

1. 停止服务
2. 删除旧的 `data/app.db`
3. 再执行 `scripts/init_db.bat`

---

## 启动全部服务

运行：

```bash
scripts/run_all.bat
```

启动后访问：

- Auth Server：`http://127.0.0.1:8000`
- Client App：`http://127.0.0.1:8001`
- Resource Server：`http://127.0.0.1:8002`

---

## 契约环境检查脚本

为方便小组成员确认配置是否满足 C 模块契约，新增：

```bash
scripts/check_contract_env.bat
```

或：

```bash
.venv/Scripts/python scripts/check_contract_env.py
```

它会输出：

- 三个服务基础地址
- 默认 `client_id`
- 默认 `redirect_uri`
- PKCE 是否开启
- 下一步建议操作

注意：这个脚本目前检查的是**配置层**，不直接联网测试服务存活状态。

---

## 演示账号

默认实验账号：

- 普通用户：`alice / alice123`
- 管理员：`admin / admin123`

默认权限：

- `alice`
  - `role = user`
  - `allowed_scopes = read:profile read:email`
- `admin`
  - `role = admin`
  - `allowed_scopes = read:profile read:email admin:panel`

---

## 默认 OAuth Client 配置

- `client_id = demo-client`
- `client_secret = course-client-secret`
- `redirect_uri = http://127.0.0.1:8001/callback`

如果你修改这些值，请同步：

- `config/settings.py`
- 数据库中的 OAuth client 种子数据
- C 同学实验脚本配置

---

## 当前登录流程

1. 访问 Client App 首页。
2. 点击标准登录或高权限实验。
3. Client App 生成并保存 `state`，必要时生成 PKCE 参数。
4. 跳转到 Authorization Server 的 `/authorize`。
5. 用户输入演示账号密码。
6. Authorization Server 校验用户与 client 信息，生成 authorization code。
7. 回调到 `/callback?code=xxx&state=xxx`。
8. Client App 严格校验 `state`。
9. Client App 调用 `/token` 换取 access token。
10. Client App 使用 token 自动请求：
    - `/profile`
    - `/admin`
11. 页面展示：
    - 授权码
    - granted scope
    - PKCE 模式
    - access token
    - JWT payload
    - 资源访问结果

---

## Resource Server 当前接口

### 1. `/profile`
- 要求 scope：`read:profile`
- 合法登录用户可访问

### 2. `/email`
- 要求 scope：`read:email`
- 适合作为成员 B 的扩展接口基础

### 3. `/admin`
访问 `/admin` 必须同时满足：

- `role = admin`
- scope 包含 `admin:panel`

所以：

- 标准登录状态下，`alice` 和 `admin` 通常都只能看 `/profile`
- 高权限实验状态下：
  - `alice` 仍不能访问 `/admin`
  - `admin` 可以访问 `/admin`

这是系统设计的正常行为，用于体现最小权限原则与 Role + Scope 双重控制。

---

## PKCE 与 state 设计

当前系统已经支持或预留：

### state
- `/login` 阶段生成随机 `state`
- `/callback` 阶段严格校验：
  - 本地无 state → 400
  - 缺少 state → 400
  - state 不匹配 → 400

### PKCE
配置位在：

- `config/settings.py`

关键项：

- `ENABLE_PKCE`
- `DEFAULT_PKCE_METHOD`
- `ALLOWED_PKCE_METHODS`

当前逻辑支持：

- `plain`
- `S256`

如果开启 PKCE：

- `/authorize` 可接收：
  - `code_challenge`
  - `code_challenge_method`
- `/token` 可接收：
  - `code_verifier`

这正是 C 同学第 5、6 章实验需要的基础。

---

## JWT payload 约定

当前 token payload 重点保留：

- `sub`
- `username`
- `role`
- `scope`
- `client_id`
- `exp`

并增加了实验友好的扩展字段：

- `iss`
- `aud`
- `iat`
- `jti`

如果后续改名或删除这些核心字段，请先同步 C 同学。

---

## 给四位同学的建议分工

### 成员 A：认证主流程
建议负责：

- `/authorize`
- `/token`
- state 绑定
- PKCE 逻辑
- 时序图和认证主线说明

重点文件：

- `auth_server/routes.py`
- `auth_server/services.py`
- `client_app/services.py`
- `client_app/routes.py`
- `config/settings.py`

### 成员 B：访问控制
建议负责：

- `/profile`
- `/email`
- `/admin`
- 新增资源接口
- 更细粒度 role / scope 策略

重点文件：

- `resource_server/routes.py`
- `resource_server/services.py`
- `shared/models.py`
- `shared/seed_data.py`

### 成员 C：攻击与防御实验
建议负责：

- 授权码截获攻击
- 登录 CSRF / state 攻击
- scope 过度授权实验
- PKCE plain / S256 / verifier 长度对比实验
- 黑盒契约检查脚本

建议目录：

```text
attack_simulator/
```

建议包含：

- `config.py`
- `oauth_client.py`
- `check_contract.py`
- `attack_code_interception.py`
- `attack_login_csrf.py`
- `attack_scope_escalation.py`
- `pkce_tuning.py`
- `run_experiments.py`

### 成员 D：论文与 PPT 整合
建议负责：

- 系统架构图
- OAuth 授权码时序图
- 攻击与防御对比图
- 实验表格
- 页面截图
- 章节结构整理

重点来源：

- `README.md`
- `docs/architecture.md`
- `docs/api_notes.md`
- `report_assets/`
- C 同学输出的实验结果 JSON / 表格

---

## C 同学实验使用方式建议

### 1. 第 5 章：攻击与防御实验
推荐至少做这三组：

#### 授权码截获攻击
- 无 PKCE 时：攻击者只拿 `code` 调 `/token`
- 开启 PKCE 时：缺少或错误 `code_verifier` 应失败

#### 登录 CSRF / state 攻击
- callback 缺少 `state`
- callback `state` 不匹配
- 本地没有保存 `state`

预期：都应被拒绝并返回 400

#### 权限提升 / 过度授权实验
- `alice` 请求 `admin:panel`
- 观察授权服务器是否正确过滤 scope
- 再访问 `/admin`

预期：
- 普通用户请求高权限 scope 后仍不能访问 `/admin`
- 管理员在申请高权限 scope 后可以访问 `/admin`

### 2. 第 6 章：PKCE 调优实验
推荐比较：

- 无 PKCE
- `plain`
- `S256`
- 不同长度 `code_verifier`

建议输出字段：

- `experiment`
- `defense`
- `attack_success`
- `token_status`
- `resource_status`
- `elapsed_ms`
- `reason`

---

## 前端窗口说明

当前前端窗口主要有三个：

1. 客户端首页
   - 说明认证流程
   - 提供标准登录与高权限实验入口

2. 认证服务器登录页
   - 展示本次授权上下文
   - 输入账号密码

3. 回调结果页
   - 展示授权码
   - granted scope
   - PKCE mode
   - access token
   - decoded JWT payload
   - `/profile` 与 `/admin` 返回结果

这些页面已经在课程展示方向上进行了统一样式优化，并且保留了继续美化的空间。

---

## 当前关键配置文件

### `config/settings.py`
建议重点关注：

- `SERVER_HOST`
- `AUTH_SERVER_PORT`
- `CLIENT_APP_PORT`
- `RESOURCE_SERVER_PORT`
- `DEFAULT_CLIENT_ID`
- `DEFAULT_CLIENT_SECRET`
- `DEFAULT_REDIRECT_URI`
- `ENABLE_PKCE`
- `DEFAULT_PKCE_METHOD`

### `shared/seed_data.py`
这里负责：

- 默认用户
- 默认角色
- 默认 allowed scopes
- 默认 OAuth client

如果你要新增普通用户或管理员，优先改这里。

---

## 常见维护规则

如果后续准备修改下面这些内容，请先同步 C 同学：

- 服务地址或端口
- 默认账号、密码、role、allowed_scopes
- `client_id`、`client_secret`、`redirect_uri`
- `/authorize` 参数
- `/token` 参数或返回字段
- `/callback` 参数或 state 校验行为
- JWT payload 中的 `username`、`role`、`scope`、`client_id`、`exp`
- `/profile`、`/admin` 的访问控制语义
- 核心 scope 名称，如 `read:profile`、`admin:panel`

原则：

- 可以扩展
- 尽量不要删除核心契约字段
- 保持黑盒实验脚本稳定可复用

---

## 当前推荐操作顺序

如果后续成员接手项目，最稳妥的流程是：

1. 运行 `scripts/install_deps.bat`
2. 确认解释器切到 `.venv\Scripts\python.exe`
3. 运行 `scripts/check_contract_env.bat`
4. 如果修改过种子数据或 client 配置，重新初始化数据库
5. 运行 `scripts/run_all.bat`
6. 打开 Client App 首页做标准登录和高权限实验
7. 再在此基础上开发访问控制、攻击脚本和论文实验

---

## 当前项目定位总结

这个系统不是生产级身份平台，而是一个**适合课程论文与小组协作的本地 OAuth2/OIDC 教学实验系统**，核心价值在于：

- 能完整复现授权码模式
- 能体现身份认证与访问控制
- 能支持 state / PKCE / scope / role 实验
- 能让 A / B / C / D 四位成员围绕统一接口继续扩展

如果后续继续开发，最推荐的主线依然是：

1. 认证主流程复现
2. 访问控制细化
3. 攻击模拟
4. 防御增强
5. 实验对比与论文总结

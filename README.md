# OAuth2/OIDC 身份认证与访问控制课程项目

这是一个适合课程论文与演示 PPT 的本地多服务模拟项目，包含：

- Authorization Server
- Client App
- Resource Server
- Shared SQLite Database
- 后续攻击与实验脚本目录

## 当前已完成

- 三服务基础骨架
- 授权码模式最小闭环
- JWT access token
- `/profile` 与 `/admin` 资源接口
- role + scope 基础访问控制
- SQLite 初始化脚本

## 目录结构

```text
config/             配置
shared/             公共数据库、模型、JWT、安全工具
auth_server/        认证授权服务器
client_app/         客户端应用
resource_server/    资源服务器
scripts/            初始化、启动、测试脚本
data/               SQLite 数据库文件
docs/               文档草稿
report_assets/      论文和 PPT 图表素材
```

## 环境要求

- Python 3.8+

## 已内置本地虚拟环境

项目目录下已经创建：

```text
.venv/
```

请注意：后续运行脚本时，优先使用项目内的 Python，而不是系统全局 Python。

推荐命令：

```bash
.venv/Scripts/python --version
.venv/Scripts/python scripts/init_db.py
.venv/Scripts/python scripts/run_all.py
```

如果你直接运行 `python init_db.py`，很可能会调用到系统 Python，导致缺少本项目依赖。

如果换设备，只需要重新执行：

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

如果希望严格还原我当前这台机器里已经验证通过的完整依赖版本，可以执行：

```bash
.venv/Scripts/pip install -r requirements-lock.txt
```

## 初始化数据库

```bash
.venv/Scripts/python scripts/init_db.py
```

## 启动全部服务

```bash
.venv/Scripts/python scripts/run_all.py
```

启动后访问：

- Auth Server: http://127.0.0.1:8000
- Client App: http://127.0.0.1:8001
- Resource Server: http://127.0.0.1:8002

## 冒烟测试

服务启动后执行：

```bash
.venv/Scripts/python scripts/smoke_test.py
```

## 演示账号

- 普通用户：`alice / alice123`
- 管理员：`admin / admin123`

## 当前登录流程

1. 访问 Client App 首页。
2. 点击登录链接跳转到 Authorization Server。
3. 输入演示账号密码。
4. Authorization Server 返回 authorization code 到 Client callback。
5. Client 使用 code 换 access token。
6. Client 自动请求 Resource Server 的 `/profile` 和 `/admin`。

## 后续给成员 B/C 的扩展点

- `authorization_codes` 表已预留：
  - `state`
  - `code_challenge`
  - `code_challenge_method`
- 用户表已包含：
  - `role`
  - `allowed_scopes`
- token payload 已包含：
  - `role`
  - `scope`
  - `client_id`

## 建议下一步

- 成员 A：补全 state 更严格校验和时序图
- 成员 B：完善 `/email`、`/admin` 等访问控制策略
- 成员 C：实现 PKCE、攻击模拟与性能对比脚本
- 成员 D：整理架构图、流程图、实验图

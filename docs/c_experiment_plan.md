# C 同学实验说明

## A 同学交付物完成度判断

按 `分工表.md` 对照当前代码：

| A 任务 | 当前状态 | 依据 |
| --- | --- | --- |
| 搭建 Authorization Server | 已完成 | `auth_server/main.py`、`auth_server/routes.py` |
| 搭建 Client | 已完成 | `client_app/main.py`、`client_app/routes.py` |
| 实现用户登录认证功能 | 已完成 | `auth_server/services.py` |
| 实现 Authorization Code 签发机制 | 已完成 | `shared/seed_data.py:create_authorization_code` |
| 实现 Access Token 与 ID Token 签发 | 部分完成 | 已签发 JWT access token；`id_token` 字段只在响应模型中预留，未真正签发 |
| 实现 OIDC 授权码模式完整登录流程 | 基本完成 | Client `/login` 到 Auth `/authorize` 再到 Client `/callback` 的闭环已存在 |
| 完成单点登录（SSO）流程验证 | 部分完成 | 当前是单客户端本地演示，还没有多客户端共享登录态验证 |

结论：当前系统已经足够支撑 C 同学的攻击、防御和 PKCE 调优实验。严格 OIDC 的 `id_token` 和多客户端 SSO 可以作为后续增强项，不阻塞 C 模块。

## C 模块实验矩阵

| 实验 | 攻击目标 | 防护点 | 预期结果 |
| --- | --- | --- | --- |
| 授权码截获攻击（无 PKCE） | 攻击者截获 `code` 后直接调用 `/token` | 无 | 攻击成功，可换取 token 并访问 `/profile` |
| 授权码截获攻击（S256 PKCE） | 攻击者截获 `code` 但没有 `code_verifier` | PKCE | 攻击失败，`/token` 返回错误 |
| 登录 CSRF：无本地 state | 伪造 callback 请求 | state cookie 校验 | callback 返回 400 |
| 登录 CSRF：缺少回调 state | 删除 callback 中的 `state` | state 参数必填 | callback 返回 400 |
| 登录 CSRF：state 不匹配 | 使用攻击者构造的 state | state 绑定校验 | callback 返回 400 |
| Scope 滥用 | `alice` 请求 `admin:panel` | 授权服务器 scope 裁剪 + 资源服务器 role/scope 双检 | `alice` 无法访问 `/admin` |
| PKCE 性能调优 | 比较不同 method 和 verifier 长度 | 本地生成耗时统计 | 输出 avg、p95、max |

## 输出字段

`attack_simulator/results/latest_summary.csv` 可直接转成论文表格：

| 字段 | 含义 |
| --- | --- |
| `experiment` | 实验名称 |
| `defense` | 防护方案或场景 |
| `attack_success` | 攻击是否成功 |
| `token_status` | `/token` HTTP 状态码 |
| `resource_status` | 资源接口或 callback HTTP 状态码 |
| `elapsed_ms` | 实验耗时 |
| `reason` | 结果解释 |
| `evidence` | 关键证据，如错误响应、granted scope、PKCE 性能指标 |

## 防护方案总结

1. 授权码截获防护：启用 PKCE，优先使用 `S256`，避免只依赖授权码本身。
2. 登录 CSRF 防护：客户端在 `/login` 生成随机 `state` 并写入 HttpOnly cookie，`/callback` 严格比较回调 state。
3. Scope 滥用防护：认证服务器按用户允许权限裁剪请求 scope，资源服务器继续执行 role + scope 双重检查。
4. Token 滥用防护：JWT 保留 `iss`、`aud`、`exp`、`iat`、`jti`，资源服务器校验签名、过期时间和 audience。
5. 性能调优建议：默认使用 `S256`，verifier 长度采用 48 bytes 已能兼顾安全性和生成开销。


# C 同学攻击实验与 PKCE 调优模块

本目录用于生成第 5 章“攻击与防御实验”和第 6 章“PKCE 调优实验”的数据。

## 前置条件

先初始化数据库并启动三台服务：

```bash
python3 scripts/init_db.py
python3 -m uvicorn auth_server.main:app --host 127.0.0.1 --port 8000
python3 -m uvicorn client_app.main:app --host 127.0.0.1 --port 8001
python3 -m uvicorn resource_server.main:app --host 127.0.0.1 --port 8002
```

Windows 环境可继续使用项目原有的：

```bat
scripts\init_db.bat
scripts\run_all.bat
```

## 运行实验

```bash
python3 attack_simulator/run_experiments.py
```

输出文件：

- `attack_simulator/results/latest_results.json`
- `attack_simulator/results/latest_summary.csv`

## 实验覆盖

- 授权码截获攻击：无 PKCE 时攻击者可换取 token；启用 S256 PKCE 后缺少 `code_verifier` 应失败。
- 登录 CSRF：覆盖无本地 state、缺少回调 state、state 不匹配三种情况。
- Scope 滥用：`alice` 请求 `admin:panel` 后应被授权服务器过滤，`admin` 请求同样 scope 后可访问 `/admin`。
- PKCE 性能：比较 `plain` 与 `S256` 在不同 verifier 长度下的本地生成开销。


# C同学攻击实验与PKCE调优演示步骤

本文档用于 C 同学在 Win11 电脑上演示第 5 章“攻击与防御实验”和第 6 章“PKCE 调优实验”。

## 一、演示前准备

### 1. 进入项目目录

在项目根目录打开 PowerShell 或 CMD。

```bat
cd IdentityAuthentication
```

### 2. 安装依赖

第一次运行或换电脑时执行：

```bat
scripts\install_deps.bat
```

### 3. 初始化数据库

```bat
scripts\init_db.bat
```

### 4. 启动三台服务

```bat
scripts\run_all.bat
```

启动成功后会有三个本地服务：

```text
Authorization Server: http://127.0.0.1:8000
Client App:           http://127.0.0.1:8001
Resource Server:      http://127.0.0.1:8002
```

浏览器打开：

```text
http://127.0.0.1:8001
```

## 二、页面演示路线

### 1. 标准登录演示

1. 打开 `http://127.0.0.1:8001`
2. 点击“使用 Course Identity 登录”
3. 在认证服务器登录页输入：

```text
alice / alice123
```

4. 观察回调结果页：
   - `/profile` 返回 200
   - `/email` 返回 200
   - `/admin` 返回 403

讲解点：

```text
普通用户 alice 只拥有 read:profile 和 read:email scope。
即使登录成功，也不能访问管理员资源。
```

### 2. Scope滥用演示

1. 回到首页
2. 点击“管理员权限请求”
3. 使用普通用户登录：

```text
alice / alice123
```

4. 观察结果：
   - granted scope 不包含 `admin:panel`
   - `/admin` 返回 403

讲解点：

```text
攻击者请求了 admin:panel，但认证服务器会按用户 allowed_scopes 裁剪权限。
资源服务器还会继续检查 role + scope，所以 alice 无法越权。
```

### 3. 管理员对照演示

1. 再次点击“管理员权限请求”
2. 使用管理员登录：

```text
admin / admin123
```

3. 观察结果：
   - granted scope 包含 `admin:panel`
   - `/admin` 返回 200

讲解点：

```text
管理员必须同时满足 role=admin 和 scope 包含 admin:panel，才能访问管理员接口。
```

### 4. PKCE登录演示

1. 回到首页
2. 点击“PKCE 登录”
3. 使用任意账号登录
4. 在结果页观察 PKCE 状态

讲解点：

```text
PKCE 会在授权请求中加入 code_challenge。
token 交换阶段必须提交匹配的 code_verifier。
攻击者即使截获 authorization code，也不能直接换取 token。
```

## 三、攻击实验脚本演示

保持三台服务运行，另开一个新的 PowerShell 或 CMD 窗口，执行：

```bat
.venv\Scripts\python.exe scripts\run_c_experiments.py
```

如果想让 PKCE 性能测试更快，可以减少迭代次数：

```bat
.venv\Scripts\python.exe scripts\run_c_experiments.py --pkce-iterations 50
```

脚本会自动执行：

1. 授权码截获攻击
2. PKCE 防御对照
3. 登录 CSRF state 校验实验
4. Scope 滥用实验
5. PKCE 性能开销测试

## 四、预期输出说明

典型输出类似：

```text
authorization_code_interception  no_pkce      attack_success=True  token=200 resource=200
authorization_code_interception  pkce_s256    attack_success=False token=400
login_csrf                       missing_saved_state attack_success=False resource=400
login_csrf                       missing_query_state attack_success=False resource=400
login_csrf                       state_mismatch      attack_success=False resource=400
scope_abuse                      user_requests_admin_scope attack_success=False token=200 resource=403
scope_abuse                      admin_requests_admin_scope attack_success=False token=200 resource=200
```

讲解方式：

| 实验 | 现象 | 结论 |
| --- | --- | --- |
| 无 PKCE 授权码截获 | 攻击成功，能换 token | 单独依赖 authorization code 不安全 |
| S256 PKCE | 攻击失败，`/token` 返回 400 | 缺少 `code_verifier` 无法换 token |
| 登录 CSRF | 三种异常 state 都返回 400 | state 绑定能防止伪造 callback |
| alice 请求 admin scope | token 成功但 `/admin` 返回 403 | scope 被裁剪，资源端继续拒绝 |
| admin 请求 admin scope | `/admin` 返回 200 | role 和 scope 同时满足才放行 |

## 五、实验结果文件

运行脚本后会生成：

```text
attack_simulator\results\latest_results.json
attack_simulator\results\latest_summary.csv
```

其中：

- `latest_results.json`：适合保存完整实验记录
- `latest_summary.csv`：适合放进论文表格或 Excel 画图

## 六、论文第5章可讲内容

第 5 章可以按下面逻辑写：

1. 实验目标：验证授权码截获、登录 CSRF、Scope 滥用三类风险。
2. 攻击前提：攻击者能观察或伪造部分 OAuth 回调参数。
3. 攻击结果：无 PKCE 时授权码截获成功，其他防护开启后攻击失败。
4. 防御机制：
   - PKCE 防止授权码被截获后直接换 token
   - state 防止登录 CSRF
   - scope 裁剪防止过度授权
   - role + scope 双重校验防止资源越权

## 七、论文第6章可讲内容

第 6 章可以按下面逻辑写：

1. 对比 `plain` 与 `S256` 两种 PKCE 方式。
2. 对比不同 `code_verifier` 长度的生成耗时。
3. 结论：

```text
S256 的开销很小，但安全性明显强于 plain。
课程项目中推荐默认使用 S256。
verifier 长度采用 48 bytes 能兼顾安全性和性能。
```

## 八、演示时常见问题

### 1. 端口被占用

如果 `8000`、`8001`、`8002` 被占用，先关闭旧服务窗口，或在 `config/settings.py` 修改端口。

### 2. 依赖缺失

重新运行：

```bat
scripts\install_deps.bat
```

### 3. 数据库数据不对

重新初始化：

```bat
scripts\init_db.bat
```

### 4. 攻击实验脚本提示服务不可用

确认 `scripts\run_all.bat` 的窗口还在运行，并且浏览器能打开：

```text
http://127.0.0.1:8001
```


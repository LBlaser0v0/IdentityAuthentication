"""
B同学：访问控制测试矩阵
======================
系统性测试所有 角色 x Scope x 资源 组合，验证 Role + Scope 双重控制。
输出：控制台表格 + CSV 文件（供成员 D 生成图表）

运行方式：
    .venv/Scripts/python tests/test_access_control.py
"""

import csv
import json
import sys
from datetime import timedelta
from pathlib import Path
from typing import Dict, List

# ---- Windows GBK 兼容：强制 stdout 使用 UTF-8 ----
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RESULT_DIR = ROOT / "report_assets"

from shared.database import Base, SessionLocal, engine
from shared.jwt_utils import create_access_token
from shared.models import User
from shared.seed_data import seed_initial_data
from resource_server.routes import get_token_payload, profile, email, admin   # noqa: E402
from config.settings import DEFAULT_CLIENT_ID   # noqa: E402


def ensure_db():
    """初始化数据库并确保种子数据存在"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()


def build_token(*, username: str, role: str, scope: str, client_id: str = DEFAULT_CLIENT_ID):
    """构造指定 role/scope 的 JWT access token"""
    user = _get_user(username)
    payload = {
        "sub": str(user.id),
        "username": username,
        "role": role,
        "scope": scope,
        "client_id": client_id,
    }
    return create_access_token(payload, expires_delta=timedelta(minutes=30))


def _get_user(username: str):
    db = SessionLocal()
    try:
        return db.query(User).filter_by(username=username).first()
    finally:
        db.close()


def call_resource(route_func, token: str):
    """用 Bearer token 调用资源接口，返回 (status_code, body_dict)"""
    authorization = f"Bearer {token}"
    try:
        payload = get_token_payload(authorization=authorization)
        result = route_func(payload=payload)
        return 200, result
    except Exception as exc:
        status_code = getattr(exc, "status_code", 500)
        detail = getattr(exc, "detail", str(exc))
        return status_code, {"error": str(detail)}


def run_matrix():
    """执行访问控制测试矩阵"""
    ensure_db()

    # 定义测试用例：[用户名, 角色, 请求的scope(已裁剪后/granted)]
    test_cases = [
        # === alice (普通用户) ===
        ("alice", "user", "read:profile"),
        ("alice", "user", "read:email"),
        ("alice", "user", "read:profile read:email"),
        ("alice", "user", ""),                         # 权限被完全裁剪的情况
        # === admin (管理员) ===
        ("admin", "admin", "read:profile"),
        ("admin", "admin", "read:email"),
        ("admin", "admin", "admin:panel"),
        ("admin", "admin", "read:profile read:email"),
        ("admin", "admin", "read:profile read:email admin:panel"),
        ("admin", "admin", ""),                        # 空 scope
    ]

    # 定义受保护资源
    resources = [
        ("GET /profile", profile, "read:profile"),
        ("GET /email", email, "read:email"),
        ("GET /admin", admin, "admin:panel + role:admin"),
    ]

    results = []
    print("=" * 100)
    print("Access Control Test Matrix - Member B")
    print("=" * 100)
    header = f"{'Case':<6} {'User':<8} {'Role':<6} {'Granted Scope':<38} {'Resource':<14} {'Required':<28} {'Status':<6} {'Result'}"
    print(header)
    print("-" * 100)

    case_id = 0
    for username, role, granted_scope in test_cases:
        token = build_token(username=username, role=role, scope=granted_scope)
        for res_label, route_func, requirement in resources:
            case_id += 1
            status, body = call_resource(route_func, token)
            passed = status == 200
            result_text = "[ALLOW]" if passed else "[DENY] "
            detail = body.get("message", body.get("error", "")) if not passed else body.get("message", "")

            # 判断是否符合预期
            expected = _expected_result(role, granted_scope, res_label)
            match_str = "PASS" if passed == expected else "FAIL"

            scope_display = granted_scope if granted_scope else "(empty)"
            print(
                f"{case_id:<6} {username:<8} {role:<6} {scope_display:<38} {res_label:<14} {requirement:<28} {status:<6} {result_text} [{match_str}]"
            )

            results.append({
                "case_id": case_id,
                "username": username,
                "role": role,
                "granted_scope": granted_scope if granted_scope else "(empty)",
                "resource": res_label,
                "requirement": requirement,
                "status_code": status,
                "access_granted": passed,
                "expected_granted": expected,
                "correct": passed == expected,
                "detail": detail,
            })

    print("-" * 100)

    # 统计
    total = len(results)
    passed_count = sum(1 for r in results if r["correct"])
    print(f"\nTotal: {total} cases, Expected: {passed_count}, Anomalies: {total - passed_count}")

    return results


def _expected_result(role: str, scope: str, resource: str) -> bool:
    """根据访问控制策略判断是否应该允许访问"""
    scopes = set(scope.split()) if scope else set()
    if resource == "GET /profile":
        return "read:profile" in scopes
    if resource == "GET /email":
        return "read:email" in scopes
    if resource == "GET /admin":
        return "admin:panel" in scopes and role == "admin"
    return False


def export_results(results: List[Dict]):
    """导出结果为 CSV 和 JSON，供成员 D 使用"""
    RESULT_DIR.mkdir(exist_ok=True)

    # CSV - 完整矩阵
    csv_path = RESULT_DIR / "access_control_matrix.csv"
    fields = ["case_id", "username", "role", "granted_scope", "resource",
              "requirement", "status_code", "access_granted", "expected_granted",
              "correct", "detail"]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nCSV exported: {csv_path}")

    # JSON
    json_path = RESULT_DIR / "access_control_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"JSON exported: {json_path}")

    # 权限矩阵摘要表（适合直接放入论文）
    summary_path = RESULT_DIR / "access_control_summary.csv"
    _export_summary(results, summary_path)
    print(f"Summary matrix exported: {summary_path}")


def _export_summary(results: List[Dict], path: Path):
    """生成 用户x资源 的权限矩阵摘要表"""
    users = ["alice (user)", "admin (admin)"]
    resources = ["GET /profile", "GET /email", "GET /admin"]

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["User \\ Resource"] + resources)
        for user in users:
            row = [user]
            for res in resources:
                username = user.split()[0]
                # 找该用户在该资源下有完整 scope 的记录（允许访问）
                entries = [r for r in results
                           if r["username"] == username
                           and r["resource"] == res
                           and r["access_granted"]]
                row.append("ALLOW" if entries else "DENY")
            writer.writerow(row)

        writer.writerow([])
        writer.writerow(["Note"])
        writer.writerow(["alice: role=user, scopes=read:profile read:email"])
        writer.writerow(["admin: role=admin, scopes=read:profile read:email admin:panel"])


def print_paper_material():
    """打印论文可直接使用的访问控制策略说明"""
    print("\n" + "=" * 60)
    print("Paper Material: Access Control Policy Table")
    print("=" * 60)
    print("""
+------------------+--------------+--------------+--------------+
| User / Resource  | /profile     | /email       | /admin       |
+------------------+--------------+--------------+--------------+
| alice (user)     | ALLOW        | ALLOW        | DENY         |
| admin (admin)    | ALLOW        | ALLOW        | ALLOW        |
+------------------+--------------+--------------+--------------+

Access Control Rules:
  /profile  -> requires scope: read:profile
  /email    -> requires scope: read:email
  /admin    -> requires scope: admin:panel AND role: admin (dual control)

Scope Clipping:
  - alice requests admin:panel -> clipped, token has no admin:panel
  - admin requests admin:panel -> retained, token has admin:panel
""")


if __name__ == "__main__":
    results = run_matrix()
    export_results(results)
    print_paper_material()

    # 如果有异常用例，退出码非0
    anomalies = [r for r in results if not r["correct"]]
    if anomalies:
        print(f"\nWARNING: {len(anomalies)} anomalous case(s)!")
        for a in anomalies:
            print(f"  Case {a['case_id']}: {a['username']} -> {a['resource']} "
                  f"(scope={a['granted_scope']}, expected_granted={a['expected_granted']}, "
                  f"got status={a['status_code']})")
        sys.exit(1)
    else:
        print("\nAll access control tests passed.")

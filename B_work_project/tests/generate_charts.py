"""
B同学：访问控制图表生成器
========================
从 access_control_results.json 读取测试数据，生成论文用图表。
供成员 D 直接使用。

运行方式：
    .venv/Scripts/python tests/generate_charts.py

输出：report_assets/ 目录下的 PNG 图片
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RESULT_DIR = ROOT / "report_assets"

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def load_results() -> List[Dict]:
    path = RESULT_DIR / "access_control_results.json"
    if not path.exists():
        print(f"Error: {path} not found. Run tests/test_access_control.py first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def chart_1_access_matrix(results: List[Dict]):
    """图1：权限矩阵热力图（2用户 x 3资源）"""
    users = ["alice\n(user)", "admin\n(admin)"]
    resources = ["GET /profile", "GET /email", "GET /admin"]

    # 构建矩阵: 1=允许, 0=拒绝
    matrix = []
    for uname in ["alice", "admin"]:
        row = []
        for res in resources:
            entry = [r for r in results
                     if r["username"] == uname
                     and r["resource"] == res
                     and r["access_granted"]]
            row.append(1 if entry else 0)
        matrix.append(row)

    fig, ax = plt.subplots(figsize=(7, 3.5))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")

    # 标注
    for i in range(2):
        for j in range(3):
            text = "ALLOW" if matrix[i][j] else "DENY"
            color = "white" if matrix[i][j] == 0 else "black"
            ax.text(j, i, text, ha="center", va="center", fontsize=13, fontweight="bold", color=color)

    ax.set_xticks(range(3))
    ax.set_xticklabels(resources, fontsize=11)
    ax.set_yticks(range(2))
    ax.set_yticklabels(users, fontsize=11)
    ax.set_title("Access Control Matrix: Role + Scope Double Control", fontsize=13, fontweight="bold", pad=12)

    # 图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#4CAF50", label="Access Granted"),
        Patch(facecolor="#F44336", label="Access Denied"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", bbox_to_anchor=(1.35, 0.5), fontsize=10)

    fig.tight_layout()
    path = RESULT_DIR / "chart_access_matrix.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {path}")


def chart_2_allow_deny_bar(results: List[Dict]):
    """图2：每个用户的 允许/拒绝 数量柱状图"""
    users = ["alice", "admin"]
    allow_counts = []
    deny_counts = []

    for uname in users:
        user_results = [r for r in results if r["username"] == uname]
        allow = sum(1 for r in user_results if r["access_granted"])
        deny = sum(1 for r in user_results if not r["access_granted"])
        allow_counts.append(allow)
        deny_counts.append(deny)

    fig, ax = plt.subplots(figsize=(6, 4))
    x = range(len(users))
    width = 0.35
    bars1 = ax.bar([i - width/2 for i in x], allow_counts, width, label="Allow", color="#4CAF50", edgecolor="white")
    bars2 = ax.bar([i + width/2 for i in x], deny_counts, width, label="Deny", color="#F44336", edgecolor="white")

    # 柱上标数字
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                str(int(bar.get_height())), ha="center", fontsize=12, fontweight="bold")
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                str(int(bar.get_height())), ha="center", fontsize=12, fontweight="bold")

    ax.set_xticks(list(x))
    ax.set_xticklabels(["alice\n(user)", "admin\n(admin)"], fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("Access Control Results by User (30 Test Cases)", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.set_ylim(0, max(allow_counts + deny_counts) + 3)

    fig.tight_layout()
    path = RESULT_DIR / "chart_allow_deny_bar.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {path}")


def chart_3_scope_detail(results: List[Dict]):
    """图3：按 Scope 组合分组的资源访问结果"""
    scope_labels = [
        "read:profile",
        "read:email",
        "read:profile\nread:email",
        "admin:panel",
        "all three",
        "(empty)",
    ]

    # 为每个 scope 标签统计 /profile, /email, /admin 的允许情况
    scope_map = {
        "read:profile": ("alice", "read:profile"),
        "read:email": ("alice", "read:email"),
        "read:profile\nread:email": ("alice", "read:profile read:email"),
        "admin:panel": ("admin", "admin:panel"),
        "all three": ("admin", "read:profile read:email admin:panel"),
        "(empty)": ("alice", ""),
    }

    resources = ["GET /profile", "GET /email", "GET /admin"]
    data = {res: [] for res in resources}

    for label, (username, scope) in scope_map.items():
        for res in resources:
            entry = [r for r in results
                     if r["username"] == username
                     and r["resource"] == res
                     and r["granted_scope"] == scope
                     and r["access_granted"]]
            data[res].append(1 if entry else 0)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = range(len(scope_labels))
    width = 0.25
    colors = ["#2196F3", "#FF9800", "#9C27B0"]

    for i, (res, vals) in enumerate(data.items()):
        offset = (i - 1) * width
        bars = ax.bar([xi + offset for xi in x], vals, width, label=res.split()[-1], color=colors[i], edgecolor="white")
        for bar in bars:
            if bar.get_height() > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                        "ALLOW", ha="center", fontsize=8, fontweight="bold", rotation=90)

    ax.set_xticks(list(x))
    ax.set_xticklabels(scope_labels, fontsize=9)
    ax.set_ylabel("Access Granted (1=Yes, 0=No)", fontsize=10)
    ax.set_title("Access Control by Granted Scope (Role + Scope Dual Control)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, loc="upper right")
    ax.set_ylim(0, 1.5)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))

    fig.tight_layout()
    path = RESULT_DIR / "chart_scope_detail.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {path}")


def chart_4_summary_table(results: List[Dict]):
    """图4：论文用权限矩阵表（纯表格图）"""
    fig, ax = plt.subplots(figsize=(6, 2.2))
    ax.axis("off")

    col_labels = ["Resource", "Required Scope", "Role Check", "alice (user)", "admin (admin)"]
    rows = [
        ["GET /profile", "read:profile", "No", "ALLOW", "ALLOW"],
        ["GET /email",   "read:email",   "No", "ALLOW", "ALLOW"],
        ["GET /admin",   "admin:panel",  "Yes (admin)", "DENY", "ALLOW"],
    ]

    table = ax.table(
        cellText=rows,
        colLabels=col_labels,
        cellLoc="center",
        loc="center",
        colWidths=[0.15, 0.18, 0.18, 0.2, 0.2],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.6)

    # 着色
    for i in range(len(rows)):
        for j in range(len(col_labels)):
            cell = table[i + 1, j]
            if j >= 3:  # 结果列
                if rows[i][j] == "ALLOW":
                    cell.set_facecolor("#C8E6C9")
                else:
                    cell.set_facecolor("#FFCDD2")
            elif j == 2 and rows[i][j] == "Yes (admin)":
                cell.set_facecolor("#FFF9C4")

    # 表头着色
    for j in range(len(col_labels)):
        table[0, j].set_facecolor("#37474F")
        table[0, j].set_text_props(color="white", fontweight="bold")

    ax.set_title("Access Control Policy Matrix", fontsize=13, fontweight="bold", pad=12)

    fig.tight_layout()
    path = RESULT_DIR / "chart_summary_table.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {path}")


def main():
    print("Generating access control charts...")
    results = load_results()

    chart_1_access_matrix(results)
    chart_2_allow_deny_bar(results)
    chart_3_scope_detail(results)
    chart_4_summary_table(results)

    print(f"\nDone. {len(list(RESULT_DIR.glob('chart_*.png')))} charts saved to {RESULT_DIR}/")


if __name__ == "__main__":
    main()

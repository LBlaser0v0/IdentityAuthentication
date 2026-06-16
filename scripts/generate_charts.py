"""为C同学论文第5、6章生成实验图表。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ── 中文字体设置 ──
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = ROOT / "report_assets"
OUT.mkdir(parents=True, exist_ok=True)

# ── 读取数据 ──
with open(ROOT / "attack_simulator" / "results" / "latest_results.json", encoding="utf-8") as f:
    data = json.load(f)

# ── 1. 攻击实验结果汇总表（第5章）── 用手绘风格横向对比图代替纯表格
attack_results = [r for r in data if r["experiment"] in ("authorization_code_interception", "login_csrf", "scope_abuse")]

exp_map = {
    "authorization_code_interception": "授权码截获",
    "login_csrf": "登录CSRF",
    "scope_abuse": "Scope滥用",
}
def_map = {
    "no_pkce": "无PKCE",
    "pkce_s256": "S256 PKCE",
    "missing_saved_state": "无本地state",
    "missing_query_state": "缺少回调state",
    "state_mismatch": "state不匹配",
    "user_requests_admin_scope": "alice请求admin",
    "admin_requests_admin_scope": "admin请求admin",
}

fig, ax = plt.subplots(figsize=(14, 5))
ax.axis("off")

col_labels = ["实验", "场景", "攻击成功?", "Token", "资源", "耗时(ms)", "关键结论"]
rows = []
cell_colors = []
for r in attack_results:
    success = "是 (成功)" if r["attack_success"] else "否 (被阻止)"
    token_s = str(r["token_status"]) if r["token_status"] else "-"
    resource_s = str(r["resource_status"]) if r["resource_status"] else "-"
    reason_short = r["reason"][:50]
    rows.append([
        exp_map.get(r["experiment"], r["experiment"]),
        def_map.get(r["defense"], r["defense"]),
        success,
        token_s,
        resource_s,
        f"{r['elapsed_ms']:.0f}",
        reason_short,
    ])
    # 攻击成功行标红，攻击被阻止行标绿
    if r["attack_success"]:
        cell_colors.append(["#FFD7D7"] * 7)
    else:
        cell_colors.append(["#D7F0D7"] * 7)

table = ax.table(cellText=rows, colLabels=col_labels, cellLoc="center", loc="center",
                 cellColours=cell_colors)
table.auto_set_font_size(False)
table.set_fontsize(9.5)
table.scale(1.0, 1.7)
for key, cell in table.get_celld().items():
    cell.set_edgecolor("#cccccc")
    cell.set_text_props(color="#222222")
    if key[0] == 0:
        cell.set_facecolor("#4472C4")
        cell.set_text_props(color="white", fontweight="bold", fontsize=10)
    # 加粗"否 (被阻止)"单元格
    if key[0] > 0 and key[1] == 2 and "否" in str(cell.get_text()):
        cell.set_text_props(color="#C0504D", fontweight="bold")

fig.tight_layout(pad=0.5)
fig.savefig(OUT / "ch5_attack_results_table.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ── 2. 授权码截获攻击对比图 ──
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
scenarios = ["无PKCE", "S256 PKCE"]
success_vals = [1, 0]
colors = ["#C0504D", "#4BACC6"]
bars = axes[0].bar(scenarios, success_vals, color=colors, width=0.4, edgecolor="white")
axes[0].set_ylim(0, 1.2)
axes[0].set_ylabel("攻击成功")
axes[0].set_title("授权码截获攻击结果", fontsize=13, fontweight="bold")
axes[0].set_yticks([0, 1])
axes[0].set_yticklabels(["失败", "成功"])
for bar, val in zip(bars, success_vals):
    axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.03,
                 "攻击成功" if val else "攻击失败", ha="center", fontsize=11, fontweight="bold")

times = [346.39, 166.38]
axes[1].bar(scenarios, times, color=colors, width=0.4, edgecolor="white")
axes[1].set_ylabel("耗时 (ms)")
axes[1].set_title("实验耗时对比", fontsize=13, fontweight="bold")
for bar, t in zip(bars, times):
    axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3, f"{t}ms", ha="center", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "ch5_code_interception.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ── 3. 登录CSRF实验结果图 ── 用HTTP状态码柱状图 + 攻击成功/失败标签
fig, ax = plt.subplots(figsize=(9, 5))
csrf_scenarios = ["无本地state\n(missing saved state)", "缺少回调state\n(missing query state)", "state不匹配\n(state mismatch)"]
csrf_status_codes = [400, 400, 400]  # 全部返回400表示被阻止
csrf_colors = ["#4BACC6", "#4BACC6", "#4BACC6"]
bars = ax.bar(csrf_scenarios, csrf_status_codes, color=csrf_colors, width=0.45, edgecolor="white")
ax.set_ylim(0, 500)
ax.set_ylabel("HTTP 状态码", fontsize=12)
ax.set_title("登录CSRF攻击实验结果 — 全部被阻止", fontsize=14, fontweight="bold")
ax.axhline(y=400, color="#C0504D", linewidth=1, linestyle="--", alpha=0.35)
for bar, code in zip(bars, csrf_status_codes):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 8,
            f"{code}\n(攻击被阻止)", ha="center", fontsize=12, fontweight="bold", color="#C0504D")
# 底部添加错误信息标注
error_msgs = [
    '"missing saved state"',
    '"missing state"',
    '"state mismatch"',
]
for bar, msg in zip(bars, error_msgs):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2,
            msg, ha="center", fontsize=9, color="white", fontweight="bold")
fig.tight_layout()
fig.savefig(OUT / "ch5_login_csrf.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ── 4. Scope滥用结果对比图 ──
fig, ax = plt.subplots(figsize=(8, 4))
scope_users = ["alice\n(普通用户)", "admin\n(管理员)"]
scope_codes = [403, 200]
scope_colors = ["#C0504D", "#9BBB59"]
bars = ax.bar(scope_users, scope_codes, color=scope_colors, width=0.35, edgecolor="white")
ax.set_ylabel("/admin 接口HTTP状态码")
ax.set_title("Scope滥用实验 — /admin访问结果", fontsize=13, fontweight="bold")
ax.set_ylim(0, 500)
ax.axhline(y=200, color="#9BBB59", linewidth=1, linestyle="--", alpha=0.4)
ax.axhline(y=403, color="#C0504D", linewidth=1, linestyle="--", alpha=0.4)
for bar, code in zip(bars, scope_codes):
    label = "允许访问" if code == 200 else "拒绝访问"
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10,
            f"{code} ({label})", ha="center", fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(OUT / "ch5_scope_abuse.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ── 5. PKCE性能对比图（第6章） ──
pkce_data = [r for r in data if r["experiment"] == "pkce_performance"]
methods = ["plain", "S256"]
lengths = [32, 48, 64, 96]

# 5a. 分方法分长度的avg耗时柱状图
fig, ax = plt.subplots(figsize=(10, 5.5))
x = np.arange(len(lengths))
width = 0.35
for i, method in enumerate(methods):
    avg_vals = []
    for length in lengths:
        for r in pkce_data:
            if r["evidence"]["method"] == method and r["evidence"]["verifier_length_bytes"] == length:
                avg_vals.append(r["evidence"]["avg_ms"] * 1000)  # convert to μs
                break
    bars = ax.bar(x + i * width, avg_vals, width, label=f"{method}",
                  color=["#5B9BD5", "#ED7D31"][i], edgecolor="white")
    for bar, val in zip(bars, avg_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{val:.1f}", ha="center", fontsize=8)

ax.set_xlabel("Code Verifier 长度 (bytes)")
ax.set_ylabel("平均耗时 (μs)")
ax.set_title("PKCE Code Verifier + Challenge 生成性能对比 (n=300)", fontsize=13, fontweight="bold")
ax.set_xticks(x + width / 2)
ax.set_xticklabels(lengths)
ax.legend(loc="upper left")
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
fig.tight_layout()
fig.savefig(OUT / "ch6_pkce_avg_comparison.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# 5b. P95耗时对比图
fig, ax = plt.subplots(figsize=(10, 5.5))
for i, method in enumerate(methods):
    p95_vals = []
    for length in lengths:
        for r in pkce_data:
            if r["evidence"]["method"] == method and r["evidence"]["verifier_length_bytes"] == length:
                p95_vals.append(r["evidence"]["p95_ms"] * 1000)
                break
    bars = ax.bar(x + i * width, p95_vals, width, label=f"{method}",
                  color=["#5B9BD5", "#ED7D31"][i], edgecolor="white")
    for bar, val in zip(bars, p95_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{val:.1f}", ha="center", fontsize=8)

ax.set_xlabel("Code Verifier 长度 (bytes)")
ax.set_ylabel("P95 耗时 (μs)")
ax.set_title("PKCE P95 耗时对比 (n=300)", fontsize=13, fontweight="bold")
ax.set_xticks(x + width / 2)
ax.set_xticklabels(lengths)
ax.legend(loc="upper left")
fig.tight_layout()
fig.savefig(OUT / "ch6_pkce_p95_comparison.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# 5c. Max耗时对比图
fig, ax = plt.subplots(figsize=(10, 5.5))
for i, method in enumerate(methods):
    max_vals = []
    for length in lengths:
        for r in pkce_data:
            if r["evidence"]["method"] == method and r["evidence"]["verifier_length_bytes"] == length:
                max_vals.append(r["evidence"]["max_ms"] * 1000)
                break
    bars = ax.bar(x + i * width, max_vals, width, label=f"{method}",
                  color=["#5B9BD5", "#ED7D31"][i], edgecolor="white")
    for bar, val in zip(bars, max_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{val:.1f}", ha="center", fontsize=8)

ax.set_xlabel("Code Verifier 长度 (bytes)")
ax.set_ylabel("最大耗时 (μs)")
ax.set_title("PKCE 最大耗时对比 (n=300)", fontsize=13, fontweight="bold")
ax.set_xticks(x + width / 2)
ax.set_xticklabels(lengths)
ax.legend(loc="upper left")
fig.tight_layout()
fig.savefig(OUT / "ch6_pkce_max_comparison.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# 5d. 综合对比：plain vs S256 (48 bytes典型值)
fig, axes = plt.subplots(1, 3, figsize=(12, 4.5))
metrics = ["avg_ms", "p95_ms", "max_ms"]
titles = ["平均耗时 (ms)", "P95耗时 (ms)", "最大耗时 (ms)"]
for ax_i, (metric, title) in enumerate(zip(metrics, titles)):
    vals_48 = {}
    for r in pkce_data:
        if r["evidence"]["verifier_length_bytes"] == 48:
            vals_48[r["evidence"]["method"]] = r["evidence"][metric]
    bars = axes[ax_i].bar(["plain", "S256"], [vals_48.get("plain", 0) * 1000, vals_48.get("S256", 0) * 1000],
                          color=["#5B9BD5", "#ED7D31"], width=0.4, edgecolor="white")
    axes[ax_i].set_title(title)
    for bar, val in zip(bars, [vals_48.get("plain", 0) * 1000, vals_48.get("S256", 0) * 1000]):
        axes[ax_i].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                        f"{val:.2f}μs", ha="center", fontsize=10)
fig.suptitle("PKCE性能: plain vs S256 (verifier=48 bytes, n=300)", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(OUT / "ch6_pkce_48bytes_detail.png", dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"Charts saved to {OUT}/")
for f in sorted(OUT.glob("*.png")):
    print(f"  {f.name}")

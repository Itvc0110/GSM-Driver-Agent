"""Sinh 4 biểu đồ cho Week 2 Report — ĐỌC SỐ TỪ ARTIFACT JSON, không hard-code.

Chạy: uv run python docs/reports/week2/make_figures.py

Nguyên tắc: mọi con số trên hình phải truy được về một file artifact trong
`research/audit/2026-07-27-current-state/`. Nếu artifact thiếu khoá, script FAIL LOUD (KeyError)
thay vì vẽ số bịa — vì một hình sai đắt hơn một hình thiếu.
"""
from __future__ import annotations

import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = pathlib.Path(__file__).resolve().parents[3]
ART = ROOT / "research/audit/2026-07-27-current-state"
OUT = pathlib.Path(__file__).resolve().parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

# Bảng màu — lấy từ dashboard_theme để report và dashboard nói cùng một ngôn ngữ màu
XANH, DUONG, AMBER, TIM, HONG = "#199e70", "#3987e5", "#c98500", "#9085e9", "#d55181"
XAM, XAM_NHAT = "#5b6b67", "#c9d4d1"
plt.rcParams.update({
    "font.family": "DejaVu Sans",   # hỗ trợ dấu tiếng Việt
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": XAM, "axes.labelcolor": "#22302c", "text.color": "#22302c",
    "xtick.color": XAM, "ytick.color": XAM, "figure.dpi": 160,
})
_vnd = FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))


def _load(name: str) -> dict:
    return json.loads((ART / name).read_text(encoding="utf-8"))


def fig_e10_arms() -> str:
    """Forest plot 4 arm E10 + vạch số CŨ (+6.016) để cho thấy nó KHÔNG tái lập được."""
    diff = _load("41-e10-diff.json")
    oracle = diff["stop1_delta_oracle"]
    arms = diff["arms"]
    rows = [
        ("B_oracle\n(biết λ thật — trần)", oracle["mean"], oracle["ci"], XANH),
        ("B_hist\n(prior lịch sử)", arms["hist"]["delta_vs_A"]["mean"], arms["hist"]["delta_vs_A"]["ci"], DUONG),
        ("B_real\n($\hat\lambda$ tự học)", arms["real"]["delta_vs_A"]["mean"], arms["real"]["delta_vs_A"]["ci"], TIM),
        ("B_wait\n(trigger chờ-lâu T=30′)", arms["wait"]["delta_vs_A"]["mean"], arms["wait"]["delta_vs_A"]["ci"], HONG),
    ]
    ref_cu = oracle.get("ref_update087")

    fig, ax = plt.subplots(figsize=(8.6, 4.1))
    ys = list(range(len(rows)))[::-1]
    for y, (lab, m, ci, c) in zip(ys, rows):
        ax.plot(ci, [y, y], color=c, lw=3, alpha=.35, solid_capstyle="round")
        ax.plot([m], [y], "o", color=c, ms=9, zorder=3)
        ax.annotate(f"{m:+,.0f}đ".replace(",", "."), (m, y), textcoords="offset points",
                    xytext=(0, -19), ha="center", fontsize=9.5, fontweight="bold", color=c)
    ax.axvline(0, color=XAM, lw=1, ls="-", zorder=1)
    if ref_cu:
        ax.axvline(ref_cu, color="#b03030", lw=1.4, ls="--", zorder=2)
        ax.annotate(f"+{ref_cu:,}đ".replace(",", ".") + " — số CŨ (UPDATE-087)\nKHÔNG tái lập được",
                    (ref_cu, len(rows) - 0.72), fontsize=8.4, color="#b03030", ha="right",
                    xytext=(-8, 0), textcoords="offset points", style="italic")
    ax.set_yticks(ys, [r[0] for r in rows], fontsize=9)
    ax.set_xlabel("Δ payout trung bình / tài xế / ngày (VNĐ) — MOCK, n=100 seed ghép cặp CRN")
    ax.set_title("E10 — advisor mất thông tin λ thì còn lại bao nhiêu giá trị?")
    ax.xaxis.set_major_formatter(_vnd)
    ax.grid(axis="x", color=XAM_NHAT, lw=.6)
    ax.set_axisbelow(True)
    ax.set_ylim(-0.75, len(rows) - 0.30)
    ax.set_xlim(-1200, (ref_cu or 6000) + 700)
    fig.tight_layout()
    p = OUT / "fig-e10-arms.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p.name


def fig_e10b_threshold() -> str:
    """Δ theo ngưỡng T + số can thiệp/ngày — chứng minh KHÔNG mua Δ bằng khối lượng."""
    s = _load("44-e10blow-summary.json")["ket_qua"]
    Ts = sorted(s, key=lambda k: float(k))
    x = [float(t) for t in Ts]
    m = [s[t]["delta_vs_A"]["mean"] for t in Ts]
    lo = [s[t]["delta_vs_A"]["ci"][0] for t in Ts]
    hi = [s[t]["delta_vs_A"]["ci"][1] for t in Ts]
    vol = [s[t]["can_thiep_moi_ngay"] for t in Ts]

    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    ax.fill_between(x, lo, hi, color=XANH, alpha=.16, label="CI 95%")
    ax.plot(x, m, "-o", color=XANH, lw=2.2, ms=7, label="Δ payout vs arm A")
    imax = m.index(max(m))
    ax.annotate(f"đỉnh T={Ts[imax]}′\n{m[imax]:+,.0f}đ".replace(",", ".") + f"\n{s[Ts[imax]]['lop']}",
                (x[imax], m[imax]), textcoords="offset points", xytext=(6, 16),
                fontsize=9, fontweight="bold", color=XANH)
    ax.set_xlabel("Ngưỡng trigger T (phút chờ tại ô)")
    ax.set_ylabel("Δ payout (VNĐ)")
    ax.yaxis.set_major_formatter(_vnd)
    ax.grid(color=XAM_NHAT, lw=.6); ax.set_axisbelow(True)

    ax2 = ax.twinx()
    ax2.plot(x, vol, "--s", color=AMBER, lw=1.6, ms=6, label="can thiệp / ngày")
    ax2.set_ylabel("Số can thiệp / ngày", color=AMBER)
    ax2.tick_params(axis="y", colors=AMBER)
    ax2.spines["right"].set_visible(True); ax2.spines["right"].set_color(AMBER)
    ax2.spines["top"].set_visible(False)

    ax.set_title("E10b — quét ngưỡng trigger: T thấp hơn ⇒ can thiệp NHIỀU hơn nhưng Δ THẤP hơn")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower center", frameon=False, fontsize=8.6, ncol=3)
    fig.tight_layout()
    p = OUT / "fig-e10b-threshold.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p.name


# Hai hình dưới lấy số từ UPDATE (đã trích trong NGUON-SO-LIEU.md) — khai rõ nguồn trên hình.
SUITE = [("UPDATE-102", 850), ("103", 860), ("110", 907), ("111", 939),
         ("113", 959), ("114+115", 990), ("116", 994), ("117", 994), ("118", 1000)]
SIGNFLIP = [("argmax\narm A", -19654, HONG), ("argmax\narm B", 27416, HONG),
            ("mean P4\n(không chọn lọc)", 3610, AMBER), ("toàn đội\n(cohort — ĐANG DÙNG)", 5350, XANH)]


def fig_suite_growth() -> str:
    fig, ax = plt.subplots(figsize=(8.2, 3.0))
    xs = range(len(SUITE))
    ys = [v for _, v in SUITE]
    ax.plot(xs, ys, "-o", color=XANH, lw=2.2, ms=6)
    ax.fill_between(xs, min(ys) - 20, ys, color=XANH, alpha=.10)
    for i, (lab, v) in enumerate(SUITE):
        if lab in ("UPDATE-102", "118"):
            ax.annotate(f"{v:,}".replace(",", "."), (i, v), textcoords="offset points",
                        xytext=(0, 9), ha="center", fontsize=9, fontweight="bold", color=XANH)
    ax.set_xticks(list(xs), [l for l, _ in SUITE], fontsize=8.4)
    ax.set_ylabel("Test PASSED (cả 2 lệnh)")
    ax.set_title("Kỷ luật kiểm thử theo mốc UPDATE — 850 → 1.000 test passed")
    ax.grid(axis="y", color=XAM_NHAT, lw=.6); ax.set_axisbelow(True)
    ax.margins(x=.04)
    fig.tight_layout()
    p = OUT / "fig-suite-growth.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p.name


def fig_estimator_signflip() -> str:
    fig, ax = plt.subplots(figsize=(8.2, 3.4))
    labs = [l for l, _, _ in SIGNFLIP]
    vals = [v for _, v, _ in SIGNFLIP]
    cols = [c for _, _, c in SIGNFLIP]
    bars = ax.bar(labs, vals, color=cols, width=.62)
    ax.axhline(0, color="#22302c", lw=1.2)
    for b, v in zip(bars, vals):
        off = 9 if v > 0 else -18
        ax.annotate(f"{v:+,.0f}đ".replace(",", "."), (b.get_x() + b.get_width() / 2, v),
                    textcoords="offset points", xytext=(0, off), ha="center",
                    fontsize=10, fontweight="bold", color=b.get_facecolor())
    ax.set_ylabel("Δ payout (VNĐ)")
    ax.yaxis.set_major_formatter(_vnd)
    ax.set_title("CÙNG một can thiệp, đổi cách chọn tài xế để đo ⇒ ĐẢO DẤU kết luận")
    ax.annotate("cùng can thiệp B1 · 5 seed · chỉ khác ESTIMATOR",
                (0.5, 0.955), xycoords="axes fraction", ha="center", fontsize=8.6,
                style="italic", color=XAM)
    ax.grid(axis="y", color=XAM_NHAT, lw=.6); ax.set_axisbelow(True)
    fig.tight_layout()
    p = OUT / "fig-estimator-signflip.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p.name


# ============================================================================
# BẢN CHO BÁO CÁO BRIEF — cùng số, nhưng nhãn tiếng Việt dễ hiểu.
# Vì sao có hai bản: bản kỹ thuật cần tên arm và ký hiệu toán để đối chiếu artifact; bản brief
# gửi stakeholder thì tên biến (`B_oracle`, `λ̂`, `KQ-GIỮ`) chỉ làm khó người đọc.
# ============================================================================

def fig_brief_arms() -> str:
    diff = _load("41-e10-diff.json")
    o, arms = diff["stop1_delta_oracle"], diff["arms"]
    rows = [
        ("Biết trước nhu cầu khách\n(giới hạn lý thuyết)", o["mean"], o["ci"], XANH),
        ("Dựa trên số liệu quá khứ", arms["hist"]["delta_vs_A"]["mean"],
         arms["hist"]["delta_vs_A"]["ci"], DUONG),
        ("Tự học từ những gì\nquan sát được", arms["real"]["delta_vs_A"]["mean"],
         arms["real"]["delta_vs_A"]["ci"], TIM),
        ('Chỉ biết "khu này\nđang vắng khách"', arms["wait"]["delta_vs_A"]["mean"],
         arms["wait"]["delta_vs_A"]["ci"], HONG),
    ]
    fig, ax = plt.subplots(figsize=(8.6, 3.5))
    ys = list(range(len(rows)))[::-1]
    for y, (lab, m, ci, c) in zip(ys, rows):
        ax.plot(ci, [y, y], color=c, lw=3.4, alpha=.33, solid_capstyle="round")
        ax.plot([m], [y], "o", color=c, ms=10, zorder=3)
        ax.annotate(f"{m:+,.0f}đ".replace(",", "."), (m, y), textcoords="offset points",
                    xytext=(0, -20), ha="center", fontsize=10.5, fontweight="bold", color=c)
    ax.axvline(0, color=XAM, lw=1.1)
    ax.annotate("không phân biệt được\nvới không làm gì", (rows[-1][1], 0), fontsize=8.6,
                color=HONG, style="italic", ha="left", xytext=(34, 2),
                textcoords="offset points")
    ax.set_yticks(ys, [r[0] for r in rows], fontsize=9.4)
    ax.set_xlabel("Thu nhập tăng thêm mỗi tài xế mỗi ngày (VNĐ) — kết quả mô phỏng")
    ax.set_title("Trợ lý càng ít được biết trước, giá trị còn lại bao nhiêu?")
    ax.xaxis.set_major_formatter(_vnd)
    ax.grid(axis="x", color=XAM_NHAT, lw=.6)
    ax.set_axisbelow(True)
    ax.set_ylim(-0.8, len(rows) - 0.35)
    ax.set_xlim(-1300, 5900)
    fig.tight_layout()
    q = OUT / "fig-brief-arms.png"
    fig.savefig(q, bbox_inches="tight"); plt.close(fig)
    return q.name


def fig_brief_threshold() -> str:
    s = _load("44-e10blow-summary.json")["ket_qua"]
    Ts = sorted(s, key=lambda k: float(k))
    x = [float(t) for t in Ts]
    m = [s[t]["delta_vs_A"]["mean"] for t in Ts]
    vol = [s[t]["can_thiep_moi_ngay"] for t in Ts]
    fig, ax = plt.subplots(figsize=(8.6, 3.3))
    ax.plot(x, m, "-o", color=XANH, lw=2.6, ms=8)
    i = m.index(max(m))
    ax.annotate(f"tốt nhất: {m[i]:+,.0f}đ".replace(",", ".") + f"\n(nói {vol[i]:.0f} lần/ngày)",
                (x[i], m[i]), textcoords="offset points", xytext=(16, -6),
                fontsize=9.6, fontweight="bold", color=XANH, ha="left", va="top")
    ax.set_ylim(min(m) - 320, max(m) + 260)   # chỗ cho nhãn, không đè tiêu đề
    ax.annotate(f"nói NHIỀU hơn ({vol[0]:.0f} lần/ngày)\nnhưng kết quả THẤP hơn",
                (x[0], m[0]), textcoords="offset points", xytext=(8, -36),
                fontsize=9, color=HONG, style="italic")
    ax.set_xlabel("Trợ lý chỉ lên tiếng khi tài xế đã chờ quá … phút")
    ax.set_ylabel("Thu nhập tăng thêm (VNĐ)")
    ax.yaxis.set_major_formatter(_vnd)
    ax.grid(color=XAM_NHAT, lw=.6)
    ax.set_axisbelow(True)
    ax2 = ax.twinx()
    ax2.plot(x, vol, "--s", color=AMBER, lw=1.7, ms=6.5)
    ax2.set_ylabel("Số lần trợ lý lên tiếng / ngày", color=AMBER, fontsize=9.4)
    ax2.tick_params(axis="y", colors=AMBER)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(AMBER)
    ax2.spines["top"].set_visible(False)
    ax.set_title("Nói nhiều hơn KHÔNG cho kết quả tốt hơn")
    fig.tight_layout()
    q = OUT / "fig-brief-threshold.png"
    fig.savefig(q, bbox_inches="tight"); plt.close(fig)
    return q.name


def fig_brief_signflip() -> str:
    labs = ["Chọn người giỏi nhất\nở thế giới KHÔNG trợ lý",
            "Chọn người giỏi nhất\nở thế giới CÓ trợ lý",
            "Trung bình một nhóm\n(không chọn lọc)",
            "Trung bình TOÀN ĐỘI\n(cách đang dùng)"]
    vals = [v for _, v, _ in SIGNFLIP]
    cols = [HONG, HONG, AMBER, XANH]
    fig, ax = plt.subplots(figsize=(8.6, 3.2))
    bars = ax.bar(labs, vals, color=cols, width=.6)
    ax.axhline(0, color="#22302c", lw=1.3)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:+,.0f}đ".replace(",", "."),
                    (b.get_x() + b.get_width() / 2, v), textcoords="offset points",
                    xytext=(0, 10 if v > 0 else -20), ha="center",
                    fontsize=11, fontweight="bold", color=b.get_facecolor())
    ax.annotate("kết luận: trợ lý GÂY HẠI", (0, vals[0]), textcoords="offset points",
                xytext=(0, -40), ha="center", fontsize=8.4, style="italic", color=HONG)
    ax.annotate("kết luận: trợ lý CỰC TỐT", (1, vals[1]), textcoords="offset points",
                xytext=(0, 30), ha="center", fontsize=8.4, style="italic", color=HONG)
    ax.set_ylabel("Thu nhập tăng thêm (VNĐ)")
    ax.yaxis.set_major_formatter(_vnd)
    ax.set_title("CÙNG một dữ liệu — đổi cách chọn người để đo thì kết luận ĐẢO NGƯỢC")
    ax.tick_params(axis="x", labelsize=8.8)
    ax.grid(axis="y", color=XAM_NHAT, lw=.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    q = OUT / "fig-brief-signflip.png"
    fig.savefig(q, bbox_inches="tight"); plt.close(fig)
    return q.name


if __name__ == "__main__":
    for fn in (fig_e10_arms, fig_e10b_threshold, fig_suite_growth, fig_estimator_signflip,
               fig_brief_arms, fig_brief_threshold, fig_brief_signflip):
        print("  đã sinh:", fn())

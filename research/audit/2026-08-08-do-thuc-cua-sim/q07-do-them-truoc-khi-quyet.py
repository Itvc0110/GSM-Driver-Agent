"""Q-07 — hai phép đo Cường yêu cầu TRƯỚC khi quyết. KHÔNG đổi một dòng code sản phẩm.

# Câu 1 — lời khuyên `P1b` tôi vừa ship có QUY SAI NGUYÊN NHÂN không?

`P1b` cảnh báo tài xế trong dải sát ngưỡng thưởng: *"tỷ lệ nhận đang sát ngưỡng — thêm vài lần
**từ chối** nữa có thể mất toàn bộ thưởng ngày dù đủ điểm"*.

Nhưng `acceptance_rate` đếm cả lượt bị chặn vì **pin** (`order_skipped_soc`) — lượt tài xế **chưa
từng được hỏi**. Nếu một tài xế nằm trong dải đó **vì pin** chứ không vì từ chối, thì lời khuyên
bảo họ *"đừng từ chối nữa"* là **chỉ sai việc phải làm**: việc đúng của họ là **đi đổi pin sớm**.

**Đo:** trong số tài xế mà tỷ lệ nhận (NHIỄM) rơi vào dải cảnh báo, bao nhiêu người có tỷ lệ
**SẠCH** đã nằm ngoài dải — tức lẽ ra **không đáng bị cảnh báo**.

# Câu 2 — k=8 với mẫu số SẠCH có qua được cổng realism không?

Nếu qua, thì Q-07 **tự tan**: không phải chọn giữa *"ghép đơn đúng"* và *"trung thành archetype"*
nữa — sửa thước đo là được cả hai, kèm **−32,6 đơn chết/ngày**.

Nếu **không** qua, thì vẫn còn một đánh đổi thật và Cường vẫn phải quyết.

⚠ Dung sai lấy TỪ chính test (`ACCEPT_TOL_PP`), không tự đặt.

Chạy: uv run python research/audit/2026-08-08-do-thuc-cua-sim/q07-do-them-truoc-khi-quyet.py
"""
from __future__ import annotations

import json
import pathlib
import statistics as st
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gsm_sim.archetypes import ARCHETYPES      # noqa: E402
from gsm_sim.config import Config              # noqa: E402
from gsm_sim.parallel import _cfg_with         # noqa: E402
from gsm_sim.runner import run_once            # noqa: E402

SEEDS = list(range(3300, 3320))
OUT = pathlib.Path(__file__).with_suffix(".json")
CLIFF_MARGIN = 0.03      # `f3_patterns.DEFAULT["cliff_margin"]` — dải sát ngưỡng của P1b


def _tol() -> float:
    """Dung sai lấy TỪ test, không tự đặt — nếu test đổi thì phép đo này đổi theo."""
    import re
    src = (ROOT / "tests/test_sim_realism.py").read_text(encoding="utf-8")
    m = re.search(r"ACCEPT_TOL_PP\s*=\s*([0-9.]+)", src)
    if not m:
        print("⛔ DỪNG — không đọc được `ACCEPT_TOL_PP` từ test; không tự bịa dung sai.")
        sys.exit(1)
    return float(m.group(1))


def main() -> None:
    tol = _tol()
    base_cfg = yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8"))
    thr = float(base_cfg["policy"]["bonus_min_acceptance"])
    print(f"ngưỡng thưởng = {thr} · dải cảnh báo P1b = [{thr:.2f}; {thr + CLIFF_MARGIN:.2f}) · "
          f"dung sai realism = {tol:.2%} (đọc từ test)\n")

    out: dict = {"nguong": thr, "cliff_margin": CLIFF_MARGIN, "tol": tol, "seeds": SEEDS}

    # ---------------- CÂU 1: dải cảnh báo P1b (k hiện hành) ----------------
    cfg = Config(base_cfg, ROOT)
    trong_dai = 0
    sach_ngoai_dai = 0
    sach_tren_nguong = 0
    vi_du = []
    for seed in SEEDS:
        r = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
        for a in r.actors:
            off, skip, acc = a.orders_offered, a.orders_soc_skipped, a.orders_accepted
            if not off:
                continue
            nhiem = acc / off
            if not (thr <= nhiem < thr + CLIFF_MARGIN):
                continue
            trong_dai += 1
            sach = acc / (off - skip) if off > skip else 1.0
            if sach >= thr + CLIFF_MARGIN:
                sach_ngoai_dai += 1
                if len(vi_du) < 3:
                    vi_du.append({"seed": seed, "arch": a.archetype, "nhiem": round(nhiem, 4),
                                  "sach": round(sach, 4), "offered": off, "skip_pin": skip})
            if sach >= thr:
                sach_tren_nguong += 1

    print("=== CÂU 1 — lời khuyên P1b có quy sai nguyên nhân không? ===")
    print(f"  tài xế rơi vào dải cảnh báo (tỷ lệ NHIỄM): {trong_dai}")
    if trong_dai:
        print(f"  … nhưng tỷ lệ SẠCH đã NGOÀI dải  ⇒ lẽ ra KHÔNG bị cảnh báo: "
              f"{sach_ngoai_dai} = {sach_ngoai_dai / trong_dai:.1%}")
        print(f"  … tỷ lệ SẠCH vẫn ≥ ngưỡng (không mất thưởng): "
              f"{sach_tren_nguong} = {sach_tren_nguong / trong_dai:.1%}")
        for v in vi_du:
            print(f"     ví dụ {v['arch']} seed {v['seed']}: nhiễm {v['nhiem']:.4f} → "
                  f"sạch {v['sach']:.4f} ({v['skip_pin']}/{v['offered']} lượt bị chặn vì pin)")
    out["cau1"] = {"trong_dai": trong_dai, "sach_ngoai_dai": sach_ngoai_dai,
                   "sach_tren_nguong": sach_tren_nguong, "vi_du": vi_du}

    # ---------------- CÂU 2: k=8 với mẫu số SẠCH ----------------
    print("\n=== CÂU 2 — k=8 với mẫu số SẠCH có qua cổng realism không? ===")
    ket_k: dict = {}
    for k in (6, 8):
        blob = json.loads(json.dumps(base_cfg))
        blob["dispatcher"]["candidate_ring_k_max"] = k
        c = Config(blob, ROOT)
        cong: dict[str, list[int]] = {}
        for seed in SEEDS:
            r = run_once(_cfg_with(c, enabled=False, actor_id=None, channels=None), seed)
            for a in r.actors:
                if not a.orders_offered:
                    continue
                cur = cong.setdefault(a.archetype, [0, 0, 0])
                cur[0] += a.orders_accepted
                cur[1] += a.orders_offered
                cur[2] += a.orders_soc_skipped
        ket_k[k] = {n: {"nhiem": acc / off,
                        "sach": acc / (off - sk) if off > sk else float("nan"),
                        "base": ARCHETYPES[n].accept_base}
                    for n, (acc, off, sk) in sorted(cong.items()) if off > 0}

    print(f"{'arch':<6}{'base':>7}{'k=6 sạch':>11}{'lệch':>9}{'k=8 sạch':>11}{'lệch':>9}  cổng k=8")
    print("-" * 70)
    truot = []
    for n in sorted(ket_k[8]):
        b = ket_k[8][n]["base"]
        s6, s8 = ket_k[6][n]["sach"], ket_k[8][n]["sach"]
        l8 = s8 - b
        ok = abs(l8) <= tol
        if not ok:
            truot.append(n)
        print(f"{n:<6}{b:>7.2f}{s6:>11.4f}{s6 - b:>+9.4f}{s8:>11.4f}{l8:>+9.4f}"
              f"   {'✅ qua' if ok else '❌ TRƯỢT'}")
    out["cau2"] = {"k": {str(k): v for k, v in ket_k.items()}, "truot_k8_sach": truot}

    print("\n=== ĐỌC CHO ĐÚNG ===")
    if not truot:
        print("  → Với mẫu số SẠCH, k=8 QUA cổng realism ở CẢ 7 archetype.")
        print("    ⇒ **Q-07 TỰ TAN**: không còn phải chọn giữa 'ghép đơn đúng' và 'trung thành")
        print("      archetype'. Sửa thước đo là được cả hai, kèm −32,6 đơn chết/ngày.")
        print("    ⚠ Vẫn phải plan mode: sửa mẫu số ĐỔI PAYOUT ⇒ đo lại mọi số cũ.")
    else:
        print(f"  → k=8 sạch VẪN trượt ở: {truot} ⇒ đánh đổi vẫn còn thật, Cường vẫn phải quyết.")
        print("    Nhưng độ lớn đánh đổi nay đo trên đại lượng SẠCH, không phải đại lượng nhiễm.")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()

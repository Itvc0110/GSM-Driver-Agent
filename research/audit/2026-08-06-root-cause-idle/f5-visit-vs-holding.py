"""F5 — GIẾNG SÂU hay LƯU VỰC RỘNG? Đo lượt-ghé vs thời-gian-giữ theo ô trong run thật.

    uv run python research/audit/2026-08-06-root-cause-idle/f5-visit-vs-holding.py

## Giả thuyết (câu `UNRESOLVED` còn lại)

Quan sát: **56,6%** phút idle của đội dồn vào `953`+`bb3` (rc-03). Nhưng:
- F1 đo **độ RỘNG lưu vực** (bao nhiêu ô khởi đầu chảy về đó) ⇒ `953` chỉ **7,1%** ở bậc n=0 hiệu dụng,
  và cặp rộng nhất lại là `88f`+`8c7`.
- F3 bác giả thuyết vị trí khởi đầu (`home_cell`).
- F4 cho biết **73%** quyết định ở bậc n=0 (ring 1, bar 1,25 — rất kén).

⇒ **Giả thuyết F5: `953`/`bb3` không phải lưu vực RỘNG mà là GIẾNG SÂU** — ít người vào nhưng **giữ rất
lâu**, vì chúng là **cực đại địa phương ở ring 1** với ngưỡng `bar = 1,25`: đứng đó thì **không ô nào
trong 0,37 km trông hơn 25%**, nên tài xế WAIT mãi. Phút idle tích lũy = (số lượt vào) × (thời gian giữ);
F1 chỉ đo vế đầu, **chưa bao giờ đo vế sau**.

**Falsifier:** nếu thời gian giữ của `953`/`bb3` **không** cao hơn hẳn các ô khác ⇒ giả thuyết ĐỔ, phải
tìm chỗ khác (và tôi phải nói ra, như bốn lần trước).

## Cách đo — pass-through, có cổng nhiễu-loạn

Bọc `behavior.consider_relocate` (⚠ **namespace `behavior`**, không phải `world` — bẫy F4 đã sập) để ghi
`(cell, action, target)` mỗi quyết định đứng-chỗ. Từ đó:
- `wait[cell]`   = số quyết định WAIT tại ô ⇒ phút idle ≈ `2′ × wait[cell]` (nhánh WAIT cộng đúng 2′)
- `arrive[cell]` = số quyết định RELOCATE **nhắm tới** ô ⇒ số lượt vào
- `giữ[cell]`    = phút idle / lượt vào

Cổng: `fingerprint_actors` có/không instrument phải **IDENTICAL**.
Nhãn: **MOCK/SIM**, arm A (mọi kênh tắt).
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim import behavior as behavior_mod                      # noqa: E402
from gsm_sim.behavior import IdleAction                           # noqa: E402
from gsm_sim.config import Config                                 # noqa: E402
from gsm_sim.runner import run_once                               # noqa: E402
from gsm_sim.sim_metrics import fingerprint_actors                # noqa: E402

OUT = Path(__file__).resolve().parent / "f5-visit-vs-holding.json"
SEEDS = [1000, 1001, 1002, 1003, 1004]
O_HUT = ["89415cb4953ffff", "89415cb4bb3ffff"]          # rc-03: giữ 56,6% phút idle nền
F1_RONG = ["89415cb488fffff", "89415cb48c7ffff"]        # F1: lưu vực rộng nhất (42,8% ở n=2)


def main() -> int:
    cfg = Config.load(str(ROOT / "configs" / "pilot_dongda.yaml"))
    fp_sach = fingerprint_actors(run_once(cfg, SEEDS[0]))

    wait: Counter = Counter()
    arrive: Counter = Counter()
    goc = behavior_mod.consider_relocate

    def wrapper(actor, grid, hour, demand_hint, rng, cfg_behavior=None):
        cell = actor.cell
        out = goc(actor, grid, hour, demand_hint, rng, cfg_behavior)
        if out and out[0] == IdleAction.RELOCATE and out[1]:
            arrive[out[1]] += 1
        else:
            wait[cell] += 1
        return out

    behavior_mod.consider_relocate = wrapper
    try:
        fp_probe = fingerprint_actors(run_once(cfg, SEEDS[0]))
        if fp_sach != fp_probe:
            print("🔴 CỔNG NHIỄU-LOẠN ĐỎ ⇒ số đo không dùng được.")
            return 1
        print("✅ cổng nhiễu-loạn XANH (fingerprint có/không instrument IDENTICAL)\n")
        for s in SEEDS[1:]:
            run_once(cfg, s)
    finally:
        behavior_mod.consider_relocate = goc

    n = len(SEEDS)
    idle_min = {c: 2.0 * v / n for c, v in wait.items()}          # phút/ngày
    vao = {c: v / n for c, v in arrive.items()}                    # lượt/ngày
    tong_idle = sum(idle_min.values())
    print(f"MOCK · arm A · {n} seed · tổng phút idle (nhánh WAIT) {tong_idle:.0f}′/ngày "
          f"· {len(idle_min)} ô có idle\n")

    def giu(c):     # phút giữ mỗi lượt vào
        return idle_min.get(c, 0.0) / vao[c] if vao.get(c, 0) > 0 else float("inf")

    top_idle = sorted(idle_min.items(), key=lambda kv: -kv[1])[:8]
    print("=== TOP 8 ô hút phút idle ===")
    print(f"  {'ô':<18}{'idle ′/ngày':>13}{'% tổng':>9}{'lượt vào/ngày':>15}{'GIỮ ′/lượt':>13}")
    for c, v in top_idle:
        nhan = "  ← ô hút rc-03" if c in O_HUT else ("  ← F1 rộng nhất" if c in F1_RONG else "")
        print(f"  {c:<18}{v:13.0f}{v / tong_idle:9.1%}{vao.get(c, 0.0):15.1f}{giu(c):13.1f}{nhan}")

    share_hut = sum(idle_min.get(c, 0.0) for c in O_HUT) / tong_idle
    print(f"\n  ⇒ hai ô hút rc-03 giữ {share_hut:.1%} phút idle "
          f"(rc-03 báo 56,6% trên sổ idle_min — {'KHỚP BẬC' if share_hut > 0.30 else 'LỆCH, phải truy'})")

    print("\n=== GIẾNG SÂU hay LƯU VỰC RỘNG? ===")
    cac_giu = [giu(c) for c in idle_min if vao.get(c, 0) >= 1.0]
    med = statistics.median(cac_giu) if cac_giu else 0.0
    print(f"  thời gian giữ TRUNG VỊ của mọi ô (≥1 lượt vào/ngày): {med:.1f}′/lượt")
    for ten, nhom in (("ô hút rc-03", O_HUT), ("F1 lưu vực rộng nhất", F1_RONG)):
        for c in nhom:
            g, v = giu(c), vao.get(c, 0.0)
            boi = g / med if med else float("nan")
            print(f"  {ten:<22} {c[-7:]}: giữ {g:7.1f}′/lượt = {boi:5.1f}× trung vị · "
                  f"vào {v:5.1f} lượt/ngày · idle {idle_min.get(c, 0.0):6.0f}′")

    g_hut = statistics.mean([giu(c) for c in O_HUT])
    g_rong = statistics.mean([giu(c) for c in F1_RONG])
    print("\n=== PHÁN QUYẾT giả thuyết F5 ===")
    if g_hut > 1.8 * med and g_hut > g_rong:
        print(f"  ⇒ ĐỨNG: ô hút giữ {g_hut:.1f}′/lượt ({g_hut / med:.1f}× trung vị) vs cặp F1-rộng "
              f"{g_rong:.1f}′ ⇒ chúng là GIẾNG SÂU, không phải lưu vực rộng.")
        print("     Phút idle tích lũy = (lượt vào) × (thời gian giữ); F1 chỉ đo vế ĐẦU nên đoán sai ô.")
    else:
        print(f"  ⇒ 🔴 ĐỔ: ô hút giữ {g_hut:.1f}′/lượt vs trung vị {med:.1f}′ và cặp F1-rộng "
              f"{g_rong:.1f}′ ⇒ 'giếng sâu' KHÔNG giải thích được. Phải tìm chỗ khác.")

    OUT.write_text(json.dumps({
        "what": "F5 — lượt ghé vs thời gian giữ theo ô (ĐO, arm A)",
        "mock": True, "arm": "A", "seeds": SEEDS,
        "cong_nhieu_loan": "XANH",
        "tong_idle_phut_ngay": round(tong_idle, 1),
        "share_idle_hai_o_hut": round(share_hut, 4),
        "giu_trung_vi_phut_moi_luot": round(med, 2),
        "top8_o_hut_idle": [{"cell": c, "idle_phut_ngay": round(v, 1),
                             "luot_vao_ngay": round(vao.get(c, 0.0), 2),
                             "giu_phut_moi_luot": round(giu(c), 2)} for c, v in top_idle],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nartifact → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

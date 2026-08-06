"""F4 — ĐO THẬT phân bố `idle_streak_min` tại điểm quyết định đứng-chỗ (nâng số DERIVED của F3 lên ĐO).

    uv run python research/audit/2026-08-06-root-cause-idle/f4-streak-distribution.py

## Vì sao

`UPDATE-170`/`D-SIM-K8` nói bậc sốt-ruột **hầu như không bao giờ tới n=2** vì `idle_streak` reset mỗi lần
relocate (`world.py:1137`). Nhưng con số chống lưng (`~17,2′` mỗi lần relocate) là **DERIVED** từ hai số
tổng của rc-03, **không** phải đo phân bố. Script này đo trực tiếp.

## Cách đo — pass-through, KHÔNG đổi hành vi

Bọc **`gsm_sim.behavior.consider_relocate`** bằng một wrapper **chỉ ghi lại** `actor.idle_streak_min` rồi
gọi hàm gốc với **đúng** tham số ⇒ 0 draw thêm, 0 nhánh đổi. **Cổng nhiễu-loạn:** chạy cùng seed **có** và
**không** có instrument rồi so `fingerprint_actors` — phải **IDENTICAL**, nếu không thì phép đo tự làm
lệch thứ nó đo (đúng bẫy mà rc-03 đã phải canh).

⚠ **Bẫy tôi đã sập một lần:** patch `world.consider_relocate` cho **0 lượt gọi** mà cổng nhiễu-loạn vẫn
**XANH** — vì đường BẢN NĂNG gọi hàm đó ở `behavior.py:172` (tra tên trong module `behavior`), còn
`world.py:18` chỉ bind bản gốc cho đường ADVISOR (`world.py:1041`, kênh `rest_window` — TẮT mặc định).
Cổng xanh + 0 quan sát là **một cặp dấu hiệu phải nghi ngờ ngay**, không được đọc thành "nhánh không chạy".

Ngưỡng cần so (từ `configs/pilot_dongda.yaml` `behavior`): `idle_impatience_step_min` (bậc n=1) và
`2 × step` (bậc n=2 — bậc mà cơ chế *"đi xa hơn"* mới bật).

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

# ⚠ Phải patch namespace của `behavior`, KHÔNG phải của `world`: đường BẢN NĂNG đi
# `behavior.choose_idle_action` → gọi `consider_relocate` ở **behavior.py:172** (tra tên trong module
# behavior). `world.py:18` chỉ bind bản gốc cho đường ADVISOR (`world.py:1041`, kênh rest_window — TẮT
# mặc định). Patch sai chỗ ⇒ 0 lượt gọi mà cổng nhiễu-loạn vẫn XANH (tôi đã sập đúng bẫy này một lần).
from gsm_sim import behavior as behavior_mod                      # noqa: E402
from gsm_sim.config import Config                                 # noqa: E402
from gsm_sim.runner import run_once                               # noqa: E402
from gsm_sim.sim_metrics import fingerprint_actors                # noqa: E402

OUT = Path(__file__).resolve().parent / "f4-streak-distribution.json"
SEEDS = [1000, 1001, 1002, 1003, 1004]


def main() -> int:
    cfg = Config.load(str(ROOT / "configs" / "pilot_dongda.yaml"))
    beh = cfg.get("behavior", {}) or {}
    step = float(beh.get("idle_impatience_step_min", 30.0))
    max_steps = int(beh.get("idle_impatience_max_steps", 2))
    nguong = [step * k for k in range(1, max_steps + 1)]
    print(f"MOCK · arm A · {len(SEEDS)} seed · ngưỡng bậc sốt-ruột: "
          f"{', '.join(f'n={i + 1} tại {v:.0f}′' for i, v in enumerate(nguong))}\n")

    # ---- cổng nhiễu-loạn: fingerprint có/không instrument phải IDENTICAL ----
    fp_sach = fingerprint_actors(run_once(cfg, SEEDS[0]))

    streaks: list[float] = []
    goc = behavior_mod.consider_relocate

    def wrapper(actor, grid, hour, demand_hint, rng, cfg_behavior=None):
        streaks.append(float(actor.idle_streak_min))
        return goc(actor, grid, hour, demand_hint, rng, cfg_behavior)

    behavior_mod.consider_relocate = wrapper
    try:
        res0 = run_once(cfg, SEEDS[0])
        fp_probe = fingerprint_actors(res0)
        if fp_sach != fp_probe:
            print("🔴 CỔNG NHIỄU-LOẠN ĐỎ: instrument làm đổi hành vi ⇒ số đo KHÔNG dùng được.")
            return 1
        print("✅ cổng nhiễu-loạn XANH: fingerprint có/không instrument IDENTICAL\n")
        for s in SEEDS[1:]:
            run_once(cfg, s)
    finally:
        behavior_mod.consider_relocate = goc

    n = len(streaks)
    if not n:
        print("KHÔNG có lượt gọi nào — kênh/nhánh không chạy?")
        return 1
    xs = sorted(streaks)
    per_seed = n / len(SEEDS)
    print(f"=== PHÂN BỐ `idle_streak_min` tại điểm quyết định (n = {n} lượt, "
          f"{per_seed:.0f}/ngày) ===")
    for q in (50, 75, 90, 95, 99):
        print(f"  p{q}: {xs[min(n - 1, int(n * q / 100))]:6.1f}′")
        pass
    print(f"  trung bình {statistics.mean(xs):6.1f}′ · max {xs[-1]:.1f}′")

    print("\n=== BAO NHIÊU % LƯỢT ĐẠT TỚI TỪNG BẬC SỐT-RUỘT? ===")
    bac: Counter = Counter()
    for v in xs:
        k = 0
        for i, ng in enumerate(nguong, start=1):
            if v >= ng:
                k = i
        bac[k] += 1
    for k in range(0, max_steps + 1):
        c = bac.get(k, 0)
        ten = "n=0 (ring 1, ~0,37 km)" if k == 0 else f"n={k} (ring {1 + k})"
        canh = "  ← bậc mà cơ chế 'đi xa hơn' MỚI bật" if k == max_steps else ""
        print(f"  {ten:26s} {c:6d}/{n} = {c / n:6.2%}{canh}")

    dat_max = bac.get(max_steps, 0) / n
    print(f"\n=== PHÁN QUYẾT `D-SIM-K8` ===")
    if dat_max < 0.05:
        print(f"  ⇒ ĐỨNG: chỉ {dat_max:.2%} lượt tới bậc n={max_steps} ⇒ cơ chế 'rỗi lâu đi xa hơn'"
              f" gần như KHÔNG BAO GIỜ bật ⇒ sửa `B3` một mình là vô nghĩa.")
    else:
        print(f"  ⇒ 🔴 BÁC/LÀM YẾU: {dat_max:.2%} lượt tới bậc n={max_steps} — không hiếm như tôi nói."
              f" Phải sửa lại phát biểu của UPDATE-170.")

    OUT.write_text(json.dumps({
        "what": "F4 — phân bố idle_streak tại điểm quyết định đứng-chỗ (ĐO, không derived)",
        "mock": True, "arm": "A", "seeds": SEEDS,
        "cong_nhieu_loan": "XANH (fingerprint có/không instrument IDENTICAL)",
        "n_luot": n, "luot_moi_ngay": round(per_seed, 1),
        "nguong_bac": nguong,
        "phan_vi": {f"p{q}": xs[min(n - 1, int(n * q / 100))] for q in (50, 75, 90, 95, 99)},
        "trung_binh": round(statistics.mean(xs), 2), "max": xs[-1],
        "ty_le_theo_bac": {f"n={k}": round(bac.get(k, 0) / n, 5) for k in range(max_steps + 1)},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nartifact → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

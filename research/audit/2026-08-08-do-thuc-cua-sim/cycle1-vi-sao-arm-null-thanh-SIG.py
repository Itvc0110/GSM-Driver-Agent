"""Cycle 1 — vì sao arm NULL đi từ `ns` sang `SIG` sau khi sửa mẫu số?

# Dấu hiệu

`cycle1-do-lai-hieu-qua-advisor.py` cho: `N − A` (payout) đi từ **−769đ ns** (mẫu số cũ) sang
**−2.378đ SIG** (mẫu số mới), cùng 30 seed, cùng arm. Arm N **không có advisor** — nó chỉ rút lại
nhiễu niềm tin (`RNG +7919`). Một arm không can thiệp mà cho hiệu ứng SIG là **đúng loại dấu hiệu**
đã làm hỏng kết luận C9 (`UPDATE-182`), nên không được bỏ qua.

# Giả thuyết (ghi TRƯỚC khi đo)

Chỉ **payout** SIG; `trips`/`served`/`expired` vẫn `ns`. Payout dịch mà chuyến không dịch ⇒ nghi
vấn ở **cổng thưởng 0,85** (`policy.day_bonus` trả 0 khi acceptance dưới ngưỡng, bất kể điểm):
mẫu số sạch đẩy nhiều tài xế lên **sát cổng** hơn, nên payout trở nên **nhạy hơn** với nhiễu niềm
tin — cùng một cú nhiễu nay đủ để lật người qua/lại cổng.

**Phán quyết:**
- `N − A` của **thành phần thưởng** SIG trong khi **phần còn lại** ns ⇒ **cơ chế cổng được xác
  nhận**. Hệ quả: payout là đại lượng có **điểm gãy**, và mọi kết luận payout phải trích kèm điều
  đó — không phải lỗi của bản vá, mà là tính chất của chính chính sách thưởng.
- Cả hai thành phần đều dịch ⇒ **KHÔNG phải cổng**; phải điều tra tiếp trước khi tin `+3.106đ`.
- Đo lại mà `N − A` thành `ns` ⇒ SIG lần trước là **may rủi đa phép thử** (1 SIG trên 8 phép thử
  null có xác suất ~34%).

⚠ Đo trên **cùng 30 seed** với phép đo gốc để so được.

Chạy: uv run python research/audit/2026-08-08-do-thuc-cua-sim/cycle1-vi-sao-arm-null-thanh-SIG.py
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import statistics as st
import sys

import numpy as np
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gsm_sim import runner as RUNNER            # noqa: E402
from gsm_sim.config import Config               # noqa: E402
from gsm_sim.entities import Actor              # noqa: E402
from gsm_sim.parallel import _cfg_with          # noqa: E402
from gsm_sim.runner import run_once             # noqa: E402
from gsm_sim.world import World                 # noqa: E402

SEEDS = list(range(3300, 3330))
OUT = pathlib.Path(__file__).with_suffix(".json")
NB = 4000

MOI = Actor.acceptance_rate
CU = property(lambda s: s.orders_accepted / s.orders_offered if s.orders_offered else 1.0)


class NoisyWorld(World):
    def _actor_demand_hint(self, actor, hour):  # type: ignore[override]
        key = (actor.actor_id, hour, actor.cell)
        cached = self._belief_cache.get(key)
        if cached is not None:
            return cached
        field = self.demand_field.get(hour, {})
        if not field:
            self._belief_cache[key] = {}
            return {}
        hint: dict[str, float] = {}
        from gsm_sim.geo import grid_disk
        for c in sorted(grid_disk(actor.cell, 2)):
            rng_c = np.random.default_rng(
                (self.seed + 7919, actor.actor_id, hour, int(c, 16)))
            hint[c] = field.get(c, 0.0) * math.exp(rng_c.normal(0.0, actor.demand_prior_sigma))
        self._belief_cache[key] = hint
        return hint


def _tach(r) -> dict:
    """TÁCH payout thành thưởng-ngày và phần còn lại — đó là phép đo quyết định."""
    b = [float(r.policy.day_bonus(a.points, a.acceptance_rate, a.completion_rate))
         for a in r.actors]
    p = [float(a.payout_vnd) for a in r.actors]
    n_qua = sum(1 for x in b if x > 0)
    return {"thuong": st.mean(b), "con_lai": st.mean(p) - st.mean(b), "tong": st.mean(p),
            "so_nguoi_qua_cong": float(n_qua)}


def _boot(xs, rng):
    m = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(NB))
    return (m[int(0.025 * NB)], m[int(0.975 * NB)])


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    rng = random.Random(20260809)
    ket: dict = {"seeds": SEEDS, "bo": {}}

    for ten, prop in (("CŨ", CU), ("MỚI", MOI)):
        Actor.acceptance_rate = prop          # type: ignore[assignment]
        rows = []
        for k, seed in enumerate(SEEDS, 1):
            A = _tach(run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed))
            RUNNER.World = NoisyWorld
            try:
                N = _tach(run_once(_cfg_with(cfg, enabled=False, actor_id=None,
                                             channels=None), seed))
            finally:
                RUNNER.World = World
            rows.append({"A": A, "N": N})
            if k % 15 == 0:
                print(f"  bộ {ten}: {k}/{len(SEEDS)} seed", flush=True)
        blk = {}
        for w in ("thuong", "con_lai", "tong", "so_nguoi_qua_cong"):
            d = [r["N"][w] - r["A"][w] for r in rows]
            lo, hi = _boot(d, rng)
            blk[w] = {"A": st.mean([r["A"][w] for r in rows]), "N_tru_A": st.mean(d),
                      "ci": [lo, hi], "sig": "SIG" if (lo > 0 or hi < 0) else "ns"}
        ket["bo"][ten] = blk
    Actor.acceptance_rate = MOI               # type: ignore[assignment]

    print(f"\n{'thành phần':<20}{'nền A':>14}{'N − A':>14}{'CI95':>26}{'':>6}")
    print("-" * 82)
    for ten in ("CŨ", "MỚI"):
        print(f"— mẫu số {ten}")
        for w in ("thuong", "con_lai", "tong", "so_nguoi_qua_cong"):
            d = ket["bo"][ten][w]
            print(f"  {w:<18}{d['A']:>14,.1f}{d['N_tru_A']:>+14,.1f}"
                  f"   [{d['ci'][0]:>+10,.1f};{d['ci'][1]:>+10,.1f}] {d['sig']}")

    print("\n=== PHÁN QUYẾT (tiêu chí ghi TRƯỚC khi thấy số) ===")
    m = ket["bo"]["MỚI"]
    if m["thuong"]["sig"] == "SIG" and m["con_lai"]["sig"] == "ns":
        print("  → CƠ CHẾ CỔNG ĐƯỢC XÁC NHẬN: nhiễu thuần dịch THƯỞNG (SIG) mà không dịch phần")
        print("    còn lại (ns) ⇒ payout có ĐIỂM GÃY ở ngưỡng 0,85. Không phải lỗi bản vá —")
        print("    là tính chất của chính chính sách thưởng, và nay lộ ra vì mẫu số sạch đẩy")
        print("    nhiều tài xế tới sát cổng hơn.")
        print("    ⇒ Mọi kết luận PAYOUT phải trích kèm điều này; kết luận trips/served/expired")
        print("      KHÔNG bị ảnh hưởng (null của chúng vẫn ns).")
    elif m["tong"]["sig"] == "ns":
        print("  → Đo lại ra `ns` ⇒ lần SIG trước là MAY RỦI ĐA PHÉP THỬ. Không có cơ chế nào.")
    else:
        print("  ⚠ CẢ HAI thành phần dịch ⇒ KHÔNG phải cổng. Chưa giải thích được;")
        print("    `+3.106đ` phải treo caveat cho tới khi điều tra xong.")

    OUT.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()

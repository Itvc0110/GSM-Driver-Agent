"""Cycle 1 — ĐO LẠI hiệu quả advisor sau khi sửa mẫu số tỷ lệ nhận.

# Vì sao bắt buộc đo lại

`+3.219đ` (và `+3.097đ` đo lại hôm qua) tính trên một thế giới nơi **3,67% driver-day bị tước
thưởng oan** vì mẫu số tỷ lệ nhận đếm cả lượt bị chặn vì pin. Sửa mẫu số **đổi payout nền**
(+1.367đ/người tiền thưởng được trả lại) ⇒ số cũ **không còn so được**.

⚠ Không được giả định hiệu ứng advisor giữ nguyên. Sửa này đổi **ai qua được cổng thưởng 0,85**,
mà cổng thưởng chính là một trong ba kênh giá trị — nên hiệu ứng advisor **có thể** đổi theo cả
hai chiều: nhỏ đi (vì tài xế đã được trả lại tiền, advisor còn ít chỗ để cải thiện) hoặc lớn hơn
(vì nay nhiều người ở gần ngưỡng hơn nên lời khuyên chạm được nhiều người hơn).

# Ba arm, giữ đúng khuôn đã dùng

| arm | là gì |
| --- | --- |
| **A** | `advice.enabled = False` — không advisor |
| **B** | `enabled = True`, `coverage: all` |
| **N** | **NULL** — advisor TẮT như A, chỉ rút lại nhiễu niềm tin (`RNG +7919`) |

Arm N là cột hiệu chuẩn bắt buộc (bài học `UPDATE-182`): sàn nhiễu theo NGƯỜI là **17,2×** hiệu
ứng, nên `B − A` một mình đọc quá tay được. Cổng tự báo `PLACEBO VÔ HIỆU` nếu N trùng khít A.

**Báo CẢ HAI bộ số** — mẫu số CŨ và MỚI trên **cùng seed** — bằng cách vá ngược property trong
tiến trình (đảo được hoàn toàn, không đụng git).

Chạy: uv run python research/audit/2026-08-08-do-thuc-cua-sim/cycle1-do-lai-hieu-qua-advisor.py
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
from gsm_sim.parallel import _cfg_with, _system_metrics   # noqa: E402
from gsm_sim.runner import run_once             # noqa: E402
from gsm_sim.world import World                 # noqa: E402

SEEDS = list(range(3300, 3330))     # 30 seed, ĐÚNG cửa sổ của `+3.219đ`
OUT = pathlib.Path(__file__).with_suffix(".json")
NB = 4000

MAU_SO_MOI = Actor.acceptance_rate
MAU_SO_CU = property(
    lambda s: s.orders_accepted / s.orders_offered if s.orders_offered else 1.0)


class NoisyWorld(World):
    """Arm NULL — chép nguyên `_actor_demand_hint`, chỉ đổi khoá RNG `+7919`."""

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


def _do(r) -> dict:
    sm = _system_metrics(r, -1)
    return {"payout": float(sm["payout_mean_all"]), "trips": float(sm["trips_mean_all"]),
            "served": float(sm["served_rate"]), "expired": float(sm["expired_n"]),
            "_fp": round(sum(float(a.payout_vnd) for a in r.actors), 4)}


def _boot(xs, rng):
    m = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(NB))
    return (m[int(0.025 * NB)], m[int(0.975 * NB)])


def _chay(cfg) -> list[dict]:
    rows = []
    for k, seed in enumerate(SEEDS, 1):
        A = _do(run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed))
        B = _do(run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                   coverage="all"), seed))
        RUNNER.World = NoisyWorld
        try:
            N = _do(run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed))
        finally:
            RUNNER.World = World
        rows.append({"A": A, "B": B, "N": N})
        if k % 10 == 0:
            print(f"    ... {k}/{len(SEEDS)} seed", flush=True)
    return rows


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    rng = random.Random(20260809)
    ket: dict = {"seeds": SEEDS, "bo": {}}

    for ten, prop in (("CŨ (mẫu số nhiễm)", MAU_SO_CU), ("MỚI (mẫu số sạch)", MAU_SO_MOI)):
        print(f"  đang chạy bộ {ten} …", flush=True)
        Actor.acceptance_rate = prop          # type: ignore[assignment]
        rows = _chay(cfg)
        trung = sum(1 for r in rows if r["N"]["_fp"] == r["A"]["_fp"])
        blk = {"placebo_trung_khit": f"{trung}/{len(rows)}",
               "PLACEBO_VO_HIEU": trung == len(rows)}
        for w in ("payout", "trips", "served", "expired"):
            a = st.mean([r["A"][w] for r in rows])
            db = [r["B"][w] - r["A"][w] for r in rows]
            dn = [r["N"][w] - r["A"][w] for r in rows]
            lb, hb = _boot(db, rng)
            ln, hn = _boot(dn, rng)
            blk[w] = {"A": a, "B_tru_A": st.mean(db), "ci_B": [lb, hb],
                      "sig_B": "SIG" if (lb > 0 or hb < 0) else "ns",
                      "N_tru_A": st.mean(dn), "ci_N": [ln, hn],
                      "sig_N": "SIG" if (ln > 0 or hn < 0) else "ns"}
        ket["bo"][ten] = blk
    Actor.acceptance_rate = MAU_SO_MOI         # type: ignore[assignment]

    print(f"\n{'chỉ số':<12}{'nền A':>26}{'B − A (advisor)':>34}{'N − A':>16}")
    print("-" * 90)
    for ten in ket["bo"]:
        print(f"— bộ {ten}")
        for w in ("payout", "trips", "served", "expired"):
            d = ket["bo"][ten][w]
            print(f"  {w:<10}{d['A']:>24,.3f}{d['B_tru_A']:>+18,.3f} "
                  f"[{d['ci_B'][0]:>+9,.2f};{d['ci_B'][1]:>+9,.2f}] {d['sig_B']:<4}"
                  f"{d['N_tru_A']:>+12,.3f} {d['sig_N']}")

    cu = ket["bo"]["CŨ (mẫu số nhiễm)"]["payout"]
    moi = ket["bo"]["MỚI (mẫu số sạch)"]["payout"]
    print("\n=== ĐỌC CHO ĐÚNG ===")
    print(f"  · Hiệu quả advisor (payout): **{cu['B_tru_A']:+,.0f}đ** (mẫu số cũ) → "
          f"**{moi['B_tru_A']:+,.0f}đ** (mẫu số mới)")
    print(f"  · Nền A dịch {moi['A'] - cu['A']:+,.0f}đ — đó là **tiền thưởng trả lại**, "
          f"KHÔNG phải advisor tạo ra.")
    for ten in ket["bo"]:
        if ket["bo"][ten]["PLACEBO_VO_HIEU"]:
            print(f"  ⛔ bộ {ten}: PLACEBO VÔ HIỆU — arm N trùng khít arm A, không đọc thành PASS")
    if not any(ket["bo"][t]["PLACEBO_VO_HIEU"] for t in ket["bo"]):
        print("  ✅ Arm NULL có phương sai thật ở CẢ HAI bộ ⇒ cột `N − A` hiệu chuẩn được.")

    OUT.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()

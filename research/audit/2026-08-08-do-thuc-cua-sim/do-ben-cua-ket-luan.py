"""ĐỘ BỀN CỦA KẾT LUẬN ADVISOR trước bất định về ĐỘ CHẶT THỊ TRƯỜNG.

# Câu hỏi

`+3.219đ SIG` được đo tại **đúng một điểm** của thế giới: `actors.n = 90`. Mà 90 **không phải
số đo được** — nó bị **vặn tay từ 74 lên 90** để kéo `served_rate` lên 0,797
(`tracking/` Cycle B0 context). Tức thế giới ta đang đo là thế giới **cố ý dư cung**.

Dư cung đúng là điều kiện mà kênh **vị trí** ít giá trị nhất: đơn nào cũng có người phục vụ, nên
dời người quanh bản đồ ít đổi kết cục. Ngược lại, thị trường **chặt** thì vị trí quyết định.

⇒ Nếu `B − A` đổi mạnh theo `n`, thì **`+3.219đ` là số của MỘT thế giới**, không phải hằng số của
advisor — và phải luôn trích kèm điều kiện. Nếu nó bền, kết luận mạnh hơn hẳn.

Đây là việc thay thế cho *"đối chiếu độ thực"* — vì `sim-vs-du-lieu-that.py` đã chứng minh trong
repo **không tồn tại neo dữ liệu thật nào** (bảng "thật" của xe máy do chính `gsm_sim` sinh ra).
Không đo được *"sim có giống thực tế không"*, nhưng đo được *"kết luận có sống sót khi thế giới
khác đi không"* — và đó mới là thứ quyết định có nên tin `+3.219đ` hay không.

# Thiết kế

| arm | nghĩa |
| --- | --- |
| **A** | `advice.enabled = False` — không advisor |
| **B** | `enabled = True`, `coverage = all` — advisor thật |
| **N** | **NULL**: advisor TẮT như A, chỉ **rút lại nhiễu niềm tin** (`RNG +7919`) |

Arm **N** ở **mọi mức đội**, không chỉ mức 90 — vì sàn nhiễu có thể tự nó đổi theo `n`, và nếu
chỉ hiệu chuẩn tại 90 thì mọi điểm khác lại thành số thô không có đối chứng. Đây chính là nội
dung cổng `null_arm_delta` (Cycle P2), áp ngay tại chỗ thay vì hứa làm sau.

**Fallback bắt buộc — bẫy tôi đã sập (`UPDATE-182`):** nếu arm N **bit-identical** với arm A thì
nó là **placebo phương-sai-0**, không chứng minh được gì. Script **tự kiểm** và in
`PLACEBO VÔ HIỆU` cho mức đội đó, tuyệt đối không đọc thành "đã hiệu chuẩn".

Ghép cặp CRN: cùng `seed` ⇒ cùng đơn, cùng actor, cùng thời tiết. CI95 bootstrap trên **hiệu
theo từng seed**, không trên giá trị thô.

Chạy: uv run python research/audit/2026-08-08-do-thuc-cua-sim/do-ben-cua-ket-luan.py
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

from gsm_sim import runner as RUNNER          # noqa: E402
from gsm_sim.config import Config             # noqa: E402
from gsm_sim.parallel import _cfg_with, _system_metrics   # noqa: E402
from gsm_sim.runner import run_once           # noqa: E402
from gsm_sim.world import World               # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
DOI = [60, 75, 90, 105, 120]        # 90 = điểm hiện hành (vặn tay)
SEEDS = list(range(3300, 3320))     # 20 seed, cùng họ với pb1b
NB = 4000


class NoisyWorld(World):
    """Sao `_actor_demand_hint` của world, CHỈ đổi khoá RNG `+7919` ⇒ rút LẠI nhiễu niềm tin.

    Chép nguyên từ `pb1b-co-che-va-lat-cat-co-dinh.py` (đã dùng và đã kiểm ở đó), để arm NULL
    ở đây **cùng một định nghĩa** với arm NULL đã hiệu chuẩn `+3.219đ`.
    """

    def _actor_demand_hint(self, actor, hour):  # type: ignore[override]
        key = (actor.actor_id, hour, actor.cell)
        cached = self._belief_cache.get(key)
        if cached is not None:
            return cached
        field = self.demand_field.get(hour, {})
        if not field:
            self._belief_cache[key] = {}
            return {}
        sigma = actor.demand_prior_sigma
        hint: dict[str, float] = {}
        from gsm_sim.geo import grid_disk
        for c in sorted(grid_disk(actor.cell, 2)):
            rng_c = np.random.default_rng((self.seed + 7919, actor.actor_id, hour, int(c, 16)))
            hint[c] = field.get(c, 0.0) * math.exp(rng_c.normal(0.0, sigma))
        self._belief_cache[key] = hint
        return hint


def _do(r) -> dict:
    """Chỉ số hệ thống + trung bình theo tài xế.

    ⚠ Bản nháp đọc `r.orders_served` / `r.match_waits` — **không thuộc tính nào tồn tại**
    (`dir(result)` đã kiểm). `getattr(..., None)` sẽ nuốt im lặng ⇒ `served_rate` tụt về đường
    suy diễn và `wait_median` thành `nan` mà không ai biết. Nay dùng `_system_metrics`, đúng
    nguồn mà chính đường A/B dùng, nên số **so được** với các artifact cũ.
    """
    sm = _system_metrics(r, -1)          # -1 = không loại actor nào ⇒ toàn đội
    idle = [float(a.idle_min) for a in r.actors]
    pay = [float(a.payout_vnd) for a in r.actors]
    return {
        "payout_mean": float(sm["payout_mean_all"]),
        "trips_mean": float(sm["trips_mean_all"]),
        "idle_mean": st.mean(idle) if idle else 0.0,
        "served_rate": float(sm["served_rate"]),
        "expired_n": float(sm["expired_n"]),
        "wait_median": float(sm["wait_median_min"]),
        "_fp": round(sum(pay), 4),                           # vân tay bắt placebo 0-phương-sai
    }


def _boot(xs, rng):
    xs = [x for x in xs if not math.isnan(x)]
    if len(xs) < 2:
        return (float("nan"), float("nan"))
    m = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(NB))
    return (m[int(0.025 * NB)], m[int(0.975 * NB)])


def main() -> None:
    base = yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8"))
    rng = random.Random(20260808)
    ket: dict = {"doi": DOI, "seeds": SEEDS, "muc": {}}

    for n in DOI:
        blob = json.loads(json.dumps(base))
        blob["actors"]["n"] = n
        cfg = Config(blob, ROOT)
        rows = []
        for k, seed in enumerate(SEEDS, 1):
            A = _do(run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed))
            B = _do(run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                       coverage="all"), seed))
            RUNNER.World = NoisyWorld
            try:
                N = _do(run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None),
                                 seed))
            finally:
                RUNNER.World = World
            rows.append({"A": A, "B": B, "N": N})
            print(f"  đội {n}: {k}/{len(SEEDS)} seed", flush=True)

        # ⚠ CỔNG PLACEBO — arm N trùng khít arm A ⇒ không hiệu chuẩn được gì
        trung = sum(1 for r in rows if r["N"]["_fp"] == r["A"]["_fp"])
        placebo_vo_hieu = trung == len(rows)

        muc = {"n": n, "placebo_trung_khit": f"{trung}/{len(rows)}",
               "PLACEBO_VO_HIEU": placebo_vo_hieu}
        for w in ("payout_mean", "trips_mean", "idle_mean", "served_rate", "expired_n",
                  "wait_median"):
            a = st.mean([r["A"][w] for r in rows])
            db = [r["B"][w] - r["A"][w] for r in rows]
            dn = [r["N"][w] - r["A"][w] for r in rows]
            lb, hb = _boot(db, rng)
            ln, hn = _boot(dn, rng)
            muc[w] = {"A": a,
                      "B_tru_A": st.mean(db), "ci_B": [lb, hb],
                      "sig_B": "SIG" if (lb > 0 or hb < 0) else "ns",
                      "N_tru_A": st.mean(dn), "ci_N": [ln, hn],
                      "sig_N": "SIG" if (ln > 0 or hn < 0) else "ns"}
        ket["muc"][str(n)] = muc
        print(f"  → đội {n}: served {muc['served_rate']['A']:.3f} · "
              f"Δpayout {muc['payout_mean']['B_tru_A']:+,.0f}đ {muc['payout_mean']['sig_B']}"
              + ("  ⛔ PLACEBO VÔ HIỆU" if placebo_vo_hieu else ""), flush=True)

    # ---------------- BẢNG ----------------
    print("\n" + "=" * 96)
    print("HIỆU QUẢ ADVISOR THEO ĐỘ CHẶT THỊ TRƯỜNG  (20 seed ghép cặp CRN · MOCK pilot_dongda)")
    print("=" * 96)
    print(f"{'đội':>5}{'served_rate A':>15}{'chờ ghép A':>13}{'Δpayout (B−A)':>26}"
          f"{'Δ nhiễu thuần (N−A)':>24}")
    print("-" * 96)
    for n in DOI:
        m = ket["muc"][str(n)]
        p, q = m["payout_mean"], m["wait_median"]
        danh = " ← hiện hành" if n == 90 else ""
        print(f"{n:>5}{m['served_rate']['A']:>15.3f}{q['A']:>12.1f}′"
              f"{p['B_tru_A']:>+15,.0f}đ [{p['ci_B'][0]:>+6,.0f};{p['ci_B'][1]:>+6,.0f}] "
              f"{p['sig_B']}"
              f"{p['N_tru_A']:>+13,.0f}đ {p['sig_N']}{danh}")

    print(f"\n{'đội':>5}{'Δ đơn hết hạn':>18}{'Δ chuyến':>14}{'Δ phút rảnh':>16}")
    print("-" * 96)
    for n in DOI:
        m = ket["muc"][str(n)]
        print(f"{n:>5}{m['expired_n']['B_tru_A']:>+14,.1f} {m['expired_n']['sig_B']:<4}"
              f"{m['trips_mean']['B_tru_A']:>+10,.3f} {m['trips_mean']['sig_B']:<4}"
              f"{m['idle_mean']['B_tru_A']:>+12,.1f}′ {m['idle_mean']['sig_B']}")

    vo = [n for n in DOI if ket["muc"][str(n)]["PLACEBO_VO_HIEU"]]
    if vo:
        print(f"\n⛔ PLACEBO VÔ HIỆU ở đội {vo} — arm N trùng khít arm A ⇒ các mức đó KHÔNG được")
        print("   đọc là 'đã hiệu chuẩn'. Đây là bẫy đã làm hỏng kết luận C9 (`UPDATE-182`).")
    else:
        print("\n✅ Arm NULL có phương sai thật ở MỌI mức đội ⇒ cột `N − A` hiệu chuẩn được.")

    OUT.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()

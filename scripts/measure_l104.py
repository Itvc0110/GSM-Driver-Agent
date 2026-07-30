"""Đo `L1-04` — dời `_claim_effect` sau clamp khả thi: Δ per-seed TRƯỚC/SAU fix.

`L1-04` là thay đổi ĐỔI HÀNH VI THẬT (đo được: 28% quyết định `shift_extend` tiêu token
`_claim_effect` rồi bị clamp bất khả thi ⇒ mất hẳn, không đường quay lại). Theo acceptance
đã duyệt (`tracking/PLAN-2026-07-30-hang-doi-cong-viec.md` §1): Δ`net_mean_all` ở n≥100
ghép cặp CRN + guardrail 4 tầng ĐA-08 + `others_payout_vnd` + verdict adherence OK.

Cách đo: chạy CÙNG 100 seed trên code TRƯỚC fix (nhãn `truoc`) và SAU fix (nhãn `sau`),
lưu per-seed ⇒ diff ghép cặp có CI hợp lệ. World A (advice off) KHÔNG phụ thuộc fix nên
chỉ cần arm B; nhưng vẫn ghi net để đối chiếu.

    uv run python scripts/measure_l104.py truoc   # TRƯỚC khi sửa advice_bridge
    uv run python scripts/measure_l104.py sau     # SAU khi sửa
    uv run python scripts/measure_l104.py diff    # đọc 2 file, bootstrap CI

Arm: ladder `all` + coverage all (shift_extend phải BẬT thì fix mới có đường chạy;
config sản phẩm đang tắt kênh này — Δ đo ở đây là Δ CỦA THẾ GIỚI ĐO, không phải sản phẩm).
Seeds 4300–4399 (tươi — 4200–4299 đã dùng cho artifact 38).
Mọi số là MOCK (`configs/pilot_dongda.yaml`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with, run_once
from gsm_sim.runner import Config
from gsm_sim.sim_metrics import adherence_audit, system_guardrail

OUT = Path("research/audit/2026-07-27-current-state")
SEEDS = list(range(4300, 4400))
GUARD_KEYS = ("served_rate", "orders_completed", "total_payout_vnd", "expired_n",
              "wait_median_min", "gini_payout", "station_hhi", "supply_cell_hhi")


def run(tag: str) -> None:
    base = Config.load("configs/pilot_dongda.yaml")
    cfg = _cfg_with(base, enabled=True, actor_id=None,
                    channels=CHANNEL_LADDER["all"], coverage="all")
    rows = []
    for i, s in enumerate(SEEDS):
        r = run_once(cfg, s)
        pay = [a.payout_vnd for a in r.actors]
        g = system_guardrail(r)
        adh = adherence_audit(r)
        ext = adh["by_channel"].get("shift_extend", {})
        rows.append({
            "seed": s,
            "net_mean_all": round(float(np.mean(pay)), 2),
            **{k: g[k] for k in GUARD_KEYS if k in g},
            "ext_decided": ext.get("decided", 0),
            "ext_followed": ext.get("followed", 0),
            "adherence_flags": adh["flags"],
        })
        if (i + 1) % 10 == 0:
            print(f"  {tag}: {i + 1}/{len(SEEDS)}", flush=True)
    out = OUT / f"40-l104-{tag}-n100.json"
    out.write_text(json.dumps({"tag": tag, "arm": "ladder=all coverage=all",
                               "seeds": SEEDS, "rows": rows},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    n_flag = sum(1 for r in rows if r["adherence_flags"])
    print(f"{tag}: {len(rows)} seed -> {out}  (seed có adherence flag: {n_flag})")


def diff() -> None:
    a = json.loads((OUT / "40-l104-truoc-n100.json").read_text(encoding="utf-8"))
    b = json.loads((OUT / "40-l104-sau-n100.json").read_text(encoding="utf-8"))
    ra = {r["seed"]: r for r in a["rows"]}
    rb = {r["seed"]: r for r in b["rows"]}
    assert set(ra) == set(rb), "hai bên khác bộ seed — diff vô nghĩa"

    fa = sum(1 for r in ra.values() if r["adherence_flags"])
    fb = sum(1 for r in rb.values() if r["adherence_flags"])
    print(f"VERDICT adherence: trước {fa}/100 seed có flag · sau {fb}/100"
          f"  ->  {'OK cả hai' if fa == fb == 0 else '🔴 TREO — đọc flags trước khi tin Δ'}")

    rng = np.random.default_rng(12345)
    print(f"\n{'metric':22s}{'mean Δ (sau−trước)':>20s}{'CI95':>28s}{'SIG':>5s}")
    for k in ("net_mean_all", *GUARD_KEYS, "ext_decided", "ext_followed"):
        d = np.array([rb[s][k] - ra[s][k] for s in sorted(ra)], dtype=float)
        boots = [float(np.mean(rng.choice(d, size=len(d), replace=True)))
                 for _ in range(5000)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        sig = "SIG" if (lo > 0 or hi < 0) else "ns"
        print(f"{k:22s}{np.mean(d):>+20,.2f}{f'[{lo:,.2f}, {hi:,.2f}]':>28s}{sig:>5s}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "?"
    {"truoc": lambda: run("truoc"), "sau": lambda: run("sau"), "diff": diff}[mode]()

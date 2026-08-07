"""pb4 — ĐO lại mọi con số trong `pb4-thieu-tinh-nang.json`. Không trích nhãn, không suy.

Chạy:  uv run python research/audit/2026-08-07-phan-bien-sim-advisor/pb4-thieu-tinh-nang.py

MẪU SỐ (kỷ luật 6 — M1/M5): mẫu số của MỌI phép chia dưới đây là **110 tài xế bike
`d-*`/`r-*`**, KHÔNG phải 150. `ui/backend/app/adapters/advisor.py` chặn ngay ở cửa
(`if not driver_id.startswith(("d-", "r-"))` → `no_active_channel`) nên 40 tài xế
car/car-premium (`ce-*`, `cp-*`) **cố ý ngoài phạm vi** — gộp vào là lặp đúng lỗi M5.
"""
from __future__ import annotations

import collections
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ui" / "backend"))

from app.adapters import advisor, mockdata                      # noqa: E402
from app.services.advice_checkpoint import (                    # noqa: E402
    ProductSolverOrchestrator, _default_l1r)
from gsm_core.features import from_l1r as F                     # noqa: E402
from gsm_core.solvers import (anomaly_alert, f3_patterns,       # noqa: E402
                              mission_knapsack, penalty_explain)

OUT: dict = {}
cat = mockdata.catalog()
INSCOPE = [d["driver_id"] for d in cat["drivers"]
           if d["driver_id"].startswith(("d-", "r-"))]
DATES = cat["dates"][::9]          # 10 ngày trải đều trên 90 ngày mock
OUT["denominator"] = {"drivers_total": len(cat["drivers"]),
                      "drivers_in_scope_bike": len(INSCOPE),
                      "dates_sampled": DATES}


# ---------- 1. Đường sản phẩm v1 nói được GÌ (GET /api/v1/advice) ----------
def do_kenh_v1() -> dict:
    kinds = collections.Counter()
    outcome = collections.Counter()
    for dt in DATES:
        for did in INSCOPE:
            for _surface, mn in (("brief", 540), ("nudge", 840), ("recap", 1290)):
                r = advisor.advice(did, dt, mn)
                if r["silent"]["is_silent"]:
                    outcome["silent"] += 1
                    continue
                outcome["spoke"] += 1
                for it in r["items"]:
                    kinds[f"{it['solver']}|{it['kind']}|{it.get('reason_code')}"] += 1
    return {"n_calls": sum(outcome.values()), "outcome": dict(outcome),
            "item_shapes": dict(kinds)}


# ---------- 2. Bốn solver 0-call-site chạy trên ĐÚNG shape dữ liệu sản phẩm ----------
def do_solver_chet() -> dict:
    l1r, pol = _default_l1r(), advisor.policy()
    c, err = collections.Counter(), collections.Counter()
    pat = collections.Counter()
    for dt in DATES:
        t_aware = dt + "T14:00:00+07:00"      # shape mà `_iso_for_minute` sản xuất
        for did in INSCOPE:
            c["N"] += 1
            ss = F.derive_session_summary_input_l1r(did, dt, l1r, pol)
            if not ss["inferred_activities"]:
                c["S3_inferred_activities_rong"] += 1
            pb = ss["payout_breakdown"]
            if pb.get("gross_vnd"):
                c["S3_co_gross_va_payout"] += 1
            if pb.get("estimated_net_vnd") is not None:
                c["S3_co_estimated_net"] += 1
            s3 = f3_patterns.solve(ss, pol)["solution"]
            if s3.get("patterns"):
                c["S3_co_pattern"] += 1
            for p in s3.get("patterns") or []:
                pat[p.get("type")] += 1

            s8 = penalty_explain.solve(
                F.derive_penalty_explain_input_l1r(did, t_aware, l1r, pol))["solution"]
            if s8.get("notable"):
                c["S8_notable"] += 1
            if s8.get("total_deducted_vnd"):
                c["S8_co_tien_bi_tru"] += 1

            try:
                s9 = anomaly_alert.solve(
                    F.derive_anomaly_alert_input_l1r(did, t_aware, l1r))["solution"]
                c["S9_ok"] += 1
                if s9.get("flags"):
                    c["S9_co_co"] += 1
            except Exception as exc:
                c["S9_crash"] += 1
                err["S9:" + type(exc).__name__] += 1

            try:
                mission_knapsack.solve(F.derive_mission_select_input_l1r(
                    did, t_aware, l1r, hours_budget_remaining=6.0))
                c["S6_ok"] += 1
            except Exception as exc:
                c["S6_crash"] += 1
                err["S6:" + type(exc).__name__] += 1
    return {"counts": dict(c), "S3_pattern_types": dict(pat), "errors": dict(err)}


# ---------- 3. S6: dict trong bộ nhớ vs str sau parquet ----------
def do_rewards_shape() -> dict:
    import polars as pl
    from gsm_core.mockgen.realdata import generate_realdata
    with tempfile.TemporaryDirectory() as td:
        tabs = generate_realdata(days=8, seed_base=501, out_dir=Path(td))["tables"]
        mem = collections.Counter(type(m.get("rewards")).__name__
                                  for m in tabs["public_mission"])
        pq = pl.read_parquet(Path(td) / "public_mission.parquet").to_dicts()
        disk = collections.Counter(type(m.get("rewards")).__name__ for m in pq)
    prod = collections.Counter(type(m.get("rewards")).__name__
                               for m in _default_l1r()["public_mission"])
    return {"in_memory": dict(mem), "parquet": dict(disk), "loader_san_pham": dict(prod)}


# ---------- 4. Kênh v2 / S2 ----------
def do_kenh_v2() -> dict:
    import os
    o = ProductSolverOrchestrator()
    r = o.solve(INSCOPE[0], DATES[1] + "T14:00:00+07:00", 360, 1320)
    return {"provider_mac_dinh": type(o.runtime_state_provider).__name__,
            "ADVICE_V2_ENABLED": os.getenv("ADVICE_V2_ENABLED", "0"),
            "solver_set": r.solver_set, "reasons": r.reasons}


# ---------- 5. Policy bundle mà sản phẩm thực sự dùng ----------
def do_policy() -> dict:
    p = advisor.policy()
    return {"version": p.version, "weekly_quota": p.weekly_quota, "costs": p.costs,
            "track": p.track, "effective_from": p.effective_from,
            "effective_to": p.effective_to,
            "policy_thresholds_source": advisor._policy_thresholds()["source"],
            "advice_json_item_fields": list(json.loads(
                (ROOT / "ui" / "contracts" / "advice.json").read_text(encoding="utf-8")
            )["properties"]["items"]["items"]["properties"].keys())}


for name, fn in (("kenh_v1", do_kenh_v1), ("solver_chet", do_solver_chet),
                 ("rewards_shape", do_rewards_shape), ("kenh_v2", do_kenh_v2),
                 ("policy", do_policy)):
    OUT[name] = fn()

print(json.dumps(OUT, ensure_ascii=False, indent=2))

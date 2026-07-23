"""C2b — Solver S1 BonusFeasibility (TDD failing-first).

Test 3 unit: policy loader từ L0 record, derive L3 bonus_gap_input, solver + SolverReport.
Ràng buộc: mọi số có source (traceability=1.0); đa ràng buộc; deterministic.
"""

import math
from pathlib import Path

import pytest

from gsm_core.policy import PolicyBundle
from gsm_core.features.bonus_gap import derive_bonus_gap_input
from gsm_core.solvers.bonus_feasibility import solve
from gsm_core.schema_registry import SchemaRegistry

ROOT = Path(__file__).resolve().parent.parent

# L0 policy_bundle record mẫu (khớp schema, số như sim-policy-v0)
POLICY_REC = {
    "schema_version": "1.0.0", "bundle_id": "b1", "version": "sim-policy-v0",
    "effective_from": "2026-07-01T00:00:00+07:00", "track": "platform", "service": "bike",
    "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300},
    "driver_share": 0.75,
    "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
               "window_hours": list(range(6, 22))},
    "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
    "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85,
                    "forced_accept_below": 0.5},
    "source_url": None, "source": "MOCK",
}


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(POLICY_REC)


# ---------- Unit 1: policy loader ----------

def test_policy_from_record(policy):
    assert policy.trip_points(7) == 10   # peak
    assert policy.trip_points(10) == 5   # normal in window
    assert policy.trip_points(3) == 0    # ngoài window
    assert policy.version == "sim-policy-v0"
    # next_tier_gap: 120 điểm → mốc kế 160, thiếu 40, thưởng 115k
    assert policy.next_tier_gap(120) == (40, 115000)
    assert policy.next_tier_gap(200) is None  # đã max
    assert policy.bonus_at(160) == 115000
    assert policy.bonus_at(50) == 0


# ---------- Unit 2: derive L3 ----------

def _mk_l1(driver="d-1", date="2026-07-01"):
    """L1 tối thiểu: 1 driver, vài trip peak+normal, accept/decline."""
    def t(h, m=0):
        return f"{date}T{h:02d}:{m:02d}:00+07:00"
    trips = [
        {"schema_version": "1.0.0", "order_id": f"o{i}", "driver_id": driver,
         "service_type": "bike", "t_request": t(h), "t_assign": t(h),
         "t_pickup": t(h), "t_complete": t(h, 20),
         "pickup": {"lat": 21.0, "lon": 105.8, "h3": "x"},
         "drop": {"lat": 21.0, "lon": 105.8, "h3": "y"},
         "dist_km": 3.0, "gross_vnd": 17000, "source": "MOCK"}
        for i, h in enumerate([7, 7, 7, 10, 10, 16])  # 3 peak(30) + 2 normal(10) + 1 peak(10) = 50đ
    ]
    events = ([{"schema_version": "1.0.0", "event_id": f"a{i}", "driver_id": driver,
                "t": t(7), "kind": "accept", "source": "MOCK"} for i in range(9)]
              + [{"schema_version": "1.0.0", "event_id": f"dc{i}", "driver_id": driver,
                  "t": t(7), "kind": "decline", "source": "MOCK"} for i in range(1)]
              + [{"schema_version": "1.0.0", "event_id": f"c{i}", "driver_id": driver,
                  "t": t(7), "kind": "complete", "source": "MOCK"} for i in range(6)]
              + [{"schema_version": "1.0.0", "event_id": "on", "driver_id": driver,
                  "t": t(6), "kind": "go_online", "source": "MOCK"}])
    return {"trip_record": trips, "app_event": events}


def test_derive_bonus_gap_input_schema(reg, policy):
    l1 = _mk_l1()
    gi = derive_bonus_gap_input("d-1", "2026-07-01T18:00:00+07:00", l1, policy,
                                 shift_window=[360, 1320], history=[])
    assert reg.validate("bonus_gap_input", gi) == []
    # points_now = 3×10 + 2×5 + 1×10 = 50
    assert gi["points_now"] == 50
    # acceptance = 9/(9+1) = 0.9
    assert abs(gi["acceptance_rate"] - 0.9) < 1e-9
    # next_tiers: mốc >50 → [60,100,160,200]
    assert gi["next_tiers"][0] == [60, 30000]


# ---------- Unit 3: solver ----------

def _gap_input(points_now=140, acceptance=0.9, completion=0.9, hours_budget=3.0,
               hist=None, t_now="2026-07-01T18:00:00+07:00"):
    return {
        "schema_version": "1.0.0", "driver_id": "d-1", "t_now": t_now,
        "points_now": points_now,
        "next_tiers": [[t, v] for t, v in POLICY_REC["day_bonus_tiers"] if t > points_now],
        "historical_points_per_hour": hist or {},
        "hours_budget_remaining": hours_budget,
        "acceptance_rate": acceptance, "completion_rate": completion,
        "policy_bundle_version": "sim-policy-v0", "view_version": "1.0.0", "source": "MOCK",
    }


def test_solve_feasible(policy):
    # 140đ, mốc 160 (thiếu 20), rate historical 15đ/h → 1.33h ≤ 3h, tỷ lệ đủ → feasible
    r = solve(_gap_input(hist={"offpeak": 15.0, "peak": 25.0}), policy)
    assert r["infeasible_reason"] is None
    sol = r["solution"]
    assert sol["feasible"] is True
    assert sol["gap_points"] == 20
    assert sol["hours_needed"] == pytest.approx(20 / 15.0, abs=0.01)


def test_solve_infeasible_hours(policy):
    # thiếu 60 điểm, rate 15/h → 4h > quỹ 2h → infeasible vì GIỜ
    r = solve(_gap_input(points_now=100, hours_budget=2.0, hist={"offpeak": 15.0}), policy)
    assert r["infeasible_reason"] is not None
    assert "giờ" in r["infeasible_reason"].lower() or "gio" in r["infeasible_reason"].lower()
    assert r["solution"]["feasible"] is False


def test_solve_infeasible_acceptance(policy):
    # đủ điểm+giờ nhưng acceptance 0.80 < 0.85 → infeasible vì TỶ LỆ (đa ràng buộc)
    r = solve(_gap_input(acceptance=0.80, hist={"offpeak": 15.0}), policy)
    assert r["solution"]["feasible"] is False
    assert "nhận" in r["infeasible_reason"] or "0.8" in r["infeasible_reason"]


def test_number_traceability(policy):
    r = solve(_gap_input(hist={"offpeak": 15.0}), policy)
    assert r["numbers"], "phải có numbers"
    for n in r["numbers"]:
        assert n["source"], f"số {n} thiếu source (traceability != 1.0)"
        assert any(n["source"].startswith(p) for p in
                   ("policy_v", "historical", "dp", "ledger")), n["source"]


def test_sensitivity_rate_flips(policy):
    # feasible sát biên; rate−40% phải đảo sang infeasible
    r = solve(_gap_input(points_now=110, hours_budget=3.4, hist={"offpeak": 15.0}), policy)
    rate_sens = [s for s in r["sensitivity"] if "rate" in s.get("param", "")]
    assert rate_sens, "phải có sensitivity theo rate"
    assert any(s.get("flips_feasible") for s in rate_sens), "rate−40% phải đảo feasible"


def test_acceptance_cliff_warning(policy):
    # acceptance 0.86 sát ngưỡng 0.85 → cliff sensitivity
    r = solve(_gap_input(acceptance=0.86, hist={"offpeak": 15.0}), policy)
    cliff = [s for s in r["sensitivity"] if s.get("param") == "acceptance_cliff"]
    assert cliff, "acceptance sát ngưỡng phải có cliff warning"


def test_solver_report_schema(reg, policy):
    r = solve(_gap_input(hist={"offpeak": 15.0}), policy)
    assert reg.validate("solver_report", r) == []
    assert r["solver"] == "bonus_feasibility"


def test_determinism(policy):
    gi = _gap_input(hist={"offpeak": 15.0})
    assert solve(gi, policy) == solve(gi, policy)


def test_fallback_confidence(policy):
    # không có historical → fallback policy_theoretical, confidence thấp
    r = solve(_gap_input(hist={}), policy)
    assert r["confidence"] <= 0.6
    assert any("policy_theoretical" in n["source"] or "dp" in n["source"] for n in r["numbers"])


def test_already_max_tier(policy):
    # đã đạt mốc cao nhất → không có gap, feasible trivially, infeasible_reason None
    r = solve(_gap_input(points_now=210), policy)
    assert r["solution"].get("already_maxed") is True
    assert r["infeasible_reason"] is None

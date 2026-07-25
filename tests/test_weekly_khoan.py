"""PI-4b — S5 WeeklyKhoanFeasibility (TDD).

Kiểm: view hợp schema; gap/clawback đúng số học; **KHÔNG bịa số khi policy thiếu quota**;
feasibility đa ràng buộc; determinism; chain từ data thật (generate_realdata).
"""

from pathlib import Path

import pytest

from gsm_core.features.from_l1r import derive_weekly_khoan_input_l1r
from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.policy import PolicyBundle
from gsm_core.schema_registry import SchemaRegistry
from gsm_core.solvers.weekly_khoan import solve

ROOT = Path(__file__).resolve().parent.parent

BASE_POLICY = {
    "schema_version": "1.0.0", "bundle_id": "b1", "version": "sim-policy-v0",
    "effective_from": "2026-07-01T00:00:00+07:00", "track": "platform", "service": "bike",
    "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300}, "driver_share": 0.75,
    "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
               "window_hours": list(range(6, 22))},
    "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
    "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85,
                    "forced_accept_below": 0.5},
    "source_url": None, "source": "MOCK",
}
QUOTA = {"min_revenue_vnd": 2_000_000, "min_active_days": 5,
         "clawback_rate": 0.20, "market_scope": "toan_quoc"}


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def policy_with_quota():
    return PolicyBundle.from_record({**BASE_POLICY, "weekly_quota": QUOTA})


@pytest.fixture(scope="module")
def policy_no_quota():
    return PolicyBundle.from_record(BASE_POLICY)


def _view(revenue=1_500_000, days_active=4, days_remaining=2, hours=20.0,
          rate=150_000, quota=QUOTA, basis="gross"):
    return {"schema_version": "1.0.0", "driver_id": "d-1", "t_now": "2026-07-03T18:00:00+07:00",
            "week_key": "2026-W27", "week_start": "2026-06-29", "week_end": "2026-07-05",
            "revenue_so_far_vnd": revenue, "days_active": days_active,
            "days_remaining": days_remaining, "hours_budget_remaining": hours,
            "avg_revenue_per_hour": rate, "quota": quota, "money_basis": basis,
            "policy_bundle_version": "sim-policy-v0", "view_version": "1.0.0", "source": "MOCK"}


# ---------- schema ----------

def test_view_schema_valid(reg):
    assert reg.validate("weekly_khoan_input", _view()) == []


def test_report_schema_valid(reg, policy_with_quota):
    r = solve(_view(), policy_with_quota)
    assert reg.validate("solver_report", r) == []
    assert r["solver"] == "weekly_khoan"


# ---------- số học ----------

def test_gap_and_clawback_math(policy_with_quota):
    r = solve(_view(revenue=1_500_000), policy_with_quota)
    s = r["solution"]
    assert s["gap_revenue_vnd"] == 500_000               # 2tr − 1.5tr
    assert s["clawback_risk_vnd"] == 100_000             # 20% × 500k
    assert s["hours_needed"] == pytest.approx(500_000 / 150_000, abs=0.01)


def test_quota_met_no_gap(policy_with_quota):
    r = solve(_view(revenue=2_500_000), policy_with_quota)
    assert r["solution"]["gap_revenue_vnd"] == 0
    assert r["solution"]["clawback_risk_vnd"] == 0
    assert r["solution"]["feasible"] is True
    assert r["infeasible_reason"] is None


def test_infeasible_not_enough_hours(policy_with_quota):
    """thiếu 1.5tr, rate 100k/h → cần 15h nhưng quỹ 5h → infeasible."""
    r = solve(_view(revenue=500_000, rate=100_000, hours=5.0), policy_with_quota)
    assert r["solution"]["feasible"] is False
    assert "giờ" in r["infeasible_reason"]


def test_infeasible_min_active_days(policy_with_quota):
    """đủ doanh số nhưng không thể đạt 5 ngày hoạt động → infeasible."""
    r = solve(_view(revenue=1_900_000, days_active=1, days_remaining=1, rate=500_000),
              policy_with_quota)
    assert r["solution"]["constraints"]["ok_active_days"] is False
    assert "ngày" in r["infeasible_reason"]


# ---------- §5: KHÔNG bịa số ----------

def test_no_quota_does_not_invent_numbers(reg, policy_no_quota):
    """BẤT BIẾN §5: policy thiếu số khoán → báo rõ, KHÔNG đoán mốc."""
    v = _view(quota=None)
    assert reg.validate("weekly_khoan_input", v) == []
    r = solve(v, policy_no_quota)
    assert reg.validate("solver_report", r) == []
    assert r["solution"]["quota_available"] is False
    assert r["solution"]["feasible"] is None
    assert "TBC" in r["infeasible_reason"] or "thiếu" in r["infeasible_reason"]
    # không có số nào mang nhãn policy (chỉ số đo được)
    assert all("policy_v" not in n["source"] for n in r["numbers"]), r["numbers"]
    assert "gap_revenue_vnd" not in r["solution"]


def test_number_traceability_and_basis(policy_with_quota):
    r = solve(_view(), policy_with_quota)
    assert r["numbers"]
    for n in r["numbers"]:
        assert n["source"], "traceability != 1.0"
        assert "basis=" in n["source"] or n["source"].startswith("historical:")


def test_missing_rate_no_crash(policy_with_quota):
    """Thiếu lịch sử rate → không ước được giờ, vẫn trả report hợp lệ."""
    r = solve(_view(rate=None), policy_with_quota)
    assert r["solution"]["hours_needed"] is None
    assert r["solution"]["feasible"] is False
    assert any("lịch sử" in c for c in r["caveats"])


def test_determinism(policy_with_quota):
    assert solve(_view(), policy_with_quota) == solve(_view(), policy_with_quota)


def test_sensitivity_flips(policy_with_quota):
    """Sát biên: rate −40% phải lật feasible."""
    r = solve(_view(revenue=1_500_000, rate=150_000, hours=3.4), policy_with_quota)
    rate_sens = [s for s in r["sensitivity"] if "rate" in s.get("param", "")]
    assert rate_sens and any(s["flips_feasible"] for s in rate_sens)


# ---------- chain từ data thật ----------

def test_end_to_end_from_realdata(reg, policy_with_quota):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tables = generate_realdata(days=8, seed_base=400, out_dir=Path(td))["tables"]
    drv = tables["driver_income_daily"][0]["driver_id"]
    d = tables["driver_income_daily"][0]["order_date"]
    v = derive_weekly_khoan_input_l1r(drv, f"{d}T18:00:00+07:00", tables, policy_with_quota)
    assert reg.validate("weekly_khoan_input", v) == [], v
    assert v["money_basis"] == "gross"
    r = solve(v, policy_with_quota)
    assert reg.validate("solver_report", r) == []
    assert r["solution"]["revenue_so_far_vnd"] == v["revenue_so_far_vnd"]


def test_view_gross_matches_income_sum(policy_with_quota):
    """revenue_so_far = Σ total_fee (GROSS) trong tuần — đúng quyết định (d)."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tables = generate_realdata(days=8, seed_base=401, out_dir=Path(td))["tables"]
    drv = tables["driver_income_daily"][0]["driver_id"]
    d = tables["driver_income_daily"][0]["order_date"]
    v = derive_weekly_khoan_input_l1r(drv, f"{d}T18:00:00+07:00", tables, policy_with_quota)
    expected = sum(r["total_fee"] for r in tables["driver_income_daily"]
                   if r["driver_id"] == drv and v["week_start"] <= r["order_date"] <= v["week_end"])
    assert v["revenue_so_far_vnd"] == expected

"""PI-4a — adapter l1r → L3 views + chain vào solver THẬT.

End-to-end: generate_realdata (13 bảng shape thật) → derive L3 view → validate schema
→ solver → SolverReport. Kiểm measured field ĐỌC THẲNG (không recompute lệch).
"""

from pathlib import Path

import pytest

from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.features.from_l1r import (derive_bonus_gap_input_l1r,
                                         derive_session_summary_input_l1r,
                                         derive_shift_plan_input_l1r)
from gsm_core.policy import PolicyBundle
from gsm_core.solvers.bonus_feasibility import solve as solve_s1
from gsm_core.schema_registry import SchemaRegistry

ROOT = Path(__file__).resolve().parent.parent

POLICY_REC = {
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


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(POLICY_REC)


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def l1r(tmp_path_factory):
    out = tmp_path_factory.mktemp("l1r")
    return generate_realdata(days=8, seed_base=300, out_dir=out)["tables"]


@pytest.fixture(scope="module")
def sample(l1r):
    """1 driver-day có cuốc (ưu tiên driver có nhiều ngày lịch sử)."""
    rows = sorted(l1r["driver_income_daily"], key=lambda r: -r["total_order"])
    r = rows[0]
    return r["driver_id"], r["order_date"]


# ---------- S1 bonus_gap ----------

def test_bonus_gap_view_valid(reg, l1r, policy, sample):
    drv, d = sample
    v = derive_bonus_gap_input_l1r(drv, f"{d}T18:00:00+07:00", l1r, policy, shift_window=[360, 1320])
    assert reg.validate("bonus_gap_input", v) == [], v


def test_acceptance_read_from_measured_field(l1r, policy, sample):
    """CỐT LÕI PI-4a: acceptance ĐỌC THẲNG statistic_daily, KHÔNG tự đếm lệch."""
    drv, d = sample
    stat = next(s for s in l1r["driver_statistic_daily"]
                if s["driver_id"] == drv and s["local_date"] == d)
    v = derive_bonus_gap_input_l1r(drv, f"{d}T18:00:00+07:00", l1r, policy)
    assert v["acceptance_rate"] == round(stat["acceptance_rate"], 4)
    assert v["completion_rate"] == round(stat["fulfillment_rate"], 4)


def test_bonus_gap_chains_into_solver(reg, l1r, policy, sample):
    """view thật → S1 solve → SolverReport hợp schema + mọi số có source (traceability=1.0)."""
    drv, d = sample
    v = derive_bonus_gap_input_l1r(drv, f"{d}T18:00:00+07:00", l1r, policy, shift_window=[360, 1320])
    rep = solve_s1(v, policy)
    assert reg.validate("solver_report", rep) == []
    assert rep["numbers"], "solver phải trả numbers"
    assert all(n["source"] for n in rep["numbers"]), "number_traceability != 1.0"


def test_points_computed_nonnegative(l1r, policy, sample):
    drv, d = sample
    v = derive_bonus_gap_input_l1r(drv, f"{d}T18:00:00+07:00", l1r, policy)
    assert v["points_now"] >= 0
    assert all(t[0] > v["points_now"] for t in v["next_tiers"])


# ---------- S3 session_summary ----------

def test_session_summary_view_valid(reg, l1r, policy, sample):
    drv, d = sample
    v = derive_session_summary_input_l1r(drv, d, l1r, policy)
    assert reg.validate("session_summary_input", v) == [], v


def test_payout_breakdown_from_measured(l1r, policy, sample):
    """gross=total_fee, payout=commission ĐỌC THẲNG; gross ≥ payout; net=None (chưa đủ cost)."""
    drv, d = sample
    inc = next(r for r in l1r["driver_income_daily"]
               if r["driver_id"] == drv and r["order_date"] == d)
    v = derive_session_summary_input_l1r(drv, d, l1r, policy)
    pb = v["payout_breakdown"]
    assert pb["gross_vnd"] == inc["total_fee"]
    assert pb["driver_payout_vnd"] == inc["commission"]
    assert pb["gross_vnd"] >= pb["driver_payout_vnd"]
    assert pb["estimated_net_vnd"] is None and pb["net_definition_version"] is None


def test_session_summary_trips_match_day(l1r, policy, sample):
    drv, d = sample
    v = derive_session_summary_input_l1r(drv, d, l1r, policy)
    assert v["trips"], "phải có cuốc"
    assert all(t["complete_time"][:10] == d for t in v["trips"])
    inc = next(r for r in l1r["driver_income_daily"]
               if r["driver_id"] == drv and r["order_date"] == d)
    assert len(v["trips"]) == inc["total_order"]


# ---------- S2 shift_plan ----------

def test_shift_plan_view_valid(reg, l1r, policy, sample):
    drv, d = sample
    v = derive_shift_plan_input_l1r(drv, f"{d}T14:00:00+07:00", l1r, policy)
    assert reg.validate("shift_plan_input", v) == [], v


def test_shift_plan_demand_forecast_from_real_trips(l1r, policy, sample):
    """demand_forecast = expected_orders/ngày theo (giờ × H3 cell) từ trips THẬT.
    soc=None (13 bảng không có telemetry pin); buckets_remaining = SỐ bucket (int)."""
    drv, d = sample
    v = derive_shift_plan_input_l1r(drv, f"{d}T14:00:00+07:00", l1r, policy)
    assert v["soc_pct"] is None
    assert isinstance(v["buckets_remaining"], int) and v["buckets_remaining"] == 10  # 14h→24h
    assert v["demand_forecast"], "phải có forecast từ trips thật"
    for f in v["demand_forecast"]:
        assert set(f) == {"bucket", "cell_cluster", "expected_orders"}
        assert f["expected_orders"] >= 0
        assert f["bucket"][11:13] >= "14", "chỉ forecast bucket còn lại"


# ---------- robustness ----------

def test_unknown_driver_no_crash(reg, l1r, policy):
    """Driver không có data → view vẫn hợp schema (không crash, không bịa số)."""
    v = derive_bonus_gap_input_l1r("d-KHONG-TON-TAI", "2026-07-01T18:00:00+07:00", l1r, policy)
    assert reg.validate("bonus_gap_input", v) == []
    assert v["points_now"] == 0
    s = derive_session_summary_input_l1r("d-KHONG-TON-TAI", "2026-07-01", l1r, policy)
    assert reg.validate("session_summary_input", s) == []
    assert s["payout_breakdown"]["gross_vnd"] == 0


def test_no_measured_row_is_labeled_estimated(reg, l1r, policy, sample):
    """Adversarial self-review: KHÔNG bịa acceptance=1.0 "như thể đo được" khi thiếu dòng đo.
    → carry-forward giá trị đo gần nhất + hạ nhãn source = ESTIMATED (§5 truy vết)."""
    drv, _ = sample
    v = derive_bonus_gap_input_l1r(drv, "2026-07-30T06:00:00+07:00", l1r, policy)  # ngày không có stat
    assert reg.validate("bonus_gap_input", v) == []
    assert v["source"] == "ESTIMATED", "thiếu dòng đo phải hạ nhãn, không giả vờ measured"
    prior = sorted((r for r in l1r["driver_statistic_daily"] if r["driver_id"] == drv),
                   key=lambda r: r["local_date"])
    assert v["acceptance_rate"] == round(prior[-1]["acceptance_rate"], 4), "phải carry-forward số ĐO gần nhất"
    # driver chưa từng có dữ liệu → vẫn ESTIMATED (không phải MOCK/REAL)
    v2 = derive_bonus_gap_input_l1r("d-CHUA-CO", "2026-07-30T06:00:00+07:00", l1r, policy)
    assert v2["source"] == "ESTIMATED"


def test_provenance_label_follows_source(l1r, policy, sample):
    """source view theo record nguồn (mock data → MOCK), không hard-code sai."""
    drv, d = sample
    v = derive_bonus_gap_input_l1r(drv, f"{d}T18:00:00+07:00", l1r, policy)
    assert v["source"] in ("MOCK", "REAL")
    assert v["source"] == "MOCK"  # data hiện tại là mock


# ---------- AUDIT A1 (UPDATE-065): S5-1 — view tuần không được rò tương lai ----------


def test_weekly_view_no_future_leak(l1r, policy):
    """`revenue_so_far` đứng ở NGÀY GIỮA tuần không được gộp doanh thu các ngày SAU đó.

    Dataset fixture có đủ 8 ngày — nếu view lọc theo cả tuần thì revenue(giữa tuần)
    == revenue(cuối tuần) → rò tương lai (S5-1)."""
    from datetime import date as _date_cls
    from collections import defaultdict
    from gsm_core.features.from_l1r import derive_weekly_khoan_input_l1r
    drv = l1r["driver_income_daily"][0]["driver_id"]
    dates = sorted({r["order_date"] for r in l1r["driver_income_daily"]
                    if r["driver_id"] == drv})
    by_week: dict = defaultdict(list)
    for d in dates:
        iso = _date_cls.fromisoformat(d).isocalendar()
        by_week[(iso.year, iso.week)].append(d)
    week_dates = max(by_week.values(), key=len)   # tuần có nhiều ngày nhất trong fixture
    assert len(week_dates) >= 3, "fixture 8 ngày phải có 1 tuần ISO chứa ≥3 ngày"
    first, last = week_dates[0], week_dates[-1]
    v_mid = derive_weekly_khoan_input_l1r(drv, f"{first}T23:59:00+07:00", l1r, policy)
    v_last = derive_weekly_khoan_input_l1r(drv, f"{last}T23:59:00+07:00", l1r, policy)
    assert v_mid["week_key"] == v_last["week_key"]
    assert v_mid["revenue_so_far_vnd"] < v_last["revenue_so_far_vnd"], \
        "đứng đầu tuần mà revenue bằng cuối tuần — view đang đọc TƯƠNG LAI"
    assert v_mid["days_active"] < v_last["days_active"]

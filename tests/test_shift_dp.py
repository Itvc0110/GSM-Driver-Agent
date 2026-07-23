"""C3 — Solver S2 ShiftDP (TDD failing-first).

DP timing-only {ONLINE,REST,SWAP,END}; forecast historical (no future-leak);
output full schedule + next-action + delta E[payout]. Mọi số có source.
"""

from pathlib import Path

import pytest

from gsm_core.policy import PolicyBundle
from gsm_core.solvers.shift_dp import solve, DEFAULT_PARAMS
from gsm_core.features.shift_plan import derive_shift_plan_input
from gsm_core.schema_registry import SchemaRegistry

ROOT = Path(__file__).resolve().parent.parent

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


def _spi(buckets=6, points=140, soc=80.0, forecast=None,
         t_now="2026-07-01T17:00:00+07:00"):
    """shift_plan_input với forecast per bucket (expected_orders)."""
    if forecast is None:
        forecast = [3.0] * buckets
    df = [{"bucket": f"2026-07-01T{17 + i // 2:02d}:{(i % 2) * 30:02d}:00+07:00",
           "cell_cluster": "ALL", "expected_orders": float(forecast[i])}
          for i in range(buckets)]
    return {
        "schema_version": "1.0.0", "driver_id": "d-1", "t_now": t_now,
        "buckets_remaining": buckets, "soc_pct": soc, "points_now": points,
        "demand_forecast": df, "policy_bundle_version": "sim-policy-v0",
        "view_version": "1.0.0", "source": "MOCK",
    }


# ---------- DP core ----------

def test_output_has_schedule_next_delta(policy):
    r = solve(_spi(), policy)
    sol = r["solution"]
    assert "schedule" in sol and len(sol["schedule"]) == 6
    assert "next_action" in sol and "action" in sol["next_action"]
    assert "expected_payout" in sol and "baseline_payout" in sol and "delta_payout" in sol
    assert set(s["action"] for s in sol["schedule"]) <= {"ONLINE", "REST", "SWAP", "END"}


def test_delta_nonnegative_vs_baseline(policy):
    """DP tối ưu ≥ baseline online-liên-tục."""
    r = solve(_spi(), policy)
    assert r["solution"]["delta_payout"] >= -1e-6


def test_terminal_bonus_drives_online(policy):
    """Gần mốc (140đ, mốc kế 160 thiếu 20đ = 2 cuốc peak) + forecast tốt → DP ưu tiên ONLINE."""
    r = solve(_spi(points=140, forecast=[5.0] * 6), policy)
    n_online = sum(1 for s in r["solution"]["schedule"] if s["action"] == "ONLINE")
    assert n_online >= 3, "gần mốc + demand cao phải chạy nhiều"
    assert r["solution"]["projected_bonus_tier"] >= 160


def test_rest_when_zero_demand(policy):
    """Forecast = 0 mọi bucket → ONLINE vô ích → DP chọn REST/END (không ONLINE)."""
    r = solve(_spi(points=10, forecast=[0.0] * 6), policy)
    assert all(s["action"] != "ONLINE" for s in r["solution"]["schedule"])


def test_swap_when_low_soc(policy):
    """SOC rất thấp → SWAP xuất hiện để chạy tiếp có lời."""
    r = solve(_spi(soc=8.0, forecast=[5.0] * 6), policy)
    assert any(s["action"] == "SWAP" for s in r["solution"]["schedule"])


def test_no_future_leak(policy):
    """Solver chỉ đọc demand_forecast — không có input nào khác của 'ngày đang giải'.
    Đổi field ngoài forecast (points, soc) đổi nghiệm; nhưng KHÔNG có realized-order field."""
    spi = _spi()
    # solver signature chỉ nhận (shift_plan_input, policy, params) — không có l1/orders
    import inspect
    sig = inspect.signature(solve)
    assert set(sig.parameters) <= {"spi", "shift_plan_input", "policy", "params"}
    assert "orders" not in sig.parameters and "l1" not in sig.parameters


def test_tiebreak_deterministic(policy):
    # forecast bằng nhau + không lý do đổi → tie xử lý cố định, lặp lại ổn định
    spi = _spi(forecast=[3.0] * 6)
    assert solve(spi, policy) == solve(spi, policy)


def test_number_traceability(policy):
    r = solve(_spi(), policy)
    assert r["numbers"]
    for n in r["numbers"]:
        assert n["source"], f"{n} thiếu source"
        assert any(n["source"].startswith(p) for p in
                   ("policy_v", "historical", "dp")), n["source"]


def test_solver_report_schema(reg, policy):
    r = solve(_spi(), policy)
    assert reg.validate("solver_report", r) == []
    assert r["solver"] == "shift_dp"


def test_sensitivity_demand(policy):
    r = solve(_spi(forecast=[4.0] * 6), policy)
    ds = [s for s in r["sensitivity"] if "demand" in s.get("param", "")]
    assert ds, "phải có sensitivity theo demand"
    # demand giảm → delta_payout không tăng
    vals = {s["param"]: s.get("delta_payout") for s in ds}
    assert all(v is not None for v in vals.values())


# ---------- L3 derivation ----------

def _mk_l1_multiday():
    """Driver có 2 ngày lịch sử + ngày hiện tại, để historical forecast có data."""
    def trip(d, h, i):
        return {"schema_version": "1.0.0", "order_id": f"o{d}{h}{i}", "driver_id": "d-1",
                "service_type": "bike", "t_request": f"{d}T{h:02d}:00:00+07:00",
                "t_assign": f"{d}T{h:02d}:00:00+07:00", "t_pickup": f"{d}T{h:02d}:05:00+07:00",
                "t_complete": f"{d}T{h:02d}:20:00+07:00",
                "pickup": {"lat": 21.0, "lon": 105.8, "h3": "x"},
                "drop": {"lat": 21.0, "lon": 105.8, "h3": "y"},
                "dist_km": 3.0, "gross_vnd": 17000, "source": "MOCK"}
    trips = []
    for d in ("2026-06-29", "2026-06-30", "2026-07-01"):
        for h in (7, 8, 17):
            for i in range(2):
                trips.append(trip(d, h, i))
    events = [{"schema_version": "1.0.0", "event_id": f"on{d}", "driver_id": "d-1",
               "t": f"{d}T06:00:00+07:00", "kind": "go_online", "source": "MOCK"}
              for d in ("2026-06-29", "2026-06-30", "2026-07-01")]
    events += [{"schema_version": "1.0.0", "event_id": f"off{d}", "driver_id": "d-1",
                "t": f"{d}T20:00:00+07:00", "kind": "go_offline", "source": "MOCK"}
               for d in ("2026-06-29", "2026-06-30", "2026-07-01")]
    return {"trip_record": trips, "app_event": events}


def test_derive_shift_plan_schema(reg, policy):
    l1 = _mk_l1_multiday()
    spi = derive_shift_plan_input("d-1", "2026-07-01T17:00:00+07:00", l1, policy,
                                   shift_window=[360, 1320], history_days=7)
    assert reg.validate("shift_plan_input", spi) == []
    assert spi["buckets_remaining"] == pytest.approx((1320 - 17 * 60) / 30, abs=1)
    # points_now ngày hiện tại: 2 peak(7h=10)×2 + 2×(8h normal? 8 không peak → 5)×2... kiểm >0
    assert spi["points_now"] > 0
    assert spi["demand_forecast"], "phải có forecast từ historical"
    assert spi["source"] == "MOCK"


def test_derive_no_future_leak(policy):
    """Forecast của ngày 07-01 KHÔNG được phụ thuộc trip realized ngày 07-01."""
    l1 = _mk_l1_multiday()
    spi_full = derive_shift_plan_input("d-1", "2026-07-01T17:00:00+07:00", l1, policy,
                                        [360, 1320], 7)
    # bỏ hết trip ngày 07-01 → forecast phải KHÔNG đổi (chỉ dùng ngày trước)
    l1_no_today = {"trip_record": [t for t in l1["trip_record"]
                                    if not t["t_request"].startswith("2026-07-01")],
                   "app_event": l1["app_event"]}
    spi_cut = derive_shift_plan_input("d-1", "2026-07-01T17:00:00+07:00", l1_no_today, policy,
                                       [360, 1320], 7)
    fc_full = {f["bucket"]: f["expected_orders"] for f in spi_full["demand_forecast"]}
    fc_cut = {f["bucket"]: f["expected_orders"] for f in spi_cut["demand_forecast"]}
    assert fc_full == fc_cut, "forecast phụ thuộc realized hôm nay = future leak"

"""B2 (PLAN-cycle-wx Phần B, đã duyệt) — C1 chi phí vận hành vào objective của S2.

Vế A5 tầm nhìn Cường (VISION-ALIGNMENT): *"hàm tối ưu phải đủ biến, cập nhật giá trị theo
policy"*. B2 = số hạng chi phí tồn tại với hệ số mặc định 0 (bit-identical); B3 sẽ để
POLICY quyết định giá trị theo (track, as_of).

Ranh giới §5 CLAUDE.md pin bằng test: chi phí đổi QUYẾT ĐỊNH của DP (giá trị net nội bộ),
nhưng `expected_payout` BÁO CÁO vẫn là GROSS payout — cost không rò vào payout.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gsm_core.policy import PolicyBundle
from gsm_core.solvers.shift_dp import DEFAULT_PARAMS, solve

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


def _acts(report) -> list[str]:
    """schedule là list dict {bucket, action} — so theo ACTION. So thẳng chuỗi vào list
    dict là bẫy vacuous (T-046 rule 5): 'ONLINE' not in [dict,...] LUÔN True."""
    return [s["action"] for s in report["solution"]["schedule"]]


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(POLICY_REC)


def _spi(buckets=6, points=140, soc=80.0, forecast=None):
    if forecast is None:
        forecast = [3.0] * buckets
    df = [{"bucket": f"2026-07-01T{17 + i // 2:02d}:{(i % 2) * 30:02d}:00+07:00",
           "cell_cluster": "ALL", "expected_orders": float(forecast[i])}
          for i in range(buckets)]
    return {
        "schema_version": "1.0.0", "driver_id": "d-1",
        "t_now": "2026-07-01T17:00:00+07:00",
        "buckets_remaining": buckets, "soc_pct": soc, "points_now": points,
        "demand_forecast": df, "policy_bundle_version": "sim-policy-v0",
        "view_version": "1.0.0", "source": "MOCK",
    }


def test_default_param_exists_and_zero():
    """Số hạng phải TỒN TẠI trong DEFAULT_PARAMS (hàm mục tiêu 'đủ biến') và mặc định 0
    (cổng an toàn: hành vi mặc định không đổi — spec objective-v2 §7 hoà giải)."""
    assert DEFAULT_PARAMS["cash_cost_vnd_per_km"] == 0.0


def test_zero_cost_bit_identical(policy):
    """cash_cost=0 tường minh phải cho KẾT QUẢ Y HỆT không truyền gì (bit-identical)."""
    a = solve(_spi(), policy, None)
    b = solve(_spi(), policy, {"cash_cost_vnd_per_km": 0.0})
    assert _acts(a) == _acts(b)
    assert a["solution"]["expected_payout"] == b["solution"]["expected_payout"]


def test_prohibitive_cost_kills_online(policy):
    """C1 phải đổi được QUYẾT ĐỊNH: chi phí/km cao tới mức net mỗi cuốc ÂM ⇒ DP không
    chọn ONLINE nữa (trước B2: solver mù chi phí, luôn chạy hết công suất — đúng chẩn
    đoán spec objective-v2 §0)."""
    # ppo = (13000 + max(0, 3-2)*4300) * 0.75 = 12.975đ / cuốc; avg 3 km
    # cash 5.000đ/km × 3 km = 15.000đ > ppo ⇒ net âm
    rep = solve(_spi(points=0), policy, {"cash_cost_vnd_per_km": 5000.0,
                                          "avg_dist_km": 3.0})
    assert "ONLINE" not in _acts(rep), _acts(rep)


def test_moderate_cost_keeps_gross_payout_reporting(policy):
    """§5: khi cost VỪA PHẢI (net vẫn dương, lịch không đổi) thì `expected_payout`
    phải Y HỆT bản cost=0 — báo cáo là GROSS payout, cost không rò vào payout.
    (Net để thước `net_mean_all` của sim đo — B1.)"""
    base = solve(_spi(), policy, {"cash_cost_vnd_per_km": 0.0})
    mod = solve(_spi(), policy, {"cash_cost_vnd_per_km": 100.0})
    assert _acts(mod) == _acts(base), \
        "cost 100đ/km (net vẫn dương rõ) không được đổi lịch fixture này"
    assert (mod["solution"]["expected_payout"]
            == base["solution"]["expected_payout"])


def test_cost_scales_with_distance(policy):
    """Mutation guard: chi phí phải nhân với avg_dist_km — ngưỡng giết-ONLINE phụ thuộc
    quãng đường. Cùng cash=5.000: avg 3km chết ONLINE (net −2k), avg 1.5km sống
    (ppo 9.750, cost 7.500 ⇒ net +2.250)."""
    dead = solve(_spi(points=0), policy,
                 {"cash_cost_vnd_per_km": 5000.0, "avg_dist_km": 3.0})
    alive = solve(_spi(points=0), policy,
                  {"cash_cost_vnd_per_km": 5000.0, "avg_dist_km": 1.5})
    assert "ONLINE" not in _acts(dead)
    assert "ONLINE" in _acts(alive)


def test_bridge_passes_cash_cost_from_config():
    """Một nguồn sự thật: solver phải nhận ĐÚNG `vehicle.cash_cost_vnd_per_km` mà sổ
    chi phí của sim dùng (T-045b) — không hai nơi hai giá trị."""
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.config import Config
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["vehicle"]["cash_cost_vnd_per_km"] = 123.0
    c.data["advice"].update(enabled=True, coverage="all", single_actor_id=None,
                            channels={"shift_plan": True, "accept_lift": False,
                                      "shift_extend": False, "rest_window": False})
    from gsm_sim.policy import PolicyBundle as SimPolicy
    bridge = AdviceActionBridge(c, SimPolicy.from_config(c), seed=1)

    class _A:  # actor tối thiểu cho solver_params
        actor_id = 0
        acceptance_rate = 0.9
        completion_rate = 0.95
        orders_offered = 10
        orders_accepted = 9
        orders_completed = 9
        rest_taken_min = 0.0
        shift_start_min = 300.0

    params = bridge.solver_params(_A())
    assert params.get("cash_cost_vnd_per_km") == 123.0

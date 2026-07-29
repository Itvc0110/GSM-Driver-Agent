"""C5 (spec objective-v2 §6 bước 2, vế còn lại — plan duyệt 2026-07-29) — SWAP có GIÁ.

Trước C5: nhánh SWAP của DP cộng đúng 0.0 — đổi pin miễn phí tuyệt đối kể cả sau
31/03/2029 (phí thật 9.000đ/lượt official). C5 KHÔNG bịa hàm phạt phi tuyến (số bịa —
lý do C2-fatigue bị bác); tính phí THẬT tại SỰ KIỆN swap từ policy. "Phi tuyến" nổi lên
nội sinh: DP tự tránh swap thừa, tự cân "chạy nốt hay giữ pin".

Chống ĐẾM KÉP với B3: khi battery ACTIVE per_swap, `cash_per_km` chỉ còn phần nền
by_track (không cộng khấu hao fee/range nữa) — một đồng trừ đúng một lần.
"""

from __future__ import annotations

import pytest

from gsm_core.policy import PolicyBundle, resolve_cost_params
from gsm_core.solvers.shift_dp import DEFAULT_PARAMS, solve

COSTS = {
    "battery_free_until": "2029-03-31",
    "swap_fee_vnd": 9000,
    "battery_rent_vnd_month": 175000,
    "swap_range_km_per_pack": 60.0,
    "cash_cost_vnd_per_km_by_track": {"platform": 0.0, "charge": 80.0},
}


def _rec(costs=None, track="platform"):
    r = {
        "schema_version": "1.1.0" if costs is not None else "1.0.0",
        "bundle_id": "b1", "version": "sim-policy-v0",
        "effective_from": "2026-07-01T00:00:00+07:00", "track": track, "service": "bike",
        "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300},
        "driver_share": 0.75,
        "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
                   "window_hours": list(range(6, 22))},
        "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
        "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85},
        "source_url": None, "source": "MOCK",
    }
    if costs is not None:
        r["costs"] = costs
    return r


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(_rec(costs=COSTS))


def _acts(report):
    return [s["action"] for s in report["solution"]["schedule"]]


def _spi(buckets=6, points=0, soc=80.0, forecast=None):
    if forecast is None:
        forecast = [3.0] * buckets
    df = [{"bucket": f"2026-07-01T{17 + i // 2:02d}:{(i % 2) * 30:02d}:00+07:00",
           "cell_cluster": "ALL", "expected_orders": float(forecast[i])}
          for i in range(buckets)]
    return {"schema_version": "1.0.0", "driver_id": "d-1",
            "t_now": "2026-07-01T17:00:00+07:00", "buckets_remaining": buckets,
            "soc_pct": soc, "points_now": points, "demand_forecast": df,
            "policy_bundle_version": "sim-policy-v0", "view_version": "1.0.0",
            "source": "MOCK"}


# ---------- 1. cổng an toàn ----------

def test_default_zero_and_identical(policy):
    assert DEFAULT_PARAMS["swap_fee_vnd"] == 0.0
    a = solve(_spi(soc=22.0), policy, None)
    b = solve(_spi(soc=22.0), policy, {"swap_fee_vnd": 0.0})
    assert _acts(a) == _acts(b)
    assert a["solution"]["expected_payout"] == b["solution"]["expected_payout"]


# ---------- 2. fee đổi QUYẾT ĐỊNH ----------

def test_fee_kills_marginal_swap(policy):
    """SOC thấp + đuôi demand mỏng: fee=0 thì swap để vét vài cuốc lãi mỏng; fee 9.000đ
    (> tổng lãi đuôi) ⇒ DP bỏ swap. Fixture: soc đủ ~2 bucket; đuôi 4 bucket demand 0.2
    cuốc/bucket ⇒ lãi đuôi ≈ 4×0.2×0.9×12.975 ≈ 9.3k... chỉnh 0.15 ⇒ ≈7k < 9k."""
    spi = _spi(buckets=6, soc=22.0, forecast=[3.0, 3.0, 0.15, 0.15, 0.15, 0.15])
    free = solve(spi, policy, {"swap_fee_vnd": 0.0})
    paid = solve(spi, policy, {"swap_fee_vnd": 9000.0})
    assert "SWAP" in _acts(free), _acts(free)
    assert "SWAP" not in _acts(paid), _acts(paid)


# ---------- 3. chống đếm kép (as_of sau hạn) ----------

def test_no_double_count_after_deadline(policy):
    cp = resolve_cost_params(policy, as_of="2029-04-01")
    assert cp["battery"]["state"] == "ACTIVE"
    assert cp["battery"]["value"] == 9000
    assert cp["battery"]["per"] == "swap"
    # cash_per_km CHỈ còn nền by_track (platform = 0) — khấu hao fee/range KHÔNG cộng nữa
    assert cp["cash_per_km"]["value"] == 0.0
    assert "150" in cp["cash_per_km"]["reason"] or "khấu hao" in cp["cash_per_km"]["reason"], \
        "số khấu hao tham khảo phải còn trong reason để người đọc đối chiếu"


def test_solver_policy_path_prices_swap(policy):
    """as_of sau hạn ⇒ solver tự lấy fee 9.000 từ policy; terms_active nói per=swap."""
    spi = _spi(buckets=6, soc=22.0, forecast=[3.0, 3.0, 0.15, 0.15, 0.15, 0.15])
    rep = solve(spi, policy, {"policy_costs_as_of": "2029-04-01"})
    terms = {t["term"]: t for t in rep["solution"]["terms_active"]}
    assert terms["battery"]["value"] == 9000 and terms["battery"]["per"] == "swap"
    assert "SWAP" not in _acts(rep)  # cùng fixture test 2 — fee từ POLICY giết swap thừa
    before = solve(spi, policy, {"policy_costs_as_of": "2026-07-29"})
    assert "SWAP" in _acts(before)  # trước hạn: miễn phí ⇒ vẫn swap vét đuôi


# ---------- 4. §5: payout GROSS + minh bạch chi phí swap ----------

def test_gross_payout_and_swap_cost_exposed(policy):
    """Demand cao đều ⇒ swap vẫn đáng dù fee: SỐ LƯỢNG swap và GROSS payout phải y hệt.
    VỊ TRÍ swap được phép dịch (fee làm đổi tie-break giữa các vị trí ĐỒNG GIÁ TRỊ — đo
    thật: [O,O,SWAP,O,O,O] → [SWAP,O,O,O,O,O], cùng 1 swap + 5 online, cùng 70.065đ)."""
    spi = _spi(soc=22.0)
    free = solve(spi, policy, {"swap_fee_vnd": 0.0})
    paid = solve(spi, policy, {"swap_fee_vnd": 9000.0})
    assert sorted(_acts(paid)) == sorted(_acts(free)), \
        "fee không được đổi THÀNH PHẦN lịch (số swap/online) ở fixture demand cao"
    assert (paid["solution"]["expected_payout"]
            == free["solution"]["expected_payout"]), "GROSS payout không dính fee (§5)"
    n_swaps = sum(1 for a in _acts(paid) if a == "SWAP")
    assert n_swaps >= 1
    assert paid["solution"]["expected_swap_cost_vnd"] == n_swaps * 9000.0
    assert free["solution"]["expected_swap_cost_vnd"] == 0.0


# ---------- 5. baseline công bằng ----------

def test_baseline_swap_cost_exposed_delta_stays_gross(policy):
    """§5 nhất quán: `delta_payout` là số GROSS (không dính fee) — nhưng chi phí swap của
    CẢ HAI lịch phải MINH BẠCH để consumer tính net công bằng (bài học hai-tên):
    `expected_swap_cost_vnd` (lịch DP) + `baseline_swap_cost_vnd` (lịch baseline)."""
    spi = _spi(soc=22.0)
    free = solve(spi, policy, {"swap_fee_vnd": 0.0})
    paid = solve(spi, policy, {"swap_fee_vnd": 9000.0})
    assert paid["solution"]["delta_payout"] == free["solution"]["delta_payout"]
    assert paid["solution"]["baseline_payout"] == free["solution"]["baseline_payout"]
    assert paid["solution"]["baseline_swap_cost_vnd"] > 0, \
        "baseline soc=22% chắc chắn phải swap — chi phí của NÓ phải minh bạch"
    assert paid["solution"]["baseline_swap_cost_vnd"] % 9000.0 == 0
    assert free["solution"]["baseline_swap_cost_vnd"] == 0.0


# ---------- 6. bridge một-nguồn-sự-thật ----------

def test_bridge_passes_swap_fee_from_config():
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.config import Config
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["vehicle"]["swap_fee_vnd"] = 4500
    c.data["advice"].update(enabled=True, coverage="all", single_actor_id=None,
                            channels={"shift_plan": True, "accept_lift": False,
                                      "shift_extend": False, "rest_window": False})
    from gsm_sim.policy import PolicyBundle as SimPolicy
    bridge = AdviceActionBridge(c, SimPolicy.from_config(c), seed=1)

    class _A:
        actor_id = 0
        acceptance_rate = 0.9
        completion_rate = 0.95
        orders_offered = 10
        orders_accepted = 9
        orders_completed = 9
        rest_taken_min = 0.0
        shift_start_min = 300.0

    assert bridge.solver_params(_A()).get("swap_fee_vnd") == 4500.0

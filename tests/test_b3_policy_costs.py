"""B3 (PLAN-cycle-wx Phần B, đã duyệt) — POLICY quyết định giá trị chi phí theo (track, as_of).

Hiện thân trọn vẹn vế A5 tầm nhìn Cường: *"hàm tối ưu phải cập nhật giá trị biến theo
thay đổi chính sách"* + ý A1 OPEN-THREADS: *"chính sách free đổi pin hết hạn thì bỏ biến
đó, hay điền arg giá −xx đồng thay vì 0"*. Ba trạng thái ACTIVE / OFF_BY_POLICY / UNKNOWN
— CẤM gộp UNKNOWN vào OFF (bài học hidden-fallback trả giá 3 lần). Số vẫn từ policy
bundle versioned; solver/agent không bịa số (§5).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gsm_core.policy import PolicyBundle, resolve_cost_params
from gsm_core.schema_registry import SchemaRegistry
from gsm_core.solvers.shift_dp import solve

ROOT = Path(__file__).resolve().parent.parent

COSTS = {
    # nguồn: research/economics/driver-cost-structure-2026.md (official, HIGH)
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
def reg():
    return SchemaRegistry(ROOT / "schemas")


# ---------- schema bump 1.0.0 → 1.1.0 (quy trình Cycle V) ----------

def test_policy_bundle_two_versions(reg):
    assert reg.versions("policy_bundle") == ("1.0.0", "1.1.0")


def test_old_record_still_valid_new_record_with_costs_valid(reg):
    assert reg.validate("policy_bundle", _rec()) == []               # 1.0.0 không costs
    assert reg.validate("policy_bundle", _rec(costs=COSTS)) == []    # 1.1.0 có costs


def test_costs_wrong_shape_invalid(reg):
    bad = _rec(costs={**COSTS, "swap_fee_vnd": "chín nghìn"})
    assert reg.validate("policy_bundle", bad)


def test_upcaster_stamp_only(reg):
    from gsm_core.upcasters import upcast
    old = _rec()
    up = upcast("policy_bundle", dict(old))
    assert up["schema_version"] == "1.1.0"
    assert "costs" not in up, "additive-optional: không bịa costs cho record cũ"


# ---------- resolve_cost_params: 3 trạng thái ----------

def test_platform_before_deadline_battery_off_by_policy():
    """Trước 31/03/2029, Platform độc quyền: số hạng pin OFF_BY_POLICY (không phải '=0'
    chung chung) + reason đọc được nêu HẠN — đúng ý A1: 'bỏ biến đó' có lý do."""
    p = PolicyBundle.from_record(_rec(costs=COSTS))
    cp = resolve_cost_params(p, as_of="2026-07-29")
    assert cp["battery"]["state"] == "OFF_BY_POLICY"
    assert "2029-03-31" in cp["battery"]["reason"]
    assert cp["cash_per_km"]["state"] == "ACTIVE"
    assert cp["cash_per_km"]["value"] == 0.0                          # by_track platform


def test_platform_after_deadline_battery_active():
    """Sau hạn: biến pin SỐNG LẠI — swap_fee 9.000đ/lượt quy ra đ/km theo tầm pack;
    'cùng một tài xế, chi phí khác' đúng như hồ sơ chi phí §7.4."""
    p = PolicyBundle.from_record(_rec(costs=COSTS))
    cp = resolve_cost_params(p, as_of="2029-04-01")
    assert cp["battery"]["state"] == "ACTIVE"
    assert cp["battery"]["value"] == 9000
    assert cp["cash_per_km"]["state"] == "ACTIVE"
    assert cp["cash_per_km"]["value"] == pytest.approx(9000 / 60.0)   # 150 đ/km


def test_charge_track_cash_always_alive():
    p = PolicyBundle.from_record(_rec(costs=COSTS, track="charge"))
    cp = resolve_cost_params(p, as_of="2026-07-29")
    assert cp["cash_per_km"]["state"] == "ACTIVE"
    assert cp["cash_per_km"]["value"] == 80.0


def test_no_costs_block_unknown_not_off():
    """Bundle 1.0.0 không có costs ⇒ UNKNOWN (không biết) — CẤM gộp vào OFF_BY_POLICY
    (biết là miễn phí). Giá trị dùng = 0 + caveat, KHÔNG bịa (§5)."""
    p = PolicyBundle.from_record(_rec())
    cp = resolve_cost_params(p, as_of="2026-07-29")
    assert cp["cash_per_km"]["state"] == "UNKNOWN"
    assert cp["cash_per_km"]["state"] != "OFF_BY_POLICY"
    assert cp["cash_per_km"]["value"] == 0.0
    assert cp["cash_per_km"]["reason"]


def test_no_as_of_unknown():
    p = PolicyBundle.from_record(_rec(costs=COSTS))
    cp = resolve_cost_params(p, as_of=None)
    assert cp["battery"]["state"] == "UNKNOWN"


# ---------- solver đọc policy theo as_of ----------

def _spi(buckets=6, points=140, soc=80.0):
    df = [{"bucket": f"2026-07-01T{17 + i // 2:02d}:{(i % 2) * 30:02d}:00+07:00",
           "cell_cluster": "ALL", "expected_orders": 3.0} for i in range(buckets)]
    return {"schema_version": "1.0.0", "driver_id": "d-1",
            "t_now": "2026-07-01T17:00:00+07:00", "buckets_remaining": buckets,
            "soc_pct": soc, "points_now": points, "demand_forecast": df,
            "policy_bundle_version": "sim-policy-v0", "view_version": "1.0.0",
            "source": "MOCK"}


def test_solver_terms_active_before_deadline():
    """solve(..., as_of=trước hạn): terms_active phải NÓI RA số hạng pin OFF_BY_POLICY
    kèm lý do — trả lời câu hỏi thiết kế #2 của Cường (OPEN-THREADS §A1: output phải nói
    'hiện không tính chi phí pin vì miễn phí tới 31/03/2029')."""
    p = PolicyBundle.from_record(_rec(costs=COSTS))
    rep = solve(_spi(), p, {"policy_costs_as_of": "2026-07-29"})
    terms = {t["term"]: t for t in rep["solution"]["terms_active"]}
    assert terms["battery"]["state"] == "OFF_BY_POLICY"
    assert "2029-03-31" in terms["battery"]["reason"]
    assert terms["cash_per_km"]["state"] == "ACTIVE"


def test_solver_uses_policy_cash_after_deadline():
    """as_of SAU hạn ⇒ solver dùng 150đ/km từ POLICY (không ai truyền tay) — 'hàm tối ưu
    cập nhật giá trị biến theo thay đổi chính sách' thành sự thật đo được."""
    p = PolicyBundle.from_record(_rec(costs=COSTS))
    rep = solve(_spi(), p, {"policy_costs_as_of": "2029-04-01"})
    terms = {t["term"]: t for t in rep["solution"]["terms_active"]}
    assert terms["cash_per_km"]["value"] == pytest.approx(150.0)
    assert terms["cash_per_km"]["state"] == "ACTIVE"


def test_explicit_params_win_over_policy():
    """Đường sim (B2) truyền cash tường minh — explicit THẮNG policy (một nguồn sự thật
    của SIM là config; policy resolution dành cho đường production)."""
    p = PolicyBundle.from_record(_rec(costs=COSTS))
    rep = solve(_spi(), p, {"cash_cost_vnd_per_km": 70.0, "policy_costs_as_of": "2029-04-01"})
    terms = {t["term"]: t for t in rep["solution"]["terms_active"]}
    assert terms["cash_per_km"]["value"] == 70.0
    assert terms["cash_per_km"]["source"] == "params(explicit)"


def test_unknown_gives_caveat_not_fabrication():
    """Bundle không costs + as_of có ⇒ dùng 0 + caveat trong report (KHÔNG bịa số)."""
    p = PolicyBundle.from_record(_rec())
    rep = solve(_spi(), p, {"policy_costs_as_of": "2026-07-29"})
    terms = {t["term"]: t for t in rep["solution"]["terms_active"]}
    assert terms["cash_per_km"]["state"] == "UNKNOWN"
    assert any("chi phí" in c or "UNKNOWN" in c for c in rep["caveats"])


def test_no_as_of_no_terms_backward_compat():
    """Không as_of (mọi caller cũ): KHÔNG có terms_active — hành vi cũ nguyên vẹn."""
    p = PolicyBundle.from_record(_rec(costs=COSTS))
    rep = solve(_spi(), p, None)
    assert "terms_active" not in rep["solution"]

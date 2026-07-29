"""F-098-01/02 — hai defect P0 từ debate review `UPDATE-098-debate-...` (remote, `c493d89`),
agent chính REPRODUCE độc lập 2026-07-29 rồi fix. TDD: hai test đầu ĐỎ trước fix.

- F-098-01: gate `online_net > 0` trong Bellman loại nhánh ONLINE TRƯỚC khi cộng giá trị
  tương lai ⇒ solver bỏ bonus 30.000đ để né lỗ ~14đ (probe: schedule=['SWAP'], payout=0).
  Nguồn gốc: B2 đổi `online_pay > 0` (điều kiện CÓ CẦU — khả thi) thành `online_net > 0`
  (điều kiện GIÁ TRỊ) — nguyên lý DP: giá trị để Bellman so, gate chỉ được chặn khả thi.
- F-098-02: `resolve_cost_params` không gọi `is_valid_at` ⇒ bundle chỉ hiệu lực 2030 vẫn
  cấp ACTIVE 9000đ/250đ tại 2029 — "hàm tối ưu cập nhật giá trị theo chính sách" (vế A5)
  mà lại dùng chính sách ngoài thời hạn.
"""

from __future__ import annotations

import pytest

from gsm_core.policy import PolicyBundle, resolve_cost_params
from gsm_core.solvers.shift_dp import solve

_BASE = {
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


def _spi(buckets: int, points: int, forecast: list[float]) -> dict:
    df = [{"bucket": f"2026-07-01T{17 + i // 2:02d}:{(i % 2) * 30:02d}:00+07:00",
           "cell_cluster": "ALL", "expected_orders": float(forecast[i])}
          for i in range(buckets)]
    return {"schema_version": "1.0.0", "driver_id": "d-1",
            "t_now": "2026-07-01T17:00:00+07:00",
            "buckets_remaining": buckets, "soc_pct": 80.0, "points_now": points,
            "demand_forecast": df, "policy_bundle_version": "sim-policy-v0",
            "view_version": "1.0.0", "source": "MOCK",
            "acceptance_rate_7d": 0.95, "completion_rate_7d": 0.95}


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(_BASE)


def _acts(report) -> list[str]:
    return [s["action"] for s in report["solution"]["schedule"]]


# ---------- F-098-01: Bellman phải nhìn TỔNG giá trị, không phải reward tức thời ----------

def test_online_negative_net_but_bonus_crossing_is_chosen(policy):
    """Tài xế 45 điểm, thiếu 15 điểm tới tier 60 (+30.000đ); cash 4.327đ/km làm net mỗi
    cuốc âm ~6đ. Tổng value ONLINE ≈ −13đ + 30.000đ ⇒ solver PHẢI chọn ONLINE.
    Trước fix: trả ['SWAP'], payout 0 — bỏ 30.000đ để né lỗ 13đ.

    ⚠ **ĐÍNH CHÍNH probe của debate review**: bản gốc F-098-01 dựng kịch bản với
    `bucket_min` mặc định 30′. Ở đó `cap_trips = bucket_min / service_min_per_trip
    = 30/25 = 1,2` ⇒ `exp_trips = 1,08` ⇒ `add_pts = 11 < points_band_size = 15` ⇒ band
    điểm KHÔNG THỂ tiến, nên ONLINE thật sự không vượt mốc và `['SWAP']` là ĐÚNG. Probe
    đó không dựng được lỗi. Nhưng defect vẫn THẬT và **chạm được ở đúng cấu hình sim**:
    `configs/pilot_dongda.yaml:361` đặt `bucket_min: 60` ⇒ cap 2,4 cuốc ⇒ add_pts = 22 ≥ 15
    ⇒ vượt band. Dùng 60′ ở đây chính là dùng cấu hình sim thật."""
    rep = solve(_spi(1, 45, [3.0]), policy,
                {"cash_cost_vnd_per_km": 4327.0, "avg_dist_km": 3.0, "bucket_min": 60})
    assert _acts(rep) == ["ONLINE"], _acts(rep)
    assert rep["solution"]["expected_payout"] > 0


def test_gate_change_is_bit_identical_at_zero_cost(policy):
    """Cổng an toàn của fix F-098-01: ở chi phí 0 (**đúng mặc định của
    `configs/pilot_dongda.yaml:274`**), điều kiện mới `exp_trips > 0` TƯƠNG ĐƯƠNG điều kiện
    cũ `online_net > 0` — vì `online_net = exp_trips × (ppo − 0)` và `ppo > 0` luôn đúng.
    Test này khoá tính tương đương đó bằng hành vi: nhiều kịch bản, chi phí 0, lịch phải
    giống hệt bản không truyền chi phí."""
    for buckets, points, fc in ((6, 140, None), (4, 0, [0.0, 3.0, 0.0, 3.0]),
                                (2, 55, [3.0, 3.0]), (1, 45, [3.0])):
        f = fc or [3.0] * buckets
        a = solve(_spi(buckets, points, f), policy, None)
        b = solve(_spi(buckets, points, f), policy, {"cash_cost_vnd_per_km": 0.0})
        assert _acts(a) == _acts(b), (buckets, points, _acts(a), _acts(b))
        assert a["solution"]["expected_payout"] == b["solution"]["expected_payout"]


def test_bucket30_no_band_crossing_is_not_a_bug(policy):
    """Đối chứng cho đính chính trên: ở `bucket_min=30`, trần công suất khiến một bucket
    KHÔNG thể tiến band ⇒ ONLINE lỗ thuần và `SWAP` là quyết định ĐÚNG. Test này tồn tại
    để không ai "sửa" nốt trường hợp này rồi làm solver chạy khi thật sự lỗ."""
    rep = solve(_spi(1, 45, [3.0]), policy,
                {"cash_cost_vnd_per_km": 4327.0, "avg_dist_km": 3.0, "bucket_min": 30})
    assert "ONLINE" not in _acts(rep), _acts(rep)


def test_online_still_skipped_when_demand_zero(policy):
    """Gate đúng là CÓ CẦU (khả thi): demand=0 ⇒ vẫn không ONLINE — giữ ngữ nghĩa gốc
    trước B2 (`online_pay > 0` chỉ chặn demand=0 vì pay=0 ⇔ trips=0)."""
    rep = solve(_spi(2, 45, [0.0, 0.0]), policy,
                {"cash_cost_vnd_per_km": 0.0, "avg_dist_km": 3.0})
    assert "ONLINE" not in _acts(rep), _acts(rep)


def test_truly_prohibitive_cost_still_kills_online(policy):
    """Khi lỗ vận hành VƯỢT mọi bonus với được (cash cực đoan 50.000đ/km — lỗ ~137.000đ/
    cuốc, tier cao nhất chỉ +170.000đ cho cả ngày), DP phải tự kết luận không ONLINE.
    Đây là phiên bản ĐÚNG của `test_prohibitive_cost_kills_online` cũ: cùng ý định,
    nhưng kịch bản không còn nằm trong vùng mà bỏ ONLINE là bỏ bonus lời."""
    rep = solve(_spi(6, 0, [3.0] * 6), policy,
                {"cash_cost_vnd_per_km": 50000.0, "avg_dist_km": 3.0})
    assert "ONLINE" not in _acts(rep), _acts(rep)


# ---------- F-098-02: policy ngoài thời hạn không được cấp giá trị ACTIVE ----------

def _bundle_2030() -> PolicyBundle:
    return PolicyBundle.from_record({
        **_BASE, "version": "policy-2030",
        "effective_from": "2030-01-01T00:00:00+07:00",
        "effective_to": "2030-12-31T23:59:59+07:00",
        "costs": {"swap_fee_vnd": 9000,
                  "cash_cost_vnd_per_km_by_track": {"platform": 250}},
    })


@pytest.mark.parametrize("as_of", ["2029-04-01T09:00:00+07:00",     # TRƯỚC hiệu lực
                                   "2031-06-15T09:00:00+07:00"])    # SAU hiệu lực
def test_resolver_rejects_policy_outside_validity(as_of):
    """`is_valid_at` trả False ⇒ mọi số hạng phải là UNKNOWN + reason nói rõ ngoài hạn —
    KHÔNG được ACTIVE (dùng giá của chính sách chưa/hết hiệu lực), cũng KHÔNG được
    OFF_BY_POLICY (cấm gộp UNKNOWN vào OFF — bài học hidden-fallback B3)."""
    b = _bundle_2030()
    assert b.is_valid_at(as_of) is False
    r = resolve_cost_params(b, as_of)
    for name, term in r.items():
        assert term["state"] == "UNKNOWN", (name, term)
        assert term["value"] == 0.0, (name, term)
        assert "hiệu lực" in term["reason"], (name, term)


def test_resolver_unknown_validity_stays_usable():
    """`is_valid_at` trả None (nguồn không ghi hạn) ⇒ KHÔNG chặn — "không biết hạn" khác
    "ngoài hạn"; chặn cả None là hidden fallback chiều ngược lại."""
    rec = {**_BASE, "effective_from": None,
           "costs": {"swap_fee_vnd": 9000,
                     "cash_cost_vnd_per_km_by_track": {"platform": 250}}}
    b = PolicyBundle.from_record(rec)
    assert b.is_valid_at("2029-04-01") is None
    r = resolve_cost_params(b, "2029-04-01T09:00:00+07:00")
    assert r["battery"]["state"] == "ACTIVE"
    assert r["cash_per_km"]["state"] == "ACTIVE"


def test_resolver_inside_validity_unchanged():
    """Trong thời hạn ⇒ hành vi y hệt trước fix (ACTIVE với giá policy)."""
    r = resolve_cost_params(_bundle_2030(), "2030-06-01T09:00:00+07:00")
    assert r["battery"]["state"] == "ACTIVE" and r["battery"]["value"] == 9000.0
    assert r["cash_per_km"]["state"] == "ACTIVE" and r["cash_per_km"]["value"] == 250.0

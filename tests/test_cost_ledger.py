"""Sổ CHI PHÍ riêng (T-045b) + hạn hiệu lực policy (Cycle P/①) — mặc định KHÔNG đổi hành vi.

Nền: `research/economics/driver-cost-structure-2026.md`. Phát hiện §0: chi phí km đang được
tính MỘT NỬA hệ thống — tài xế *quyết định* như thể mỗi km tốn 3.000đ (disutility trong
`decide_accept`) nhưng sổ tiền mà advisor tối ưu *không trừ gì*. Cycle P tách bạch: disutility
giữ nguyên tên mới (`pickup_disutility_vnd_per_km`), tiền mặt thật vào `actor.cost_vnd`.

Ràng buộc: mặc định config = 0 ⇒ `cost_vnd` luôn 0 và MỌI hành vi/trace y hệt — chi phí pin là
biến theo cohort × thời điểm (miễn phí official tới 31/03/2029 cho Platform độc quyền), đặt số
khác 0 làm mặc định là bịa chính sách.
"""

from __future__ import annotations

import copy

import pytest

from gsm_core.policy import PolicyBundle as CorePolicy
from gsm_sim.config import Config
from gsm_sim.runner import run_once

SEED = 1000


@pytest.fixture(scope="module")
def base():
    return Config.load("configs/pilot_dongda.yaml")


def _run(base, **veh):
    c = Config(copy.deepcopy(base.data), base.root_dir)
    c.data.setdefault("vehicle", {}).update(veh)
    return run_once(c, SEED)


# ---------- mặc định 0: sổ trống, hành vi y hệt ----------

def test_default_cost_is_zero_and_km_is_counted(base):
    r = _run(base)
    assert all(a.cost_vnd == 0 for a in r.actors), "mặc định 0 mà sổ chi phí có số — bịa chi phí"
    moved = [a for a in r.actors if a.km_driven > 0]
    assert len(moved) > 50, "km_driven không được accrue — chốt chặn consume_soc không chạy"


def test_cost_fields_do_not_change_behavior(base):
    """Có khoá config (giá trị 0) vs KHÔNG có khoá ⇒ trace y hệt — mẫu test bit-identical
    đã dùng cho `drop_demand_alpha` và `positioning_overrides`."""
    c_absent = Config(copy.deepcopy(base.data), base.root_dir)
    (c_absent.data.get("vehicle") or {}).pop("swap_fee_vnd", None)
    (c_absent.data.get("vehicle") or {}).pop("cash_cost_vnd_per_km", None)
    ra, rb = run_once(c_absent, SEED), _run(base)
    assert {a.actor_id: a.payout_vnd for a in ra.actors} == \
           {a.actor_id: a.payout_vnd for a in rb.actors}
    assert len(ra.events) == len(rb.events)


# ---------- bật chi phí: sổ đúng, payout KHÔNG đổi ----------

def test_cost_reconciles_and_payout_untouched(base):
    """cost = km × cash + số_lần_đổi_pin × fee, và payout KHÔNG suy chuyển một đồng.

    Trừ chi phí vào payout là trộn `driver_payout` với `estimated_net` — vi phạm §5. Sổ riêng
    để UI/advisor tính net TƯỜNG MINH khi đủ known costs + definition version."""
    r0 = _run(base)
    r1 = _run(base, swap_fee_vnd=9000, cash_cost_vnd_per_km=150)
    pay0 = {a.actor_id: a.payout_vnd for a in r0.actors}
    swaps_by = {}
    for e in r1.events:
        if e.kind == "swap_done":
            swaps_by[e.actor_id] = swaps_by.get(e.actor_id, 0) + 1
    for a in r1.actors:
        expect = int(round(a.km_driven * 150)) + 9000 * swaps_by.get(a.actor_id, 0)
        assert a.cost_vnd == expect, (
            f"d-{a.actor_id}: cost {a.cost_vnd} ≠ {expect} "
            f"(km {a.km_driven:.1f}, swaps {swaps_by.get(a.actor_id, 0)}) — sổ không khớp")
        assert a.payout_vnd == pay0[a.actor_id], (
            f"d-{a.actor_id}: payout đổi khi bật chi phí — cost đang RÒ vào payout (vi phạm §5)")


# ---------- Cycle P/①: hạn hiệu lực policy ----------

def test_policy_validity_semantics():
    """`is_valid_at` phải phân biệt BA trạng thái: True / False / **None = không biết**.

    Gộp None vào True là hidden fallback — đúng lỗi `soc_pct=None ⇒ pin đầy` (UPDATE-079)."""
    rec = {"version": "v-test", "fare": {"base_vnd": 12500, "base_km": 2.0, "per_km_vnd": 4300},
           "driver_share": 0.8,
           "points": {"peak": 2, "normal": 1, "peak_hours": [7, 8], "window_hours": [7, 8, 9]},
           "day_bonus_tiers": [[60, 30000]], "thresholds": {}}
    p = CorePolicy.from_record(rec)
    assert p.is_valid_at("2026-07-01") is None, "nguồn không ghi hạn ⇒ phải là KHÔNG BIẾT"

    p2 = CorePolicy.from_record({**rec, "effective_from": "2026-01-01",
                                 "effective_to": "2026-06-30"})
    assert p2.is_valid_at("2026-03-15") is True
    assert p2.is_valid_at("2026-07-01") is False, "quá hạn mà vẫn valid — advisor trích dẫn policy chết"
    assert p2.is_valid_at("2025-12-31") is False, "chưa hiệu lực mà vẫn valid"
    assert p2.is_valid_at("2026-06-30") is True, "biên phải inclusive"

    p3 = CorePolicy.from_record({**rec, "effective_from": "2026-01-01"})
    assert p3.is_valid_at("2030-01-01") is True, "không có hạn trên ĐÃ BIẾT ⇒ còn hiệu lực"


def test_world_warns_when_policy_expired(base):
    """Config khai hạn đã QUA ⇒ World phải phát event `policy_outside_validity` — fail-loud.

    Đây là wire-site test (quy tắc T-046: kiểm caller TRUYỀN, không chỉ kiểm hàm)."""
    c = Config(copy.deepcopy(base.data), base.root_dir)
    c.data.setdefault("meta", {}).update({"policy_effective_from": "2025-01-01",
                                          "policy_effective_to": "2026-06-30"})
    r = run_once(c, SEED)
    warns = [e for e in r.events if e.kind == "policy_outside_validity"]
    assert warns, "policy hết hạn 30/06 mà sim 01/07 không cảnh báo — advisor dùng policy chết im lặng"
    # pilot mặc định KHÔNG khai hạn ⇒ không có cảnh báo (UNKNOWN ≠ False)
    r0 = _run(base)
    assert not [e for e in r0.events if e.kind == "policy_outside_validity"]

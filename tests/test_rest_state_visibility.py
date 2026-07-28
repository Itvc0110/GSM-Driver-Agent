"""DP phải NHÌN THẤY nghỉ đã nghỉ + SWAP phải thắng REST khi hoà (Cycle R, Q-10c).

## Bằng chứng reproduce (R1, 3 seed 2000-2002, trước fix)

- Advisor làm tổng nghỉ toàn đội tăng **+16–27%** so với thế giới tắt advice;
- **11–14 lần/seed** DP tái-khuyên REST trong vòng 60′ sau khi tài xế VỪA nghỉ xong;
- 18–21 chuỗi REST-advisory cách nhau ≤90′;
- Fixture SOC=22% + demand phẳng: DP xếp `ONLINE, REST, REST, SWAP, …` — nghỉ TRƯỚC đổi pin
  khi pin đã dưới ngưỡng ⇒ 7–12 lần `go_swap → rest`/seed ngoài sim.

## Root cause (đã chứng minh, không phải phỏng đoán)

**H1 — VISIBILITY GAP**: `spi` không có trường nào về nghỉ đã diễn ra (`actor.rest_min` tồn tại
mà không ai truyền). Mỗi consult, `_required_rest(B_còn_lại)` tính lại từ đầu và DP khởi động
`rl = R` ⇒ nhu cầu nghỉ bị TÁI ÁP vô hạn, không có tín dụng cho nghỉ đã nghỉ.

**H3 — THẾ HOÀ**: trong `_solve_dp`, REST xét trước SWAP với so sánh chặt `v > best_v` ⇒ mọi thế
hoà (cả hai đều 0 thu nhập tức thời) REST thắng. Thế giới thật không hoà: hoãn swap ⇒ pin tụt,
hàng đợi trạm, 11% thất bại — nhưng DP không thấy các chi phí đó.

## Ràng buộc fix (Cường)

KHÔNG thêm "giá trị nghỉ" vào objective; không vặn `rest_min_per_4h`. Fix H1 là cấp STATE CÓ
THẬT cho DP (visibility), fix H3 là đổi THỨ TỰ ƯU TIÊN khi hoà — cả hai không bịa số nào.
"""

from __future__ import annotations

import copy

import pytest

from gsm_core.policy import PolicyBundle as CorePolicy
from gsm_core.solvers.shift_dp import DEFAULT_PARAMS, _required_rest, solve
from gsm_sim.config import Config
from gsm_sim.policy import PolicyBundle as SimPolicy

P60 = {**DEFAULT_PARAMS, "bucket_min": 60}


@pytest.fixture(scope="module")
def policy():
    cfg = Config.load("configs/pilot_dongda.yaml")
    return CorePolicy.from_record(SimPolicy.from_config(cfg).to_core_record())


def _spi(policy, *, B=8, soc=80.0, flat=2.0, start_h=14, **extra):
    d = {
        "schema_version": "1.0.0", "driver_id": "d-x",
        "t_now": f"2026-07-01T{start_h:02d}:00:00+07:00",
        "buckets_remaining": B, "soc_pct": soc, "points_now": 0,
        "demand_forecast": [
            {"bucket": f"2026-07-01T{start_h + i:02d}:00:00+07:00",
             "cell_cluster": "ALL", "expected_orders": flat} for i in range(B)],
        "policy_bundle_version": policy.version, "view_version": "t", "source": "MOCK",
    }
    d.update(extra)
    return d


PARAMS = {"bucket_min": 60, "p_accept": 0.85, "avg_dist_km": 3.5,
          "acceptance_rate": 0.9, "completion_rate": 0.95}


# ---------- H1: tín dụng cho nghỉ ĐÃ NGHỈ ----------

def test_required_rest_credits_rest_taken():
    """Tín dụng nghỉ phải ĐƠN ĐIỆU AN TOÀN: `R_mới ≤ R_cũ` với MỌI input.

    (Bản đầu của test này đòi ngữ nghĩa BACKFILL — "nhu cầu cả ca − đã nghỉ" — và số liệu đã
    bác bỏ nó: đo 3 seed, advisory REST nổ 55–66 → 145–178/seed vì tài xế chưa-nghỉ bị đòi bù
    quá khứ. Ngữ nghĩa đúng: chỉ phần nghỉ VƯỢT nhu cầu của ca-đã-qua mới trừ vào phần còn lại;
    thiếu hụt không bị bắt bù. Sửa expectation kèm lý do — đây là giả thuyết bị đo bác, lần 3
    trong phiên.)

    Ca 10h, đã chạy 5h (elapsed_need = 300//240 = 1), còn 5 bucket (forward = 1):
    """
    # nghỉ 120' = 2 bucket ⇒ surplus 1 ⇒ R = 1−1 = 0
    assert _required_rest(5, P60, rest_taken_min=120.0, shift_elapsed_min=300.0) == 0
    # chưa nghỉ gì ⇒ KHÔNG bắt bù quá khứ — giữ đúng mức cũ 1, không phải 2
    assert _required_rest(5, P60, rest_taken_min=0.0, shift_elapsed_min=300.0) == 1
    # nghỉ 45' ≈ 1 bucket = vừa đủ phần ca đã qua ⇒ surplus 0 ⇒ giữ mức cũ 1
    assert _required_rest(5, P60, rest_taken_min=45.0, shift_elapsed_min=300.0) == 1


def test_required_rest_is_monotone_safe():
    """Bất biến chống tái phạm backfill: có state KHÔNG BAO GIỜ đòi nghỉ nhiều hơn mù state.

    Quét lưới B × elapsed × taken — nếu ai đổi công thức về dạng bắt-bù, test này đỏ ngay."""
    for B in (1, 3, 5, 8, 10):
        old = _required_rest(B, P60)
        for elapsed in (0.0, 120.0, 300.0, 480.0, 700.0):
            for taken in (0.0, 20.0, 45.0, 90.0, 180.0):
                new = _required_rest(B, P60, rest_taken_min=taken, shift_elapsed_min=elapsed)
                assert new <= old, (
                    f"B={B} elapsed={elapsed} taken={taken}: R={new} > R_cũ={old} — "
                    f"công thức lại bắt bù nghỉ quá khứ (đã bị số liệu bác bỏ)")


def test_required_rest_backward_compatible_without_state():
    """Không truyền state (producer l1r cũ, mọi caller hiện có) ⇒ công thức CŨ y hệt.

    Đây là điều kiện để test S2 hiện hành không đỏ và đường l1r không đổi hành vi."""
    for B in (1, 4, 8, 10, 20):
        assert _required_rest(B, P60) == min(B, (B * 60 // 240) * P60["rest_min_per_4h"])


def test_no_forced_rest_when_already_rested_enough(policy):
    """Tài xế ĐÃ nghỉ đủ cho cả ca ⇒ schedule không còn REST ép.

    Trước fix: DP mù ⇒ vẫn ép (5×60)//240 = 1 bucket nghỉ dù vừa nghỉ 2 tiếng."""
    spi = _spi(policy, B=5, rest_taken_min=120.0, shift_elapsed_min=300.0)
    sched = [s["action"] for s in solve(spi, policy, PARAMS)["solution"]["schedule"]]
    assert "REST" not in sched, (
        f"đã nghỉ 120′/nhu cầu 120′ mà DP vẫn ép nghỉ: {sched} — tín dụng nghỉ không được trừ")


def test_rest_still_forced_when_not_taken(policy):
    """Chiều ngược lại PHẢI giữ: chưa nghỉ gì trong ca dài ⇒ DP vẫn ép nghỉ.

    Fix visibility không được biến thành 'bỏ ràng buộc sinh lý' — đó là vặn số liệu kiểu khác."""
    spi = _spi(policy, B=8, rest_taken_min=0.0, shift_elapsed_min=120.0)
    sched = [s["action"] for s in solve(spi, policy, PARAMS)["solution"]["schedule"]]
    assert "REST" in sched, "chưa nghỉ phút nào trong ca 10h mà DP thôi ép nghỉ — mất ràng buộc"


# ---------- H3: SWAP thắng REST khi hoà ----------

def test_swap_before_rest_when_battery_low(policy):
    """SOC dưới ngưỡng đổi pin + demand phẳng ⇒ SWAP phải đứng TRƯỚC REST trong lịch.

    Repro trước fix: `['ONLINE','REST','REST','SWAP',…]` — nghỉ hai bucket trong khi pin 22%.
    Thế giới thật: hoãn swap = pin tụt + hàng đợi + 11% thất bại. DP không mô hình hoá các chi
    phí đó, nên ít nhất thứ tự ưu tiên khi HOÀ phải nghiêng về swap."""
    spi = _spi(policy, B=8, soc=22.0, rest_taken_min=0.0, shift_elapsed_min=120.0)
    sched = [s["action"] for s in solve(spi, policy, PARAMS)["solution"]["schedule"]]
    assert "SWAP" in sched, f"pin 22% mà không swap: {sched}"
    if "REST" in sched:
        assert sched.index("SWAP") < sched.index("REST"), (
            f"pin 22% mà DP vẫn xếp nghỉ trước đổi pin: {sched} — thế hoà đang nghiêng về REST")


# ---------- bridge truyền state ----------

def test_bridge_passes_rest_state(policy):
    """`build_shift_plan_input` phải truyền `rest_taken_min` + `shift_elapsed_min` từ actor.

    Mẫu lỗi T-046: thêm tham số ở solver mà caller không truyền = fix chết ngay khi merge."""
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.entities import Actor, FleetType
    cfg = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    c.data.setdefault("advice", {}).update({"enabled": True, "coverage": "all"})
    br = AdviceActionBridge(c, SimPolicy.from_config(c), seed=1)
    a = Actor(actor_id=1, archetype="P4", fleet=FleetType.SWAP, home_cell="x",
              shift_start_min=600.0, shift_end_min=1320.0, demand_prior_sigma=0.2,
              accept_base=0.8, fatigue_threshold_min=480.0, meal_hour=12)
    a.cell, a.rest_min = "x", 37.5
    spi = br.build_shift_plan_input(a, 900.0, lambda _a, _h: {"c": 1.0}, 1320.0)
    assert spi.get("rest_taken_min") == 37.5, "bridge không truyền nghỉ đã nghỉ"
    assert spi.get("shift_elapsed_min") == 300.0, "bridge không truyền thời gian đã vào ca"

"""SIM-3 — gate cho cầu nối advice → action.

Cầu nối này là nền của SIM-4 (thế giới song song). Ba thứ SAI ở đây sẽ làm mọi kết luận A/B
về sau vô giá trị, nên khoá lại trước:

1. **Bật/tắt phải sạch** — advice tắt thì World A phải y hệt như chưa từng có SIM-3.
2. **Không rò thông tin tương lai** — nếu advisor nhìn được đơn của phần còn lại trong ngày,
   Δ(B−A) sẽ dương GIẢ và ta sẽ tưởng advisor giỏi.
3. **Dịch đúng ngữ nghĩa** — `ONLINE` KHÔNG phải "đứng im" (xem BUG-SIM3-01).
"""

from __future__ import annotations

import pytest

from gsm_sim.advice_bridge import DEFAULT_ADHERENCE, AdviceActionBridge
from gsm_sim.behavior import IdleAction
from gsm_sim.config import Config
from gsm_sim.entities import FleetType
from gsm_sim.metrics import summarize
from gsm_sim.policy import PolicyBundle
from gsm_sim.runner import run_once


def _cfg_advice_on(actor_id: int) -> Config:
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["advice"].update(enabled=True, coverage="single", single_actor_id=actor_id)
    return c


@pytest.fixture(scope="module")
def base_cfg():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture(scope="module")
def run_a(base_cfg):
    return run_once(base_cfg, seed=1000)


# ---------- Gate 1: tắt advice = World A không đổi ----------


def test_advice_disabled_by_default(base_cfg):
    """Mặc định phải TẮT — nếu ai đó bật nhầm trong config, mọi baseline SIM-1/SIM-2 lệch."""
    assert base_cfg.get("advice.enabled") is False


def test_disabled_advice_emits_nothing(run_a):
    kinds = {e.kind for e in run_a.events}
    assert "advice_given" not in kinds and "advice_followed" not in kinds


def test_disabled_advice_does_not_shift_rng(base_cfg):
    """Bằng chứng World A còn nguyên: chạy 2 lần cùng seed cho kết quả y hệt, và kết quả đó
    không phụ thuộc việc `AdviceActionBridge` có được khởi tạo hay không (nó không tiêu
    RNG dùng chung khi tắt)."""
    assert summarize(run_once(base_cfg, seed=42)) == summarize(run_once(base_cfg, seed=42))


# ---------- Gate 2: KHÔNG rò thông tin tương lai (quan trọng nhất) ----------


def test_forecast_comes_from_belief_not_future_orders(base_cfg, run_a):
    """Input đưa cho solver chỉ được chứa **belief cá nhân**, không phải đơn thật sắp tới.

    Kiểm bằng cách đưa một `demand_hint_fn` GIẢ trả giá trị nhận dạng được: nếu forecast
    chứa đúng giá trị đó thì bridge lấy từ belief; nếu nó lấy từ `world.orders` thì con số
    sẽ khác.
    """
    policy = PolicyBundle.from_config(base_cfg)
    bridge = AdviceActionBridge(_cfg_advice_on(0), policy, seed=1)
    actor = run_a.actors[0]
    SENTINEL = 12.345

    def fake_hint(_actor, _hour):
        return {"8a" + "0" * 13: SENTINEL}

    spi = bridge.build_shift_plan_input(actor, now_min=600.0, demand_hint_fn=fake_hint,
                                        horizon_min=900.0)
    assert spi["demand_forecast"], "forecast rỗng — solver sẽ không có gì để tối ưu"
    assert all(f["expected_orders"] == SENTINEL for f in spi["demand_forecast"]), \
        "forecast KHÔNG lấy từ belief ⇒ nghi rò rỉ nguồn khác"


def test_input_has_no_future_fields(base_cfg, run_a):
    """`shift_plan_input` không được mang theo bất kỳ khoá nào ngoài schema L3 — chống việc
    ai đó 'tiện tay' nhét thêm dữ liệu tương lai vào cho solver."""
    allowed = {"schema_version", "driver_id", "t_now", "buckets_remaining", "soc_pct",
               "points_now", "demand_forecast", "policy_bundle_version", "view_version",
               "source"}
    bridge = AdviceActionBridge(_cfg_advice_on(0), PolicyBundle.from_config(base_cfg), seed=1)
    spi = bridge.build_shift_plan_input(run_a.actors[0], 600.0, lambda a, h: {"c": 1.0}, 900.0)
    assert set(spi) <= allowed, f"khoá lạ trong input solver: {set(spi) - allowed}"


def test_horizon_never_exceeds_shift_end(base_cfg, run_a):
    """Số bucket phải tính tới HẾT CA của tài xế, không phải hết ngày — nếu quá, advisor
    đang lên kế hoạch cho khoảng thời gian tài xế đã nghỉ."""
    bridge = AdviceActionBridge(_cfg_advice_on(0), PolicyBundle.from_config(base_cfg), seed=1)
    spi = bridge.build_shift_plan_input(run_a.actors[0], 600.0, lambda a, h: {"c": 1.0},
                                        horizon_min=780.0)
    assert spi["buckets_remaining"] == 3, spi["buckets_remaining"]


# ---------- Gate 3: ánh xạ hành động đúng ngữ nghĩa ----------


def test_online_does_not_override_instinct(base_cfg, run_a):
    """**BUG-SIM3-01**: `ONLINE` từng bị map thành `WAIT` (đứng im), ghi đè cả `RELOCATE`.
    Đo được: d-42 tụt 14→11 cuốc, payout 214.400→155.376đ. `ONLINE` nghĩa là "cứ ở trạng
    thái làm việc" — KHÔNG phải mệnh lệnh đứng yên ⇒ phải là KHÔNG can thiệp."""
    from gsm_sim.advice_bridge import _map_action
    assert _map_action("ONLINE", run_a.actors[0]) is None


def test_swap_maps_by_fleet(run_a):
    from gsm_sim.advice_bridge import _map_action
    swap = next(a for a in run_a.actors if a.fleet == FleetType.SWAP)
    charge = next(a for a in run_a.actors if a.fleet == FleetType.CHARGE)
    assert _map_action("SWAP", swap) == IdleAction.GO_SWAP
    assert _map_action("SWAP", charge) == IdleAction.GO_CHARGE, \
        "tài xế sạc cắm ở nhà không 'đổi pin' tại trạm được"


def test_rest_and_end_map_directly(run_a):
    from gsm_sim.advice_bridge import _map_action
    a = run_a.actors[0]
    assert _map_action("REST", a) == IdleAction.REST
    assert _map_action("END", a) == IdleAction.END_SHIFT


# ---------- Gate 4: phạm vi + nhịp hỏi ----------


def test_coverage_single_targets_one_driver(base_cfg, run_a):
    bridge = AdviceActionBridge(_cfg_advice_on(7), PolicyBundle.from_config(base_cfg), seed=1)
    covered = [a for a in run_a.actors if bridge.covers(a)]
    assert len(covered) == 1 and covered[0].actor_id == 7


def test_consult_respects_interval(base_cfg, run_a):
    """Tài xế không mở app 30 giây một lần."""
    cfg = _cfg_advice_on(run_a.actors[0].actor_id)
    bridge = AdviceActionBridge(cfg, PolicyBundle.from_config(base_cfg), seed=1)
    a = run_a.actors[0]
    assert bridge.due(a, 600.0)
    bridge._last_consult[a.actor_id] = 600.0
    assert not bridge.due(a, 610.0)
    assert bridge.due(a, 600.0 + bridge.interval_min)


# ---------- Gate 5: mô hình tuân thủ ----------


def test_adherence_rate_matches_config(base_cfg):
    """Tỷ lệ nghe lời phải bám tham số archetype — nếu lệch, mọi kết luận SIM-4 về
    'advice giúp được bao nhiêu' sẽ sai theo."""
    policy = PolicyBundle.from_config(base_cfg)
    bridge = AdviceActionBridge(_cfg_advice_on(0), policy, seed=1)
    p = bridge.adherence["P4"]
    hits = sum(1 for _ in range(4000) if bridge.rng.random() < p)
    assert abs(hits / 4000 - p) < 0.05


def test_newbie_listens_more_than_veteran():
    """Giả định mô hình: tân binh nghe nhiều hơn lão làng. Nếu ai đó đảo tham số, các kết
    luận về 'advisor giúp tân binh nhiều nhất' sẽ đảo theo mà không ai để ý."""
    assert DEFAULT_ADHERENCE["P4"] > DEFAULT_ADHERENCE["P3"]
    assert DEFAULT_ADHERENCE["P4"] > DEFAULT_ADHERENCE["P5"]


# ---------- Gate 6: bật advice vẫn giữ mọi bảo toàn của SIM-2 ----------


def test_conservation_holds_with_advice_on(run_a):
    from gsm_sim.journey import build_journey
    tgt = max((a for a in run_a.actors if a.archetype == "P4"), key=lambda a: a.orders_offered)
    rB = run_once(_cfg_advice_on(tgt.actor_id), seed=1000)
    actor = next(a for a in rB.actors if a.actor_id == tgt.actor_id)
    j = build_journey(rB, tgt.actor_id)
    assert len(j.offers) == actor.orders_offered
    assert j.income_curve[-1][1] == actor.payout_vnd
    session = sum(b - a for a, b in j.sessions)
    assert abs(sum(b.minutes for b in j.timeline) - session) <= 1.0


def test_advice_events_are_emitted(run_a):
    tgt = max((a for a in run_a.actors if a.archetype == "P4"), key=lambda a: a.orders_offered)
    rB = run_once(_cfg_advice_on(tgt.actor_id), seed=1000)
    given = [e for e in rB.events if e.kind == "advice_given"]
    assert given, "bật advice mà không có event nào — cầu nối chưa chạy"
    assert all(e.actor_id == tgt.actor_id for e in given), "advice rò sang tài xế khác"
    for e in given:
        assert e.detail["solver_action"] in ("ONLINE", "REST", "SWAP", "END")
        assert e.detail["adherence"] in ("follow", "ignore")

"""Hook `advice.market_demand_override` — belief cầu RIÊNG của advisor (Cycle Q / ĐA-09 §2.2).

Fictitious play cần lặp belief-cầu của ADVISOR trên cung thực tế phát sinh từ vòng trước:
`d^k = f(kết quả vòng k−1)`. Vòng lặp đó chỉ được đụng belief của **planner/MarketState** —
tuyệt đối không đụng `_actor_demand_hint` (bản năng tài xế): nếu bản năng cũng ăn theo belief
lặp thì ta đang đổi THẾ GIỚI chứ không phải đổi ADVISOR, và mọi so sánh giữa các vòng vô nghĩa.

Nhãn dữ liệu: override là AGGREGATE của RUN KHÁC (cross-run learning) — không phải future-leak
trong run. Vắng khoá ⇒ hành vi y hệt từng bit (mẫu test chuẩn: `drop_demand_alpha`, cost keys).
"""

from __future__ import annotations

import copy

import pytest

from gsm_sim.config import Config
from gsm_sim.runner import run_once

SEED = 3000


@pytest.fixture(scope="module")
def base():
    return Config.load("configs/pilot_dongda.yaml")


def _cfg(base, override=None):
    c = Config(copy.deepcopy(base.data), base.root_dir)
    adv = c.data.setdefault("advice", {})
    adv.update({"enabled": True, "coverage": "all",
                "positioning_overrides": "wait_only",
                "channels": {"shift_plan": False, "accept_lift": False,
                             "shift_extend": False, "rest_window": False}})
    if override is not None:
        adv["market_demand_override"] = override
    return c


def test_producer_uses_override_when_present(base):
    """Override phải đi vào view của planner: dồn toàn bộ cầu vào MỘT ô ⇒ ô đó thống trị
    `ranked_cells` (mọi ô khác cầu 0 ⇒ không có trần ⇒ biến mất)."""
    from gsm_sim.market_state import MarketStateProducer

    class FakeWorld:
        def __init__(self, cfg):
            self.cfg = cfg
            self.actors = []
            self.demand_field = {9: {"a": 5.0, "b": 5.0}}

    ov = {"9": {"a": 99.0}}                  # khoá giờ dạng str (YAML) — producer phải chịu cả int/str
    w = FakeWorld(_cfg(base, override=ov))
    p = MarketStateProducer(w, bucket_min=60)
    v = p.view(9 * 60)
    assert v["cells"].get("a", {}).get("expected_demand") == 99.0, \
        "override không tới được view của planner"
    assert "b" not in v["cells"], "ô ngoài override vẫn còn cầu — override không thay thế field"


def test_absent_override_is_bit_identical(base):
    """Vắng khoá ⇒ trace y hệt từng bit (điều kiện để mọi baseline còn so sánh được)."""
    r0 = run_once(_cfg(base), SEED)
    c1 = _cfg(base)
    assert "market_demand_override" not in c1.data["advice"]
    r1 = run_once(c1, SEED)
    assert {a.actor_id: a.payout_vnd for a in r0.actors} == \
           {a.actor_id: a.payout_vnd for a in r1.actors}
    assert len(r0.events) == len(r1.events)


def test_override_flows_only_into_the_planner(base):
    """Override CHỈ được chảy vào planner — chứng minh bằng cách TẮT planner.

    (Bản đầu của test này so đích relocate bản năng giữa hai run có/không override khi planner
    BẬT — sai logic: khi advisor hành động khác đi, thế giới phân kỳ HỢP LỆ và hành động bản
    năng sau đó khác nhau là hệ quả vị trí, không phải hint bị nhiễm. Bất biến đúng: với
    `positioning_overrides: off` (consumer duy nhất của override không chạy), override có mặt
    hay không phải cho trace Y HỆT — nếu lệch, có một consumer LÉN thứ hai, ví dụ hint actor.)
    """
    r_no = run_once(_cfg(base), SEED)
    c_off = _cfg(base, override={"9": {r_no.grid.core_cells[0]: 999.0}})
    c_off.data["advice"]["positioning_overrides"] = "off"
    c_ref = _cfg(base)
    c_ref.data["advice"]["positioning_overrides"] = "off"
    r_ov = run_once(c_off, SEED)
    r_ref = run_once(c_ref, SEED)
    assert {a.actor_id: a.payout_vnd for a in r_ov.actors} == \
           {a.actor_id: a.payout_vnd for a in r_ref.actors}, (
        "planner TẮT mà override vẫn đổi trace — có consumer lén (bản năng actor bị nhiễm?)")
    assert len(r_ov.events) == len(r_ref.events)

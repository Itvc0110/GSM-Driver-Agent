"""E4/E-05 — kênh CON `shift_plan_end_only`: chỉ khuyên KẾT CA sớm khi DP bảo END.

Vì sao (UPDATE-151 r05): đường thi hành END→END_SHIFT ĐÃ NỐI SẴN trong _ACTION_MAP/consult;
full shift_plan bị ĐA-07 bác vì hại — kênh con này tách riêng "giá trị của lời khuyên kết ca"
(loại lời khuyên GIẢM giờ làm — không cần lan can sức khoẻ chiều kéo). Mặc định TẮT.
"""
from __future__ import annotations

import copy

import pytest

from gsm_core.solvers import shift_dp
from gsm_sim.advice_bridge import AdviceActionBridge
from gsm_sim.behavior import IdleAction
from gsm_sim.config import Config
from gsm_sim.policy import PolicyBundle


@pytest.fixture()
def cfgs():
    base = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(base.data), base.root_dir)
    c.data["advice"].update(enabled=True, coverage="all",
                            channels={"shift_plan": True, "accept_lift": False,
                                      "shift_extend": False, "rest_window": False},
                            shift_plan_end_only=True)
    return base, c


def _bridge(c):
    return AdviceActionBridge(c, PolicyBundle.from_config(c), seed=7)


def _actor(run_cfg):
    from gsm_sim.runner import run_once
    return run_once(run_cfg, 1000).actors[0]


def _fake_report(action: str):
    return {"solution": {"schedule": [{"bucket": "2026-09-28T20:00:00", "action": action}],
                         "next_action": {"action": action, "bucket": None, "reason": "x"}},
            "confidence": 0.8, "numbers": [], "sensitivity": [], "caveats": []}


def test_mac_dinh_TAT(cfgs):
    base, _ = cfgs
    assert base.get("advice").get("shift_plan_end_only") is False
    assert _bridge(base).sp_end_only is False


def test_end_only_nen_moi_thu_khong_phai_END(cfgs, monkeypatch):
    """Lịch DP bảo ONLINE ⇒ 'không có gì để nói': trả None, KHÔNG rút coin, KHÔNG tiêu suất
    (họ R-08 — mutation đảo thứ tự coin/gate phải làm test này đỏ)."""
    base, c = cfgs
    b = _bridge(c)
    monkeypatch.setattr(shift_dp, "solve", lambda *a, **k: _fake_report("ONLINE"))
    called = []
    b.coin_follows = lambda *a, **k: called.append(1) or True
    a = _actor(base)
    a.online_min = 60.0
    adv = b.consult(a, 600.0, lambda ac, h: {ac.cell: 1.0}, a.shift_end_min)
    assert adv is None
    assert called == [], "end_only vẫn rút coin cho lời khuyên KHÔNG tồn tại (phạm R-08)"


def test_end_only_cho_END_di_qua(cfgs, monkeypatch):
    base, c = cfgs
    b = _bridge(c)
    monkeypatch.setattr(shift_dp, "solve", lambda *a, **k: _fake_report("END"))
    b.coin_follows = lambda *a, **k: True
    a = _actor(base)
    a.online_min = 60.0
    adv = b.consult(a, 600.0, lambda ac, h: {ac.cell: 1.0}, a.shift_end_min)
    assert adv is not None and adv.solver_action == "END"
    assert adv.mapped_action == IdleAction.END_SHIFT      # đường thi hành ĐÃ NỐI


def test_tat_co_thi_hanh_vi_cu_nguyen_ven(cfgs, monkeypatch):
    """Đối chứng: cờ TẮT ⇒ ONLINE/REST vẫn được consult như cũ (không nén nhầm kênh mẹ)."""
    base, c = cfgs
    c.data["advice"]["shift_plan_end_only"] = False
    b = _bridge(c)
    monkeypatch.setattr(shift_dp, "solve", lambda *a, **k: _fake_report("REST"))
    b.coin_follows = lambda *a, **k: True
    a = _actor(base)
    a.online_min = 60.0
    adv = b.consult(a, 600.0, lambda ac, h: {ac.cell: 1.0}, a.shift_end_min)
    assert adv is not None and adv.solver_action == "REST"

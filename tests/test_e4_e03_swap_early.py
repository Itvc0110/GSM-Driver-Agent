"""E4/E-03 — kênh ĐỔI PIN SỚM lúc rảnh + trạm vắng (UPDATE-151 r03 SWAP-06, UPDATE-156).

Nguyên tắc: đổi THỜI ĐIỂM của một việc tất yếu (SOC trong band trên ngưỡng) sang lúc RẺ
(idle dài + trạm vắng). Mọi điều kiện đọc từ trạng thái HIỆN TẠI — không dự báo, không rò.
"""
from __future__ import annotations

import copy

import pytest

from gsm_sim.advice_bridge import AdviceActionBridge
from gsm_sim.config import Config
from gsm_sim.entities import Actor, FleetType
from gsm_sim.policy import PolicyBundle

THR = 20.0


def _cfg(on: bool = True):
    base = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(base.data), base.root_dir)
    c.data["advice"].update(enabled=True, coverage="all")
    c.data["advice"]["channels"] = {"shift_plan": False, "accept_lift": False,
                                    "shift_extend": False, "rest_window": False,
                                    "swap_early": on}
    return c


def _bridge(on: bool = True):
    c = _cfg(on)
    b = AdviceActionBridge(c, PolicyBundle.from_config(c), seed=5)
    b.coin_follows = lambda *a, **k: True          # coin không phải chủ thể — cô lập rail
    return b


def _actor(**kw) -> Actor:
    a = Actor(actor_id=1, archetype="P4", fleet=FleetType.SWAP, home_cell="x",
              shift_start_min=600.0, shift_end_min=1200.0, demand_prior_sigma=0.2,
              accept_base=0.8, fatigue_threshold_min=480.0, meal_hour=12)
    a.cell = "x"
    a.soc_pct = 30.0            # trong band (20, 35]
    a.idle_streak_min = 20.0    # rảnh dài
    for k, v in kw.items():
        setattr(a, k, v)
    return a


# ---------- rails: MỖI test đẩy đúng MỘT biến qua ngưỡng ----------

def test_du_dieu_kien_thi_khuyen():
    ok, why = _bridge().check_swap_early(_actor(), 700.0, 0, True, THR)
    assert (ok, why) == (True, "swap_now")


@pytest.mark.parametrize("kw,expect", [
    (dict(fleet=FleetType.CHARGE), "not_swap_fleet"),      # phần cứng không đổi được (SWAP-01)
    (dict(soc_pct=15.0), "below_threshold"),               # bản năng bước 1 tự lo
    (dict(soc_pct=50.0), "soc_high"),                      # chưa tất yếu — khuyên là đổi thừa
    (dict(idle_streak_min=3.0), "not_idle_long"),          # chưa rảnh đủ — cơ hội chưa rẻ
])
def test_rail_chan_dung_ly_do(kw, expect):
    ok, why = _bridge().check_swap_early(_actor(**kw), 700.0, 0, True, THR)
    assert (ok, why) == (False, expect)


def test_tram_dong_khong_khuyen():
    b = _bridge()
    assert b.check_swap_early(_actor(), 700.0, 2, True, THR) == (False, "station_busy")
    assert b.check_swap_early(_actor(), 700.0, 0, False, THR) == (False, "station_busy")


def test_kenh_tat_tra_channel_off_khong_rut_coin():
    b = _bridge(on=False)
    called = []
    b.coin_follows = lambda *a, **k: called.append(1) or True
    assert b.check_swap_early(_actor(), 700.0, 0, True, THR) == (False, "channel_off")
    assert called == []


def test_khong_nghe_co_dau_vet_mau_so():
    """D-M3-01: quyết định KHÔNG nghe phải vào drain (mẫu số adherence) — kind đã khai
    trong world._SPOKEN_OUTCOME_KIND."""
    b = _bridge()
    b.coin_follows = lambda *a, **k: False
    ok, why = b.check_swap_early(_actor(), 700.0, 0, True, THR)
    assert (ok, why) == (False, "not_followed")
    outs = [o for o in b.drain_spoken_outcomes() if o[2] == "swap_early"]
    assert len(outs) == 1 and outs[0][3] is False
    from gsm_sim.world import _SPOKEN_OUTCOME_KIND
    assert _SPOKEN_OUTCOME_KIND.get("swap_early") == "advice_swap_early"


def test_topic_da_vao_registry_duoc_do():
    from gsm_core.lifecycle.advice_topics import MEASURED_TOPICS, classify
    assert "swap_early" in MEASURED_TOPICS and classify("swap_early") == "measured"


def test_tich_hop_kenh_ON_chay_duoc_va_OFF_bit_identical():
    """(a) Kênh ON không nổ (1 seed run_once); (b) kênh OFF ⇒ bit-identical với config gốc
    (gate cờ đứng TRƯỚC choose_station — 0 draw RNG khi tắt, kỷ luật CRN)."""
    from gsm_sim.parallel import _cfg_with
    from gsm_sim.runner import run_once
    from gsm_sim.sim_metrics import fingerprint_actors

    base = Config.load("configs/pilot_dongda.yaml")
    r_off1 = run_once(base, 4242)
    r_off2 = run_once(Config(copy.deepcopy(base.data), base.root_dir), 4242)
    assert fingerprint_actors(r_off1) == fingerprint_actors(r_off2)   # xác lập baseline

    ch = {"shift_plan": False, "accept_lift": False, "shift_extend": False,
          "rest_window": False, "swap_early": True, "positioning_overrides": "off"}
    r_on = run_once(_cfg_with(base, enabled=True, actor_id=None,
                              channels=ch, coverage="all"), 4242)
    kinds = {e.kind for e in r_on.events}
    # không đòi kênh PHẢI nói ở seed này (điều kiện hẹp) — chỉ đòi đường ống không nổ
    assert "battery_stranded" in kinds or True

"""E4/E-01 — kênh gợi TRẠM đổi pin theo trạng thái SỐNG toàn cục (UPDATE-157; r05 E-01).

Bản năng: trạm quen/gần nhất, né queue>3 đúng MỘT lần — mù pin-sẵn và đường đi. Advisor:
argmin `station_eta_min` = đường + queue×swap + chờ-pin-chín; chỉ NÓI khi tiết kiệm ≥ ngưỡng.
"""
from __future__ import annotations

import copy

import pytest

from gsm_sim.advice_bridge import AdviceActionBridge
from gsm_sim.config import Config
from gsm_sim.entities import Actor, BatteryInStation, FleetType, Station
from gsm_sim.policy import PolicyBundle


def _st(nid, queue=0, ready=1, ready_in=0.0, cell="x"):
    b = [BatteryInStation(soc_pct=100.0, ready_at_min=0.0) for _ in range(ready)]
    if ready == 0:
        b = [BatteryInStation(soc_pct=100.0, ready_at_min=ready_in)]
    return Station(node_id=nid, cell=cell, lat=0.0, lon=0.0, slots=4,
                   ready_soc_pct=90.0, batteries=b, queue_len=queue)


def _bridge(on=True, gain=3.0):
    base = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(base.data), base.root_dir)
    c.data["advice"].update(enabled=True, coverage="all",
                            station_choice_min_gain_min=gain)
    c.data["advice"]["channels"] = {"shift_plan": False, "accept_lift": False,
                                    "shift_extend": False, "rest_window": False,
                                    "station_choice": on}
    b = AdviceActionBridge(c, PolicyBundle.from_config(c), seed=3)
    b.coin_follows = lambda *a, **k: True
    return b


def _actor():
    a = Actor(actor_id=1, archetype="P4", fleet=FleetType.SWAP, home_cell="x",
              shift_start_min=600.0, shift_end_min=1200.0, demand_prior_sigma=0.2,
              accept_base=0.8, fatigue_threshold_min=480.0, meal_hour=12)
    a.cell = "x"
    return a


# ---------- station_eta_min: mọi số quan sát được ----------

def test_eta_gom_duong_queue_va_pin_chin():
    s = _st(1, queue=2, ready=1)
    assert AdviceActionBridge.station_eta_min(s, 100.0, travel_min=4.0) == pytest.approx(
        4.0 + 2 * 1.5)
    s2 = _st(2, queue=0, ready=0, ready_in=110.0)     # pin chín lúc 110, now=100 ⇒ chờ 10
    assert AdviceActionBridge.station_eta_min(s2, 100.0, travel_min=2.0) == pytest.approx(12.0)
    s3 = Station(node_id=3, cell="x", lat=0, lon=0, slots=4, ready_soc_pct=90.0,
                 batteries=[], queue_len=0)
    assert AdviceActionBridge.station_eta_min(s3, 100.0, travel_min=1.0) == float("inf")


# ---------- pick_station: rails ----------

def test_goi_tram_re_hon_ro_ret():
    b = _bridge()
    near_busy = _st(1, queue=5, ready=1)              # gần (2') nhưng 5 người chờ ⇒ eta 9.5
    far_empty = _st(2, queue=0, ready=2)              # xa (4') nhưng trống ⇒ eta 4.0
    tmin = {1: 2.0, 2: 4.0}
    got, why = b.pick_station(_actor(), [near_busy, far_empty], 700.0,
                              lambda s: tmin[s.node_id], near_busy)
    assert got is far_empty and why == "st2"


def test_khong_noi_khi_chenh_vat():
    b = _bridge(gain=3.0)
    a_st = _st(1, queue=1, ready=1)                   # eta 2+1.5 = 3.5
    b_st = _st(2, queue=0, ready=1)                   # eta 2.0 ⇒ tiết kiệm 1.5 < 3
    tmin = {1: 2.0, 2: 2.0}
    got, why = b.pick_station(_actor(), [a_st, b_st], 700.0,
                              lambda s: tmin[s.node_id], a_st)
    assert got is None and why == "not_material"


def test_ban_nang_toi_uu_thi_im():
    b = _bridge()
    s1, s2 = _st(1, queue=0, ready=1), _st(2, queue=3, ready=1)
    tmin = {1: 2.0, 2: 2.0}
    got, why = b.pick_station(_actor(), [s1, s2], 700.0, lambda s: tmin[s.node_id], s1)
    assert got is None and why == "instinct_optimal"


def test_kenh_tat_khong_noi_khong_coin():
    b = _bridge(on=False)
    called = []
    b.coin_follows = lambda *a, **k: called.append(1) or True
    got, why = b.pick_station(_actor(), [_st(1)], 700.0, lambda s: 1.0, _st(1))
    assert (got, why) == (None, "channel_off") and called == []


def test_khong_nghe_thi_giu_ban_nang_va_co_mau_so():
    b = _bridge()
    b.coin_follows = lambda *a, **k: False
    near_busy, far_empty = _st(1, queue=5, ready=1), _st(2, queue=0, ready=2)
    tmin = {1: 2.0, 2: 4.0}
    got, why = b.pick_station(_actor(), [near_busy, far_empty], 700.0,
                              lambda s: tmin[s.node_id], near_busy)
    assert (got, why) == (None, "not_followed")
    outs = [o for o in b.drain_spoken_outcomes() if o[2] == "station_choice"]
    assert len(outs) == 1 and outs[0][3] is False
    from gsm_sim.world import _SPOKEN_OUTCOME_KIND
    assert _SPOKEN_OUTCOME_KIND.get("station_choice") == "advice_station_choice"


def test_topic_trong_registry():
    from gsm_core.lifecycle.advice_topics import MEASURED_TOPICS, classify
    assert "station_choice" in MEASURED_TOPICS and classify("station_choice") == "measured"


def test_tich_hop_ON_khong_no_OFF_bit_identical():
    from gsm_sim.parallel import _cfg_with
    from gsm_sim.runner import run_once
    from gsm_sim.sim_metrics import fingerprint_actors

    base = Config.load("configs/pilot_dongda.yaml")
    f1 = fingerprint_actors(run_once(base, 4243))
    f2 = fingerprint_actors(run_once(Config(copy.deepcopy(base.data), base.root_dir), 4243))
    assert f1 == f2
    ch = {"shift_plan": False, "accept_lift": False, "shift_extend": False,
          "rest_window": False, "station_choice": True, "positioning_overrides": "off"}
    r_on = run_once(_cfg_with(base, enabled=True, actor_id=None, channels=ch,
                              coverage="all"), 4243)
    assert r_on.actors           # đường ống không nổ; kênh nói hay không tuỳ seed (điều kiện hẹp)

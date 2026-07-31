"""E10 wiring — cổng đo lường + producer rẽ nguồn cầu (spec e10-advisor-noisy §2, §5.5; T1, T8–T11).

T1: wrapper verdict của script PHẢI nối tới cổng thống kê D-M3-10 thật. Bẫy nó canh
(BOOTSTRAP §5#4): adapter quên truyền `by_channel_archetype` ⇒ cổng im lặng VĨNH VIỄN
và mọi arm E10 "sạch" một cách giả tạo. Chứng minh đỏ được: ngắt tạm việc truyền
`by_channel_archetype` trong `arm_verdict` ⇒ test này đỏ (đã làm 2026-07-31, xem UPDATE).

T8–T11: `market_demand_source` — fail-loud config, oracle path nguyên trạng từng bit,
poison-đúng-ref (arm realized không bao giờ trả `world.demand_field`), fingerprint exact-repeat.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from gsm_sim.config import Config
from gsm_sim.entities import Actor, ActorState, FleetType
from gsm_sim.market_state import MarketStateProducer
from gsm_sim.world import Event

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("measure_e10", ROOT / "scripts" / "measure_e10.py")
me10 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(me10)


def _audit(decided: int, followed: int, arche: str = "P4") -> dict:
    """Audit tối thiểu đúng dạng `adherence_audit` trả về cho MỘT seed."""
    return {
        "by_channel": {"positioning": {
            "decided": decided, "followed": followed,
            "event_decided": decided, "event_followed": followed}},
        "by_channel_archetype": {f"positioning|{arche}": {
            "decided": decided, "followed": followed}},
        "flags": [],
    }


NOMINAL = {"P4": 0.75}


def test_t1_wrapper_treo_khi_lech_010_o_n500():
    # lệch +0,10 trên n=500: z = 0,10·500 / sqrt(500·0,75·0,25) ≈ 5,16 > 4 ⇒ TREO
    audits = [_audit(100, int(100 * 0.85)) for _ in range(5)]
    out = me10.arm_verdict(audits, NOMINAL)
    assert out["verdict"].startswith("TREO"), out
    assert any("positioning" in f for f in out["flags_per_seed"]), out


def test_t1_wrapper_ok_khi_lech_001_o_n500():
    # lệch +0,01 trên n=500: z ≈ 0,52 — nhiễu lấy mẫu thuần, cổng không được bắn
    audits = [_audit(100, 76) for _ in range(5)]
    out = me10.arm_verdict(audits, NOMINAL)
    assert out["verdict"] == "OK", out


def test_t1_wrapper_dung_nominal_cua_run_khong_hardcode():
    # adherence đo 0,75 = DEFAULT của P4 — nhưng run này override nominal P4=0,50.
    # Nếu wrapper rơi về DEFAULT cứng (lỗi UPDATE-107 đã sửa ở run_ladder) thì "sạch" giả.
    audits = [_audit(100, 75) for _ in range(5)]
    out = me10.arm_verdict(audits, {"P4": 0.50})
    assert out["verdict"].startswith("TREO"), out


def test_pooled_z_khop_cong_thuc_poisson_binomial():
    from gsm_sim.sim_metrics import poisson_binomial_z
    audits = [_audit(100, 85) for _ in range(5)]
    z, mu, fol, n = me10.pooled_channel_z(audits, NOMINAL, "positioning")
    assert (fol, n) == (425, 500)
    assert abs(z - poisson_binomial_z(425, [0.75] * 500)) < 1e-12
    assert abs(mu - 0.75) < 1e-12


# ====================== T8–T11: producer rẽ nguồn cầu ========================

def _actor(actor_id: int, cell: str) -> Actor:
    a = Actor(actor_id=actor_id, archetype="P1", fleet=FleetType.SWAP, home_cell=cell,
              shift_start_min=300.0, shift_end_min=1400.0, demand_prior_sigma=0.2,
              accept_base=0.9, fatigue_threshold_min=480.0, meal_hour=12)
    a.cell, a.state, a.enroute_cell = cell, ActorState.IDLE, None
    return a


def _cfg_e10(**advice_over) -> Config:
    c = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(c.data), c.root_dir)
    c.data.setdefault("advice", {}).update(advice_over)
    return c


class _LogWorld:
    """Stub đủ mặt cho producer: cfg + actors + demand_field + events + log recorder."""

    def __init__(self, cfg, actors, demand_field, events=None):
        self.cfg, self.actors, self.demand_field = cfg, actors, demand_field
        self.events = events if events is not None else []
        self.logged: list[tuple] = []

    def log(self, actor_id, kind, cell="", **detail):
        self.logged.append((actor_id, kind, cell, detail))


def _pickups(ts_cells) -> list[Event]:
    return [Event(t_min=float(t), actor_id=1, kind="pickup", cell=c) for t, c in ts_cells]


# --- T8: fail-loud config ----------------------------------------------------

def test_t8_source_la_gia_tri_la_valueerror():
    w = _LogWorld(_cfg_e10(market_demand_source="banana"), [_actor(1, "A")], {9: {"A": 1.0}})
    with pytest.raises(ValueError):
        MarketStateProducer(w, bucket_min=60)


def test_t8_realized_tron_voi_override_valueerror():
    # hai belief THAY THẾ nhau (tiền lệ comment `_demand`) — trộn là vô nghĩa, phải nổ
    w = _LogWorld(_cfg_e10(market_demand_source="realized",
                           market_demand_override={9: {"A": 5.0}}),
                  [_actor(1, "A")], {9: {"A": 1.0}})
    with pytest.raises(ValueError):
        MarketStateProducer(w, bucket_min=60)


def test_t8_realized_bucket_khac_60_valueerror():
    # phạm vi đo pin b=60 (spec §3.2) — re-derive cho b khác rồi mới được gỡ
    w = _LogWorld(_cfg_e10(market_demand_source="realized"), [_actor(1, "A")], {9: {"A": 1.0}})
    with pytest.raises(ValueError):
        MarketStateProducer(w, bucket_min=30)


# --- T9: oracle mode nguyên trạng ---------------------------------------------

def test_t9_oracle_default_khong_estimator_khong_event_moi():
    w = _LogWorld(_cfg_e10(), [_actor(1, "A")], {9: {"A": 12.0, "B": 6.0}})
    p = MarketStateProducer(w, bucket_min=60)
    assert p.demand_source is None
    v = p.view(9 * 60)
    assert v["cells"]["A"]["expected_demand"] == 12.0        # đường oracle cũ, giá trị y hệt
    assert w.logged == []                            # neutrality: KHÔNG event kind mới


def test_t9_stub_khong_co_cfg_van_dung_duong_cu():
    class _Bare:                                     # test cũ dựng producer kiểu này
        pass
    w = _Bare()
    w.actors, w.demand_field = [_actor(1, "A")], {9: {"A": 3.0}}
    p = MarketStateProducer(w, bucket_min=60)
    assert p.demand_source is None
    assert p.view(9 * 60)["cells"]["A"]["expected_demand"] == 3.0


# --- T9b/T10 (unit): realized mode — estimator điều khiển, log đúng nhịp -------

def test_t10_realized_khong_bao_gio_tra_oracle_field():
    # demand_field CÓ MẶT và đầy số — nếu realized còn đường nào rơi về nó, test đỏ
    events = _pickups([(310, "A"), (320, "A"), (370, "B")])
    w = _LogWorld(_cfg_e10(market_demand_source="realized",
                           realized_demand={"window_buckets": 3, "min_pickups": 1}),
                  [_actor(1, "A")], {h: {"A": 99.0, "B": 99.0} for h in range(24)}, events)
    p = MarketStateProducer(w, bucket_min=60)
    assert p.demand_source is not None
    v = p.view(7 * 60)                               # cửa sổ [5,7): A=2/2, B=1/2
    assert v["cells"]["A"]["expected_demand"] == 1.0 and v["cells"]["B"]["expected_demand"] == 0.5
    assert all(c["expected_demand"] != 99.0 for c in v["cells"].values())


def test_t10_cold_ra_view_rong_va_log_demand_est_cold():
    w = _LogWorld(_cfg_e10(market_demand_source="realized",
                           realized_demand={"window_buckets": 3, "min_pickups": 5}),
                  [_actor(1, "A")], {h: {"A": 99.0} for h in range(24)},
                  _pickups([(310, "A")]))            # total=1 < min_n=5 ⇒ COLD
    p = MarketStateProducer(w, bucket_min=60)
    v = p.view(7 * 60)
    assert v["ranked_cells"] == []                   # advisor im lặng — planner tự skip
    kinds = [k for (_, k, _, _) in w.logged]
    assert kinds == ["demand_est_cold"]
    assert w.logged[0][3]["idx"] == 7


def test_t9c_log_mot_lan_moi_bucket_cache_miss():
    events = _pickups([(310, "A"), (320, "A")])
    w = _LogWorld(_cfg_e10(market_demand_source="realized",
                           realized_demand={"window_buckets": 3, "min_pickups": 1}),
                  [_actor(1, "A")], {}, events)
    p = MarketStateProducer(w, bucket_min=60)
    p.view(7 * 60); p.view(7 * 60 + 30); p.view(7 * 60 + 58)   # cùng bucket — cache
    assert len(w.logged) == 1
    p.view(8 * 60)                                              # bucket mới — log lần 2
    assert len(w.logged) == 2
    assert [k for (_, k, _, _) in w.logged] == ["demand_est", "demand_est"]
    det = w.logged[0][3]
    assert det["idx"] == 7 and det["n_cells"] == 1 and "cells" in det


# --- T10 (integration): poison đúng ref, trọn ngày arm realized ----------------

def test_t10_integration_tron_ngay_realized_demand_khong_identity_voi_oracle():
    from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with
    from gsm_sim.runner import run_once

    calls: list[tuple[int, bool, bool]] = []
    orig = MarketStateProducer._demand

    def spy(self, hour, idx):
        out = orig(self, hour, idx)
        oracle = self.world.demand_field.get(hour, {}) or {}
        calls.append((idx, out is oracle, bool(out) and dict(out) == dict(oracle)))
        return out

    base = _cfg_e10(market_demand_source="realized",
                    realized_demand={"window_buckets": 3, "min_pickups": 5})
    cfg = _cfg_with(base, enabled=True, actor_id=None,
                    channels=CHANNEL_LADDER["positioning"], coverage="all")
    MarketStateProducer._demand = spy
    try:
        run_once(cfg, 5100)
    finally:
        MarketStateProducer._demand = orig
    assert calls, "planner không gọi _demand — wiring chết"
    assert not any(ident for (_, ident, _) in calls), "identity với world.demand_field — oracle leak"
    assert not any(eq for (_, _, eq) in calls), "giá trị y hệt oracle ở bucket không cold — khả nghi leak"

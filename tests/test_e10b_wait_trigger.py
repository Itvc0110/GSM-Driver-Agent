"""E10b — trigger positioning theo THỜI GIAN CHỜ + zone-veto (spec e10-advisor-noisy §4, T12–T18).

Bẫy trung tâm (phản biện chứng minh từ `capacity_alloc.py`): cost lệch target = `pen + 10`,
KHÔNG phải LARGE ⇒ Hungarian STAGGER ứng viên sang bất kỳ zone còn slot — kể cả ô đang đứng.
Test "pref ≠ own" bị CẤM làm bằng chứng veto (nó xanh khi lỗi còn sống) — T14 dựng đúng ca
stagger-về-own-cell và chứng minh đỏ trên thế giới CHƯA veto.
"""
from __future__ import annotations

import copy

import pytest

from gsm_core.features.allocation import derive_allocation_input
from gsm_core.solvers import capacity_alloc
from gsm_sim.config import Config
from gsm_sim.entities import Actor, ActorState, FleetType
from gsm_sim.market_state import count_idle_wait, wait_fired_cells
from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with
from gsm_sim.runner import run_once
from gsm_sim.sim_metrics import adherence_audit


def _actor(actor_id: int, cell: str, state=ActorState.IDLE, streak: float = 0.0) -> Actor:
    a = Actor(actor_id=actor_id, archetype="P1", fleet=FleetType.SWAP, home_cell=cell,
              shift_start_min=300.0, shift_end_min=1400.0, demand_prior_sigma=0.2,
              accept_base=0.9, fatigue_threshold_min=480.0, meal_hour=12)
    a.cell, a.state, a.enroute_cell = cell, state, None
    a.idle_streak_min = streak
    return a


def _wait_cfg(**advice_over) -> Config:
    c = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(c.data), c.root_dir)
    c.data.setdefault("advice", {}).update(advice_over)
    return _cfg_with(c, enabled=True, actor_id=None,
                     channels=CHANNEL_LADDER["positioning"], coverage="all")


# --- T12: count_idle_wait ------------------------------------------------------

def test_t12_loc_idle_gop_o_median_noi_suy():
    acts = [_actor(1, "A", streak=10), _actor(2, "A", streak=30),
            _actor(3, "A", streak=20, state=ActorState.ON_TRIP),   # không IDLE — loại
            _actor(4, "B", streak=50)]
    stats = count_idle_wait(acts)
    assert stats["A"] == (2, 20.0)          # median chẵn = nội suy (10+30)/2
    assert stats["B"] == (1, 50.0)
    assert count_idle_wait([]) == {}


def test_t12_median_le():
    acts = [_actor(i, "A", streak=s) for i, s in enumerate((4, 8, 100))]
    assert count_idle_wait(acts)["A"] == (3, 8.0)


# --- T13: luật fire + cổng cá nhân ---------------------------------------------

def test_t13_fire_can_ca_median_lon_hon_T_va_du_n():
    stats = {"A": (2, 31.0), "B": (2, 30.0), "C": (1, 99.0)}
    fired = wait_fired_cells(stats, 30.0, 2)
    assert fired == {"A"}                   # B: median == T không fire (strict >); C: n=1 < n_min


def test_t13_dau_ca_moi_streak_0_khong_o_nao_fire():
    stats = count_idle_wait([_actor(i, "A") for i in range(5)])   # streak đều 0
    assert wait_fired_cells(stats, 30.0, 2) == set()
    assert wait_fired_cells(stats, 0.0, 1) == set()               # median 0 > 0 vẫn False


# --- T14: stagger-về-own-cell — đỏ bắt buộc trước khi vá ------------------------

def _solve(cands, zones):
    ai = derive_allocation_input("2026-07-31T09:00:00+07:00", cands, [], zones, bucket_min=60)
    return capacity_alloc.solve(ai)["solution"]


def test_t14_hungarian_stagger_ve_own_cell_khi_CHUA_veto():
    """Thế giới CHƯA veto (own cell còn slot trong zones): ứng viên bị pref-đầy STAGGER về
    đúng ô mình đang đứng — coin sẽ rút, decided phình, rồi pop im lặng. Đây là bằng chứng
    ĐỎ rằng `pref ≠ own` không đủ; luật veto tồn tại vì ca này."""
    cands = [
        {"driver_id": "d-1", "advice_kind": "standby_zone", "target": "PREF", "priority_soc": 10.0},
        {"driver_id": "d-2", "advice_kind": "standby_zone", "target": "PREF", "priority_soc": 90.0},
    ]
    zones = [{"zone": "PREF", "capacity": 1}, {"zone": "OWN", "capacity": 1}]   # OWN = ô đang đứng
    sol = _solve(cands, zones)
    tgt = {al["driver_id"]: al["assigned_target"] for al in sol["allocations"]}
    assert tgt["d-1"] == "PREF"             # SOC penalty thấp thắng pref
    assert tgt["d-2"] == "OWN"              # kẻ thua bị stagger VỀ CHỖ ĐỨNG — lỗ có thật


def test_t14_zone_veto_dong_ca_stagger():
    """Cùng ca trên nhưng zones dựng từ `ranked_eff` (ô fired bị loại): không ai có thể bị
    gán vào ô fired nữa — kẻ thua pref rơi vào unassigned thay vì churn về chỗ cũ."""
    fired = {"OWN"}
    cands = [
        {"driver_id": "d-1", "advice_kind": "standby_zone", "target": "PREF", "priority_soc": 10.0},
        {"driver_id": "d-2", "advice_kind": "standby_zone", "target": "PREF", "priority_soc": 90.0},
    ]
    zones = [{"zone": z, "capacity": 1} for z in ("PREF", "OWN") if z not in fired]
    sol = _solve(cands, zones)
    assert all(al["assigned_target"] not in fired for al in sol["allocations"])
    assert len(sol["allocations"]) == 1 and len(sol["unassigned"]) == 1


# --- T15: ranked_eff rỗng ⇒ không ứng viên, không coin, decided không tăng ------

class _Universe:
    """fired 'chứa mọi ô' — ép ranked_eff rỗng cả ngày."""

    def __contains__(self, item):
        return True


def test_t15_moi_o_deu_fire_planner_im_lang_khong_dot_coin(monkeypatch):
    import gsm_sim.market_state as ms
    monkeypatch.setattr(ms, "wait_fired_cells", lambda stats, t, n: _Universe())
    r = run_once(_wait_cfg(positioning_trigger="wait"), 5100)
    assert not [e for e in r.events if e.kind == "standby_alloc"], "planner phải im tuyệt đối"
    pos = adherence_audit(r)["by_channel"].get("positioning", {})
    assert int(pos.get("decided") or 0) == 0    # không rút coin, không đếm decided


# --- T16: cadence check sống ở nhánh wait ---------------------------------------

def test_t16_bat_count_positioning_in_budget_chan_duoc_nhanh_wait():
    # T=0/n_min=1 để trigger fire được trong dynamics thật; ngân sách 0 ⇒ cadence chặn HẾT
    loose = {"positioning_trigger": "wait",
             "positioning_wait": {"threshold_min": 0.0, "min_idle": 1}}
    r_free = run_once(_wait_cfg(**loose), 5101)
    d_free = int(adherence_audit(r_free)["by_channel"].get("positioning", {}).get("decided") or 0)
    assert d_free > 0, "trigger nới hết cỡ mà vẫn 0 decided — nhánh wait chết, T16 vô nghĩa"

    r_block = run_once(_wait_cfg(**loose,
                                 cadence={"count_positioning_in_budget": True,
                                          "max_proactive_per_shift": 0}), 5101)
    d_block = int(adherence_audit(r_block)["by_channel"].get("positioning", {}).get("decided") or 0)
    assert d_block == 0, "ngân sách 0 mà vẫn nói — cadence check rơi khỏi nhánh wait (bẫy sketch cũ)"


# --- T17: cold hai tầng — estimator câm ⇒ planner ngủ ---------------------------

def test_t17_realized_cold_ca_ngay_wait_mode_khong_alloc():
    cfg = _wait_cfg(positioning_trigger="wait",
                    market_demand_source="realized",
                    realized_demand={"window_buckets": 3, "min_pickups": 10 ** 9})
    r = run_once(cfg, 5100)
    assert not [e for e in r.events if e.kind == "standby_alloc"]
    colds = [e for e in r.events if e.kind == "demand_est_cold"]
    assert colds, "cold cả ngày thì phải có log demand_est_cold (advisor im CÓ GHI)"


# --- T18: probe wait_stats — log-only, neutral tuyệt đối ------------------------

def test_t18_probe_fingerprint_identical_va_khong_lot_lifecycle():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "probe_mod", Path(__file__).resolve().parents[1] / "scripts" / "probe_adherence_truth.py")
    probe_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe_mod)

    base = Config.load("configs/pilot_dongda.yaml")
    off = _cfg_with(base, enabled=False, actor_id=None, channels=None)
    on = Config(copy.deepcopy(off.data), off.root_dir)
    on.data["probe"] = {"wait_stats": True}

    r_off, r_on = run_once(off, 5100), run_once(on, 5100)
    assert probe_mod.fingerprint_actors(r_off) == probe_mod.fingerprint_actors(r_on), \
        "probe log-only mà làm trôi thế giới — 0 RNG/0 state bị vi phạm"
    probes = [e for e in r_on.events if e.kind == "probe_wait_stats"]
    assert probes and all("cells" in e.detail for e in probes)
    assert not [e for e in r_off.events if e.kind == "probe_wait_stats"]

    # event probe không được lọt vào lifecycle projections (không decision_id ⇒ skip)
    from gsm_core.lifecycle import projections as p
    lc = p.sim_events_to_lifecycle(r_on.events)
    assert not [e for e in lc if e.get("kind") == "probe_wait_stats"]
    assert adherence_audit(r_on)["by_channel"] == adherence_audit(r_off)["by_channel"]

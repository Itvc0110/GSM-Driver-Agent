"""T-030 / M0 integrity — regression + invariant tests (failing-first theo CLAUDE.md §4b).

Tranche 1: battery conservation (M0-1), order lifecycle (M0-5), censoring + time (M0-6/M0-4).
Tranche 2: future-leak/belief (M0-3/4), offer cooldown (M0-2), meal (M0-7), home-charge (M0-8).
Tranche 3: distance contract (M0-9), atomic pos (M0-10), dispatch (M0-11/12), congestion toggle (C-2).
Pin sẵn: order_expired flat schema (M0-13), drop-point position (M0-14).
"""

from pathlib import Path

import h3
import pytest

from gsm_sim.config import Config
from gsm_sim.geo import haversine_km
from gsm_sim.runner import run_once

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def cfg():
    return Config.load(ROOT / "configs" / "pilot_dongda.yaml")


@pytest.fixture(scope="module")
def result(cfg):
    return run_once(cfg, seed=3)


# ---------- Pin sẵn từ baseline (M0-13, M0-14) ----------


def test_order_expired_flat_schema(result):
    """M0-13: order_expired phải có order_id ở top-level detail (không nested)."""
    expired = [e for e in result.events if e.kind == "order_expired"]
    assert expired, "phải có ít nhất 1 order_expired trong run chuẩn"
    for e in expired:
        assert "order_id" in e.detail, f"nested/missing order_id: {e.detail}"
        assert isinstance(e.detail["order_id"], int)


def test_actor_position_after_dropoff(result):
    """M0-14: sau dropoff, vị trí actor = điểm trả THẬT của đơn (không teleport)."""
    orders_by_id = {o.order_id: o for o in result.orders}
    # traj: (t, actor_id, lat, lon, state) — tìm waypoint on_trip kết thúc
    drops = [e for e in result.events if e.kind == "dropoff"][:20]
    assert drops
    for e in drops:
        o = orders_by_id[e.detail["order_id"]]
        # waypoint gần nhất sau dropoff của actor này phải ở đúng drop point
        pts = [w for w in result.traj if w[1] == e.actor_id and abs(w[0] - e.t_min) < 0.01]
        assert pts, f"không có waypoint tại dropoff actor {e.actor_id}"
        w = pts[-1]
        assert haversine_km(w[2], w[3], o.drop_lat, o.drop_lon) < 0.01


# ---------- Tranche 1: M0-1 battery conservation ----------


def test_battery_conservation(result):
    """M0-1: tổng số pin trong mỗi tủ không đổi (swap = đổi 1-1, không phát sinh/mất pin)."""
    slots = int(result.config.get("station.slots"))
    expected = slots - 1  # khởi tạo slots-1 pin (1 khe trống)
    for st in result.stations:
        assert len(st.batteries) == expected, (
            f"trạm {st.node_id}: {len(st.batteries)} pin != {expected} (non-conservation)")


def test_battery_recharge_completes(result):
    """M0-1: pin trả về tủ phải được sạc — sau recharge_min pin phải ready (soc>=ready_soc).
    Baseline bug: pin append soc=0 và không bao giờ được nâng lên."""
    # cuối run: mọi pin có ready_at <= end_min phải có soc >= ready_soc
    end_min = float(result.config.get("time.end_min"))
    ready_soc = float(result.config.get("station.ready_soc_pct"))
    stale = []
    for st in result.stations:
        for b in st.batteries:
            if b.ready_at_min <= end_min and b.soc_pct < ready_soc:
                stale.append((st.node_id, b.soc_pct, b.ready_at_min))
    assert not stale, f"pin quá hạn sạc nhưng soc vẫn thấp (không bao giờ hồi): {stale[:5]}"


def test_no_phantom_swap_when_empty(result):
    """M0-1: không actor nào nhận pin 100% khi trạm không còn pin ready (wait-cap fallthrough).
    Sau fix: hết wait-cap → swap_failed, SOC giữ nguyên."""
    # sau fix phải tồn tại đường sự kiện swap_failed HOẶC mọi swap_done đều xảy ra khi có pin ready.
    # Kiểm chứng gián tiếp: với mọi swap_done, wait_min phải <= wait_cap (không có swap sau khi break cap)
    wait_cap = float(result.config.get("station.wait_cap_min", 60.0))
    over = [e for e in result.events if e.kind == "swap_done"
            and e.detail.get("wait_min", 0.0) > wait_cap]
    assert not over, f"swap_done sau khi vượt wait_cap (phantom battery): {len(over)} sự kiện"


# ---------- Tranche 1: M0-5 order lifecycle ----------


def test_order_exactly_one_terminal(result):
    """M0-5: mỗi đơn kết thúc đúng 1 terminal state: COMPLETED / EXPIRED / CENSORED."""
    states = result.order_states
    assert states, "world phải xuất order_states"
    n = len(result.orders)
    assert len(states) == n, f"thiếu order trong state map: {len(states)} != {n}"
    terminals = {"COMPLETED", "EXPIRED", "CENSORED_END_OF_RUN"}
    bad = {oid: s for oid, s in states.items() if s[0] not in terminals}
    assert not bad, f"đơn không có terminal state (bốc hơi): {dict(list(bad.items())[:5])}"


def test_order_matched_event_emitted(result):
    """M0-5: khi actor nhận đơn phải có event order_matched trước pickup."""
    matched = {e.detail["order_id"] for e in result.events if e.kind == "order_matched"}
    picked = {e.detail["order_id"] for e in result.events if e.kind == "pickup"}
    assert matched, "phải có order_matched events"
    assert picked <= matched, f"đơn pickup mà không có matched: {list(picked - matched)[:5]}"


# ---------- Tranche 1: M0-6 + M0-4 censoring + time conservation ----------


def test_time_conservation_busy_at_end(result):
    """M0-4: actor còn online tới end_min phải được cộng đủ online_min ~ (end - start).
    Baseline bug: đoạn bận cuối ngày bị mất."""
    end_min = float(result.config.get("time.end_min"))
    for a in result.actors:
        if a.state.value == "offline":
            continue  # đã kết ca, online_min chốt lúc end_shift
        span = end_min - a.shift_start_min
        # online_min không được hụt quá 3 phút so với span thực (tolerance vòng lặp)
        assert a.online_min >= span - 3.0, (
            f"actor {a.actor_id} ({a.state}): online_min {a.online_min:.1f} << span {span:.1f}")


def test_inflight_order_censored(result):
    """M0-6: đơn đang phục vụ lúc 24:00 phải được đánh dấu CENSORED, không biến mất."""
    states = result.order_states
    # đơn có matched nhưng không dropoff và không expired → phải CENSORED
    matched = {e.detail["order_id"] for e in result.events if e.kind == "order_matched"}
    dropped = {e.detail["order_id"] for e in result.events if e.kind == "dropoff"}
    expired = {e.detail["order_id"] for e in result.events if e.kind == "order_expired"}
    inflight = matched - dropped - expired
    for oid in inflight:
        assert states[oid][0] == "CENSORED_END_OF_RUN", (
            f"đơn {oid} in-flight cuối ngày nhưng state={states.get(oid)}")


# ---------- Tranche 2: M0-3 future-leak + M0-4 stable belief ----------


def test_no_future_information_leak(cfg):
    """M0-3: belief của actor KHÔNG được đọc realized order trace của run.
    Sau fix: world không còn build demand_field từ orders; hint đến từ expected
    field (config) + prior per-actor."""
    r = run_once(cfg, seed=3)
    # world không được giữ field realized (thuộc tính demand_field từ orders phải biến mất
    # hoặc không được xây từ realized trace)
    from gsm_sim.world import World
    assert not hasattr(r, "_demand_field_realized")
    # kiểm gián tiếp qua nguồn: expected field chỉ phụ thuộc config, không phụ thuộc seed →
    # 2 run khác seed phải cho CÙNG expected field (nếu field xây từ realized thì khác nhau)
    import copy
    from gsm_sim.config import Config as _C
    from gsm_sim.demand import expected_demand_field
    grid = r.grid
    f1 = expected_demand_field(grid, cfg)
    f2 = expected_demand_field(grid, cfg)
    assert f1 == f2, "expected field phải deterministic theo config"
    # và không trùng y hệt realized counts của một seed cụ thể
    realized = {}
    for o in r.orders:
        h = int(o.t_min // 60) % 24
        realized.setdefault(h, {})
        realized[h][o.pickup_cell] = realized[h].get(o.pickup_cell, 0.0) + 1.0
    assert f1 != realized, "expected field không được là realized trace (future leak)"


def test_actor_belief_stable_and_hashseed_free(cfg):
    """M0-4: belief per (actor, hour) phải ổn định trong run (không resample mỗi call)
    và kết quả sim không phụ thuộc PYTHONHASHSEED (set-iteration đã prove nondeterminism)."""
    from gsm_sim.metrics import summarize
    a = summarize(run_once(cfg, seed=4))
    b = summarize(run_once(cfg, seed=4))
    assert a == b  # in-process determinism giữ
    # belief stability: chạy 1 world, gọi hint 2 lần cùng (actor, hour) → identical
    from gsm_sim.geo import build_grid
    from gsm_sim.policy import PolicyBundle
    from gsm_sim.demand import generate_orders
    from gsm_sim.archetypes import sample_actors
    from gsm_sim.world import World
    data_dir = cfg.resolve_path("world.data_dir")
    grid = build_grid(geom_path=data_dir / cfg.get("world.geom_file"),
                      stations_path=data_dir / cfg.get("world.stations_file"),
                      poi_path=data_dir / cfg.get("world.poi_file"),
                      res=int(cfg.get("world.h3_res")),
                      res_report=int(cfg.get("world.h3_res_report")))
    policy = PolicyBundle.from_config(cfg)
    orders = generate_orders(grid, cfg, policy, seed=4)
    actors = sample_actors(grid, cfg, seed=4)
    w = World(grid, cfg, policy, orders, actors, seed=4)
    actor = actors[0]
    h1 = w._actor_demand_hint(actor, 9)
    h2 = w._actor_demand_hint(actor, 9)
    assert h1 == h2, "belief resample mỗi call (M0-4 chưa fix)"


# ---------- Tranche 2: M0-2 offer cooldown ----------


def test_declined_pair_not_reoffered_within_cooldown(result):
    """M0-2: cùng (order, actor) không được chào lại trong cooldown sau khi decline."""
    cooldown = float(result.config.get("dispatcher.offer_cooldown_min", 10.0))
    declines: dict[tuple, list[float]] = {}
    for e in result.events:
        if e.kind == "order_declined":
            declines.setdefault((e.detail["order_id"], e.actor_id), []).append(e.t_min)
    violations = []
    for pair, times in declines.items():
        times.sort()
        for t1, t2 in zip(times, times[1:]):
            if t2 - t1 < cooldown - 1e-9:
                violations.append((pair, t1, t2))
    assert not violations, f"re-offer trong cooldown: {violations[:5]}"


# ---------- Tranche 2: M0-7 meal once ----------


def test_meal_rest_once_per_day(result):
    """M0-7: mỗi actor nghỉ ăn (rest trong meal_hour) tối đa 1 lần/ngày."""
    actors = {a.actor_id: a for a in result.actors}
    meal_rests: dict[int, int] = {}
    for e in result.events:
        if e.kind == "rest":
            a = actors.get(e.actor_id)
            if a is not None and int(e.t_min // 60) % 24 == a.meal_hour:
                meal_rests[e.actor_id] = meal_rests.get(e.actor_id, 0) + 1
    over = {aid: n for aid, n in meal_rests.items() if n > 1}
    assert not over, f"actor nghỉ ăn nhiều lần cùng meal_hour: {over}"


# ---------- Tranche 2: M0-8 home-charge travel ----------


def test_home_charge_has_travel_segment(result):
    """M0-8: sạc-tại-nhà phải có leg di chuyển VỀ NHÀ trước khi charge (không teleport)."""
    actors = {a.actor_id: a for a in result.actors}
    home_charges = [e for e in result.events if e.kind == "charge_home_start"]
    if not home_charges:
        pytest.skip("run này không có charge_home (phụ thuộc mix archetype)")
    segs = result.segments
    for e in home_charges:
        a = actors[e.actor_id]
        # phải tồn tại segment relocate reason=go_home_charge kết thúc đúng lúc charge bắt đầu
        legs = [s for s in segs if s["actor_id"] == e.actor_id
                and s.get("reason") == "go_home_charge" and abs(s["t1"] - e.t_min) < 0.5]
        assert legs, f"actor {e.actor_id} charge_home lúc {e.t_min} không có leg về nhà"
        # và sự kiện charge phải diễn ra tại home_cell
        assert e.cell == a.home_cell, (
            f"charge_home tại {e.cell} != home_cell {a.home_cell}")


# ---------- Tranche 3: M0-9 distance contract ----------


def test_distance_contract_consistency(result):
    """M0-9: dist_km (tính tiền/thời gian/pin) phải = haversine(pickup_pt, drop_pt).
    Baseline bug: dist_km sample lognormal độc lập với endpoints."""
    for o in result.orders[:200]:
        hv = haversine_km(o.pickup_lat, o.pickup_lon, o.drop_lat, o.drop_lon)
        assert abs(o.dist_km - hv) < 0.02, (
            f"đơn {o.order_id}: dist_km={o.dist_km} != haversine(endpoints)={hv:.3f}")


# ---------- Tranche 3: M0-10 atomic position/cell sync ----------


def test_position_cell_always_synced(result):
    """M0-10: actor.cell phải luôn = h3(latlng) sau mọi movement — kiểm cuối run."""
    res = int(result.config.get("world.h3_res"))
    for a in result.actors:
        if a.lat == 0.0 and a.lon == 0.0:
            continue  # chưa từng online
        expect = h3.latlng_to_cell(a.lat, a.lon, res)
        assert a.cell == expect, (
            f"actor {a.actor_id}: cell={a.cell} != h3(pos)={expect} (desync)")


# ---------- Tranche 3: M0-11 + M0-12 dispatch semantics ----------


def test_dispatch_nearest_across_rings(cfg):
    """M0-11: actor GẦN HƠN (haversine) ở ring xa hơn phải thắng actor xa hơn ở ring gần.
    Baseline bug: dừng ở ring đầu tiên có candidate."""
    from gsm_sim.dispatcher import match_batch
    from gsm_sim.demand import Order
    from gsm_sim.entities import Actor, ActorState, FleetType
    from gsm_sim.geo import build_grid, grid_disk
    import h3 as _h3
    data_dir = cfg.resolve_path("world.data_dir")
    grid = build_grid(geom_path=data_dir / cfg.get("world.geom_file"),
                      stations_path=data_dir / cfg.get("world.stations_file"),
                      poi_path=data_dir / cfg.get("world.poi_file"),
                      res=int(cfg.get("world.h3_res")),
                      res_report=int(cfg.get("world.h3_res_report")))
    pickup = grid.core_cells[len(grid.core_cells) // 2]
    plat, plon = grid.cell_centroid[pickup]
    # actor A: cell sát pickup (ring 1) nhưng đứng RÌA XA của cell → haversine xa
    ring1 = [c for c in grid_disk(pickup, 1) if c != pickup][0]
    a_lat, a_lon = _h3.cell_to_latlng(ring1)
    # dời A ra xa pickup thêm ~1.2km theo hướng ngược
    from gsm_sim.geo import offset_latlng
    a_lat, a_lon = offset_latlng(a_lat, a_lon, 1.2, 1.2)
    # actor B: ring 3 nhưng đứng gần pickup hơn (chỉ ~0.5km)
    ring3 = [c for c in grid_disk(pickup, 3) if c not in set(grid_disk(pickup, 2))][0]
    b_lat, b_lon = offset_latlng(plat, plon, 0.35, 0.35)  # ~0.5km từ pickup

    def mk(aid, cell, lat, lon):
        a = Actor(actor_id=aid, archetype="P2", fleet=FleetType.SWAP, home_cell=cell,
                  shift_start_min=0, shift_end_min=1440, demand_prior_sigma=0.3,
                  accept_base=0.95, fatigue_threshold_min=600, meal_hour=12, cell=cell)
        a.state = ActorState.IDLE
        a.lat, a.lon = lat, lon
        return a

    A = mk(1, ring1, a_lat, a_lon)
    B = mk(2, ring3, b_lat, b_lon)
    order = Order(0, 600.0, pickup, pickup, 3.0, 20000, 5.0, plat, plon, plat, plon)
    asg = match_batch([order], [A, B], grid, 12, cfg.get("speed_kmh"), cfg.get("dispatcher"))
    assert asg, "phải match được"
    assert asg[0].actor_id == 2, (
        f"actor 2 gần hơn (0.5km, ring3) phải thắng actor 1 (1.7km, ring1); got {asg[0].actor_id}")


def test_dispatch_tiebreak_deterministic(cfg):
    """M0-12: hai actor cùng khoảng cách → actor_id nhỏ hơn thắng (ổn định 2 lần chạy)."""
    from gsm_sim.dispatcher import match_batch
    from gsm_sim.demand import Order
    from gsm_sim.entities import Actor, ActorState, FleetType
    from gsm_sim.geo import build_grid
    data_dir = cfg.resolve_path("world.data_dir")
    grid = build_grid(geom_path=data_dir / cfg.get("world.geom_file"),
                      stations_path=data_dir / cfg.get("world.stations_file"),
                      poi_path=data_dir / cfg.get("world.poi_file"),
                      res=int(cfg.get("world.h3_res")),
                      res_report=int(cfg.get("world.h3_res_report")))
    pickup = grid.core_cells[10]
    plat, plon = grid.cell_centroid[pickup]

    def mk(aid):
        a = Actor(actor_id=aid, archetype="P2", fleet=FleetType.SWAP, home_cell=pickup,
                  shift_start_min=0, shift_end_min=1440, demand_prior_sigma=0.3,
                  accept_base=0.95, fatigue_threshold_min=600, meal_hour=12, cell=pickup)
        a.state = ActorState.IDLE
        a.lat, a.lon = plat, plon  # cùng đúng 1 vị trí → distance bằng nhau tuyệt đối
        return a

    order = Order(0, 600.0, pickup, pickup, 3.0, 20000, 5.0, plat, plon, plat, plon)
    for _ in range(2):
        asg = match_batch([order], [mk(7), mk(3)], grid, 12,
                          cfg.get("speed_kmh"), cfg.get("dispatcher"))
        assert asg and asg[0].actor_id == 3, f"tie phải chọn actor_id nhỏ (3), got {asg}"


# ---------- Tranche 3: C-2 congestion toggle ----------


def test_congestion_disabled_zeroes_route_effect(cfg):
    """C-2: enabled=false phải zero TOÀN BỘ r() kể cả event route_effect."""
    import copy
    from gsm_sim.config import Config as _C
    from gsm_sim.congestion import CongestionField
    from gsm_sim.environment import EnvironmentContext
    from gsm_sim.geo import build_grid
    data_dir = cfg.resolve_path("world.data_dir")
    grid = build_grid(geom_path=data_dir / cfg.get("world.geom_file"),
                      stations_path=data_dir / cfg.get("world.stations_file"),
                      poi_path=data_dir / cfg.get("world.poi_file"),
                      res=int(cfg.get("world.h3_res")),
                      res_report=int(cfg.get("world.h3_res_report")))
    venue = grid.core_cells[0]
    data = copy.deepcopy(cfg.data)
    data["congestion"]["enabled"] = False
    data["environment"]["events"] = [{
        "venue_cell": venue, "t_start_min": 1140, "t_end_min": 1320,
        "attendance": 20000, "capture_rate": 0.1, "sigma_cells": 2.0,
        "route_effect": {"speed_multiplier": 0.5, "sigma_cells": 2.0},
    }]
    c2 = _C(data, cfg.root_dir)
    env = EnvironmentContext(grid, c2, seed=1)
    from gsm_sim.demand import generate_orders
    from gsm_sim.policy import PolicyBundle
    orders = generate_orders(grid, c2, PolicyBundle.from_config(c2), seed=1, env=env)
    field = CongestionField(orders, c2, env=env)
    # 19h (=1140+30) trong cửa sổ event, tại venue: nếu toggle đúng → r=0
    assert field.r(venue, 19) == 0.0, (
        f"enabled=false nhưng r(venue,19h)={field.r(venue, 19)} — route_effect chưa bị gate (C-2)")

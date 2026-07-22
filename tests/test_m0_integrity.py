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

"""Behavior model B-arm (bản năng — không advice).

Nguồn: advisor-optimization-layer-a.md §1. Deterministic theo RNG stream truyền vào.
Cung cấp quyết định: accept đơn, chọn hành động khi idle, chọn trạm đổi pin.

Slice v0: xấp xỉ utility model — đủ để actor hành xử hợp lý (chạy peak, nghỉ trưa,
đi đổi pin khi SOC thấp, kết ca quanh giờ quen). Tinh chỉnh tham số ở calibration (T-021).
"""

from __future__ import annotations

import math
from enum import Enum

from .entities import Actor, ActorState, FleetType, Station
from .geo import Grid, cell_distance_km


class IdleAction(str, Enum):
    WAIT = "wait"
    RELOCATE = "relocate"
    GO_SWAP = "go_swap"
    GO_CHARGE = "go_charge"
    REST = "rest"
    END_SHIFT = "end_shift"


def _logistic(x: float) -> float:
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def accept_order(actor: Actor, gross_vnd: int, pickup_dist_km: float, forced: bool, rng) -> bool:
    """Quyết định nhận đơn. forced=True (auto-accept) → luôn nhận."""
    if forced:
        return True
    # utility: giá trị đơn trừ chi phí đến đón; scale để accept_base là điểm giữa
    net = gross_vnd - pickup_dist_km * 3000.0
    # dịch để p ~ accept_base khi net ~ 12k
    x = (net - 6000.0) / 8000.0 + math.log(actor.accept_base / (1 - actor.accept_base))
    return rng.random() < _logistic(x)


def soc_range_km(actor: Actor, cfg_vehicle: dict) -> float:
    if actor.fleet == FleetType.SWAP:
        return actor.soc_pct / max(1e-6, float(cfg_vehicle["swap_consume_pct_per_km"]))
    return actor.soc_pct / max(1e-6, float(cfg_vehicle["charge_consume_pct_per_km"]))


def choose_idle_action(
    actor: Actor,
    now_min: float,
    grid: Grid,
    cfg_vehicle: dict,
    hour: int,
    demand_hint: dict[str, float] | None,
    rng,
) -> tuple[IdleAction, str | None]:
    """Chọn hành động khi idle. Trả (action, target_cell nếu relocate).

    demand_hint: Ê kỳ vọng đơn theo cell (kinh nghiệm cá nhân) — None thì dùng đồng đều.
    """
    swap_threshold = float(cfg_vehicle["swap_soc_threshold_pct"])

    # 1. SOC thấp → đi đổi pin / sạc (ưu tiên cao nhất)
    if actor.soc_pct <= swap_threshold:
        return (IdleAction.GO_SWAP if actor.fleet == FleetType.SWAP else IdleAction.GO_CHARGE, None)

    # 2. Quá giờ kết ca quen → kết ca
    if now_min >= actor.shift_end_min:
        return (IdleAction.END_SHIFT, None)

    # 3. Giờ ăn quen + đã chạy đủ lâu → nghỉ (một lần quanh meal_hour)
    fatigue = actor.online_min / max(1.0, actor.fatigue_threshold_min)
    if hour == actor.meal_hour and fatigue > 0.35 and rng.random() < 0.5:
        return (IdleAction.REST, None)

    # 4. Mệt cao → nghỉ ngắn xác suất tăng theo fatigue
    if fatigue > 1.0 and rng.random() < 0.3:
        return (IdleAction.REST, None)

    # 5. Cân nhắc relocate sang cell lân cận có kỳ vọng đơn cao hơn rõ rệt
    if demand_hint is not None:
        here = demand_hint.get(actor.cell, 0.0)
        best_cell, best_val = actor.cell, here
        for nb in _neighbors(actor.cell, grid):
            v = demand_hint.get(nb, 0.0)
            # trừ chi phí di chuyển
            v_adj = v - 0.15 * cell_distance_km(grid, actor.cell, nb)
            if v_adj > best_val * 1.25:  # chỉ đi nếu hơn hẳn
                best_cell, best_val = nb, v_adj
        if best_cell != actor.cell and rng.random() < 0.5:
            return (IdleAction.RELOCATE, best_cell)

    return (IdleAction.WAIT, None)


def _neighbors(cell: str, grid: Grid) -> list[str]:
    from .geo import grid_disk

    return [c for c in grid_disk(cell, 1) if c != cell and grid.is_core(c)]


def choose_station(actor: Actor, grid: Grid, stations: list[Station], now_min: float, rng) -> Station | None:
    """Chọn trạm đổi pin: trạm quen p=0.7 (mock = gần nhà), else gần nhất theo cell distance.
    Nếu trạm gần nhất quá đông (queue>3) → chuyển sang trạm gần kế (1 lần)."""
    if not stations:
        return None
    ranked = sorted(stations, key=lambda s: cell_distance_km(grid, actor.cell, s.cell))
    nearest = ranked[0]
    if nearest.queue_len > 3 and len(ranked) > 1:
        return ranked[1]
    return nearest

"""Dispatcher batched-nearest trên dispatch tick (T1).

Nguồn: research/simulation/world-parameters.md §3 (baseline greedy nearest; Hungarian
để vòng sau). Gom đơn mở + tài xế idle trong tick, gán greedy theo ETA tăng dần.
Deterministic: sort ổn định theo (order_id) và (actor_id).
"""

from __future__ import annotations

from dataclasses import dataclass

from .entities import Actor, ActorState
from .geo import Grid, grid_disk, haversine_km


@dataclass
class Assignment:
    order_id: int
    actor_id: int
    pickup_dist_km: float
    eta_min: float


def _speed_kmh(hour: int, speed_cfg: dict) -> float:
    if hour in set(speed_cfg["peak_hours"]):
        return float(speed_cfg["peak"])
    if hour in set(speed_cfg["night_hours"]):
        return float(speed_cfg["night"])
    return float(speed_cfg["offpeak"])


def match_batch(
    open_orders: list,          # list[Order] còn mở
    idle_actors: list[Actor],
    grid: Grid,
    hour: int,
    speed_cfg: dict,
    disp_cfg: dict,
    speed_fn=None,              # (cell, hour) -> km/h hiệu dụng (mưa/tắc); None = base theo giờ
    detour: float = 1.0,        # hệ số đường vòng (A4) — fallback khi không có factor_fn
    factor_fn=None,             # SIM-XANH: (cell_from, cell_to) -> hệ số đường THẬT (OSRM)
) -> list[Assignment]:
    """Gán greedy per-order (order_id tăng dần): M0-11 quét MỘT LẦN toàn bộ candidate
    trong grid_disk(pickup, k_max) — H3 chỉ là shortlist; xếp hạng theo khoảng cách
    LIÊN TỤC actor→điểm đón (haversine). M0-12 tie-break deterministic (dist, actor_id).
    ETA đơn điệu theo distance nên actor gần nhất fail ETA ⇒ mọi actor khác cũng fail
    (không cần try-next). Mỗi actor nhận tối đa 1 đơn/tick."""
    k_max = int(disp_cfg["candidate_ring_k_max"])
    eta_max = float(disp_cfg["eta_max_min"])

    # index actor theo cell để tra nhanh (candidate retrieval theo H3 grid_disk)
    by_cell: dict[str, list[Actor]] = {}
    for a in idle_actors:
        by_cell.setdefault(a.cell, []).append(a)

    taken: set[int] = set()
    assignments: list[Assignment] = []

    for order in sorted(open_orders, key=lambda o: o.order_id):
        best: Actor | None = None
        best_key: tuple[float, int] = (float("inf"), -1)
        for cell in grid_disk(order.pickup_cell, k_max):
            for a in by_cell.get(cell, []):
                if a.actor_id in taken:
                    continue
                d = haversine_km(a.lat, a.lon, order.pickup_lat, order.pickup_lon)
                key = (d, a.actor_id)  # M0-12: cùng distance → actor_id nhỏ thắng
                if key < best_key:
                    best_key, best = key, a
        if best is None:
            continue
        best_dist = best_key[0]
        speed = speed_fn(order.pickup_cell, hour) if speed_fn is not None else _speed_kmh(hour, speed_cfg)
        # SIM-XANH: ETA theo hệ số đường của CẶP (actor → điểm đón) khi có matrix
        fac = factor_fn(best.cell, order.pickup_cell) if factor_fn is not None else detour
        eta = (best_dist * fac) / speed * 60.0
        if eta > eta_max:
            continue
        taken.add(best.actor_id)
        assignments.append(Assignment(order.order_id, best.actor_id, round(best_dist, 3), round(eta, 2)))

    return assignments  # đã theo order_id tăng dần (vòng lặp sorted)

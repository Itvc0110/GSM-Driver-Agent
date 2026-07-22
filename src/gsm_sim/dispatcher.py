"""Dispatcher batched-nearest trên dispatch tick (T1).

Nguồn: research/simulation/world-parameters.md §3 (baseline greedy nearest; Hungarian
để vòng sau). Gom đơn mở + tài xế idle trong tick, gán greedy theo ETA tăng dần.
Deterministic: sort ổn định theo (order_id) và (actor_id).
"""

from __future__ import annotations

from dataclasses import dataclass

from .entities import Actor, ActorState
from .geo import Grid, cell_distance_km, grid_disk, haversine_km


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
    detour: float = 1.0,        # hệ số đường vòng (A4)
) -> list[Assignment]:
    """Gán greedy: với mỗi đơn (theo order_id tăng dần), tìm actor idle gần nhất
    (khoảng cách LIÊN TỤC actor→điểm đón, haversine) trong grid_disk k (nới tới k_max, H3),
    thỏa ETA_max. Mỗi actor nhận tối đa 1 đơn/tick. speed_fn cho tốc độ theo cell đón."""
    k = int(disp_cfg["candidate_ring_k"])
    k_max = int(disp_cfg["candidate_ring_k_max"])
    eta_max = float(disp_cfg["eta_max_min"])

    # index actor theo cell để tra nhanh (candidate search vẫn theo H3 grid_disk)
    by_cell: dict[str, list[Actor]] = {}
    for a in idle_actors:
        by_cell.setdefault(a.cell, []).append(a)

    taken: set[int] = set()
    assignments: list[Assignment] = []

    for order in sorted(open_orders, key=lambda o: o.order_id):
        best: Actor | None = None
        best_dist = float("inf")
        ring = k
        while ring <= k_max and best is None:
            for cell in grid_disk(order.pickup_cell, ring):
                for a in by_cell.get(cell, []):
                    if a.actor_id in taken:
                        continue
                    # khoảng cách thực actor→điểm đón (toạ độ liên tục)
                    d = haversine_km(a.lat, a.lon, order.pickup_lat, order.pickup_lon)
                    if d < best_dist:
                        best_dist, best = d, a
            ring += 1
        if best is None:
            continue
        speed = speed_fn(order.pickup_cell, hour) if speed_fn is not None else _speed_kmh(hour, speed_cfg)
        eta = (best_dist * detour) / speed * 60.0  # phút (quãng đường thực × detour)
        if eta > eta_max:
            continue
        taken.add(best.actor_id)
        assignments.append(Assignment(order.order_id, best.actor_id, round(best_dist, 3), round(eta, 2)))

    # sort ổn định theo actor_id để xử lý deterministic
    assignments.sort(key=lambda x: x.order_id)
    return assignments

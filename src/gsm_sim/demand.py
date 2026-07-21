"""Demand generator — sinh exogenous trace (đơn hàng) deterministic theo seed.

Nguồn: specs/mock-order-distribution.md (hour-shape), advisor-optimization-layer-a §4
(harmonize: renormalize trong window, OD buffer ring). specs/simulation-pilot-world §1.

Trace ngoại sinh = danh sách Order (thời điểm, cell đón, cell trả, quãng đường, gross)
được sinh TRƯỚC khi chạy sim → dùng chung cho mọi arm (nền CRN).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .config import Config
from .geo import Grid, cell_distance_km, grid_disk
from .policy import PolicyBundle


@dataclass(frozen=True)
class Order:
    order_id: int
    t_min: float  # phút từ 00:00
    pickup_cell: str
    drop_cell: str
    dist_km: float
    gross_vnd: int


def _cell_weights(grid: Grid, cfg: Config) -> dict[str, float]:
    """Trọng số demand mỗi cell lõi: w = a·pop_proxy + b·poi_score, chuẩn hóa tổng=1.

    pop_proxy: đồng đều trên cells lõi (chưa có dân số per-cell) — mock.
    poi_score: tổng hệ số POI rơi vào cell.
    """
    a = float(cfg.get("demand.zone_weight_pop_coeff"))
    b = float(cfg.get("demand.zone_weight_poi_coeff"))
    type_w = cfg.get("demand.poi_type_weights")
    default_w = float(type_w.get("default", 1.0))

    poi_score: dict[str, float] = {c: 0.0 for c in grid.core_cells}
    for p in grid.pois:
        if p.cell in poi_score:
            poi_score[p.cell] += float(type_w.get(p.kind, default_w))

    n = len(grid.core_cells)
    pop_each = 1.0 / n if n else 0.0
    total_poi = sum(poi_score.values()) or 1.0

    raw: dict[str, float] = {}
    for c in grid.core_cells:
        raw[c] = a * pop_each + b * (poi_score[c] / total_poi)
    s = sum(raw.values()) or 1.0
    return {c: w / s for c, w in raw.items()}


def _hour_intensity(cfg: Config) -> dict[int, float]:
    """Trọng số giờ (relative), chỉ giữ các giờ trong run window, chuẩn hóa tổng=1."""
    weights = cfg.get("demand.hour_weights")
    start_min = int(cfg.get("time.start_min"))
    end_min = int(cfg.get("time.end_min"))
    start_h, end_h = start_min // 60, end_min // 60
    kept = {int(h): float(w) for h, w in weights.items() if start_h <= int(h) < end_h}
    s = sum(kept.values()) or 1.0
    return {h: w / s for h, w in kept.items()}


def generate_orders(grid: Grid, cfg: Config, policy: PolicyBundle, seed: int) -> list[Order]:
    """Sinh exogenous trace deterministic theo seed.

    Số đơn/giờ ~ Poisson(orders_per_day × hour_share). Mỗi đơn: pickup cell theo
    zone weight; drop cell theo distance-decay (có thể rơi vào vành k≤buffer);
    quãng đường lognormal; gross theo policy.
    """
    rng = np.random.default_rng(seed)
    orders_per_day = float(cfg.get("demand.orders_per_day"))
    hour_share = _hour_intensity(cfg)
    cell_w = _cell_weights(grid, cfg)
    cells = list(cell_w.keys())
    probs = np.array([cell_w[c] for c in cells], dtype=float)

    med = float(cfg.get("demand.trip_km_median"))
    sigma = float(cfg.get("demand.trip_km_sigma"))
    km_max = float(cfg.get("demand.trip_km_max"))
    buffer_k = int(cfg.get("world.buffer_ring_k"))
    mu = math.log(med)  # lognormal median = exp(mu)

    orders: list[Order] = []
    oid = 0
    for hour, share in sorted(hour_share.items()):
        lam = orders_per_day * share
        n_h = int(rng.poisson(lam))
        for _ in range(n_h):
            t_min = hour * 60 + rng.uniform(0, 60)
            pickup = cells[rng.choice(len(cells), p=probs)]
            dist_km = float(min(km_max, math.exp(rng.normal(mu, sigma))))
            drop = _sample_drop(grid, pickup, dist_km, buffer_k, rng)
            gross = policy.gross_fare(dist_km)
            orders.append(Order(oid, t_min, pickup, drop, round(dist_km, 3), gross))
            oid += 1

    orders.sort(key=lambda o: (o.t_min, o.order_id))
    return orders


def _sample_drop(grid: Grid, pickup: str, dist_km: float, buffer_k: int, rng) -> str:
    """Chọn cell trả: trong grid_disk quanh pickup, ưu tiên cell có khoảng cách gần
    dist_km nhất (distance-decay). Cho phép rơi ngoài lõi (nhãn outside xử lý ở world)."""
    k = max(1, min(buffer_k + 3, int(round(dist_km / 0.35)) + 1))  # ~0.35km/cell res9
    disk = grid_disk(pickup, k)
    if len(disk) <= 1:
        return pickup
    # chọn theo khoảng cách gần mục tiêu, có nhiễu
    dists = np.array([abs(cell_distance_km(grid, pickup, c) - dist_km) for c in disk])
    weights = np.exp(-dists / 0.5)
    weights = weights / weights.sum()
    return disk[rng.choice(len(disk), p=weights)]

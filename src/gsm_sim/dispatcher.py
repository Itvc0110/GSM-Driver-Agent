"""Dispatcher HAI TẦNG trên dispatch tick (T1) — đúng đặc tả `world-parameters.md` §3.

    Tầng 1 — candidate retrieval: `grid_disk(pickup, k_max)` ở res H3 vận hành.
    Tầng 2 — batched bipartite matching: cost(o,d) = **ETA_pickup**,
             `scipy.linear_sum_assignment`, chỉ nhận cặp `ETA ≤ eta_max`.

Nguồn: đặc tả nội bộ dẫn công bố DiDi (batch bipartite Hungarian); thực tế ngành cũng vậy
(Uber/DiDi), xem `research/audit/2026-07-27-current-state/15-*` §2.

## Vì sao KHÔNG dùng greedy nữa (UPDATE-080)

Tầng 2 từng bị hoãn (*"Hungarian để vòng sau"*) và không bao giờ được xây. Greedy để lại **hai
khuyết tật đo được**:

1. **`bad_hex`** (thuật ngữ của Rapido): xếp hạng theo **haversine** nên chọn người *gần hơn về
   hình học nhưng đường chậm hơn*; ETA người đó fail thì **bỏ luôn đơn**, viện lý do "ETA đơn điệu
   theo distance". Sai — `factor` OSRM biến thiên **1,00 → 3,50**. Đo: **293/3.520 lượt bỏ OAN**.
2. **Đói theo `order_id`**: xét đơn theo id tăng dần ⇒ đơn cũ giành mất tài xế mà đơn mới **cần
   hơn** (có khi là ứng viên khả thi DUY NHẤT của nó) ⇒ đơn mới chết hoặc phải nhận người ở xa.

Hungarian xử lý cả hai vì nó tối ưu **tổng** trên toàn bộ cặp khả thi cùng lúc.

Greedy vẫn giữ được qua `disp_cfg["matching"] = "greedy"` — đặc tả yêu cầu giữ nó làm **baseline
so sánh**, và nó là đường lui khi ma trận quá lớn.

Deterministic: ma trận dựng theo thứ tự `sorted(order_id)` × `sorted(actor_id)`; tie-break ổn định.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

from .entities import Actor, ActorState
from .geo import Grid, grid_disk, haversine_km

# cost cho cặp KHÔNG khả thi — lớn hơn mọi ETA thật nhưng hữu hạn (scipy cần hữu hạn)
INFEASIBLE = 1e6
# trần kích thước bài toán gán; vượt thì rơi về greedy (giữ thời gian tick có trần)
MAX_PAIRS = 200_000


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
    """Gán đơn cho tài xế trong một tick. Trả list[Assignment] theo `order_id` tăng dần.

    Tầng 1 dựng ứng viên bằng H3; tầng 2 giải bài toán gán tối ưu tổng ETA. Mỗi tài xế nhận
    tối đa 1 đơn/tick. Cặp có `ETA > eta_max` không bao giờ được gán.
    """
    if not open_orders or not idle_actors:
        return []

    k_max = int(disp_cfg["candidate_ring_k_max"])
    eta_max = float(disp_cfg["eta_max_min"])
    mode = str(disp_cfg.get("matching", "batch")).lower()

    orders = sorted(open_orders, key=lambda o: o.order_id)
    actors = sorted(idle_actors, key=lambda a: a.actor_id)
    idx_of = {a.actor_id: j for j, a in enumerate(actors)}

    by_cell: dict[str, list[Actor]] = {}
    for a in actors:
        by_cell.setdefault(a.cell, []).append(a)

    speed = {}

    def _eta(order, a) -> float:
        """ETA đón THẬT: quãng đường × hệ số đường CỦA CẶP Ô ÷ tốc độ hiệu dụng.

        Dùng `factor_fn` chứ không phải haversine trần — đây là chỗ sinh ra `bad_hex`.
        """
        h = speed.get(order.pickup_cell)
        if h is None:
            h = speed_fn(order.pickup_cell, hour) if speed_fn is not None                 else _speed_kmh(hour, speed_cfg)
            speed[order.pickup_cell] = h
        d = haversine_km(a.lat, a.lon, order.pickup_lat, order.pickup_lon)
        fac = factor_fn(a.cell, order.pickup_cell) if factor_fn is not None else detour
        return d * fac / h * 60.0, d

    # --- Tầng 1: ứng viên theo H3, kèm ETA/khoảng cách ---
    cand: list[list[tuple[int, float, float]]] = []   # theo thứ tự `orders`
    for order in orders:
        row: list[tuple[int, float, float]] = []
        for cell in grid_disk(order.pickup_cell, k_max):
            for a in by_cell.get(cell, []):
                eta, d = _eta(order, a)
                if eta <= eta_max:
                    row.append((idx_of[a.actor_id], eta, d))
        cand.append(row)

    n_o, n_d = len(orders), len(actors)
    use_batch = mode != "greedy" and n_o > 1 and n_d > 1 and n_o * n_d <= MAX_PAIRS

    if use_batch:
        # --- Tầng 2: bipartite, cost = ETA, cặp không khả thi = INFEASIBLE ---
        cost = np.full((n_o, n_d), INFEASIBLE, dtype=float)
        dist = np.zeros((n_o, n_d), dtype=float)
        for i, row in enumerate(cand):
            for j, eta, d in row:
                if eta < cost[i, j]:          # cùng cặp có thể xuất hiện 1 lần; giữ nhỏ nhất
                    cost[i, j] = eta
                    dist[i, j] = d
        rows, cols = linear_sum_assignment(cost)
        out = [Assignment(orders[i].order_id, actors[j].actor_id,
                          round(float(dist[i, j]), 3), round(float(cost[i, j]), 2))
               for i, j in zip(rows, cols) if cost[i, j] < INFEASIBLE]
        return sorted(out, key=lambda x: x.order_id)

    # --- Đường lui: greedy theo ETA (baseline so sánh + khi bài toán quá lớn) ---
    taken: set[int] = set()
    out = []
    for i, order in enumerate(orders):
        best = None
        for j, eta, d in sorted(cand[i], key=lambda t: (t[1], actors[t[0]].actor_id)):
            if j in taken:
                continue
            best = (j, eta, d)
            break
        if best is None:
            continue
        j, eta, d = best
        taken.add(j)
        out.append(Assignment(order.order_id, actors[j].actor_id, round(d, 3), round(eta, 2)))
    return out

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
from .geo import Grid, cell_distance_km, grid_disk, haversine_km, sample_point_in_cell
from .policy import PolicyBundle


@dataclass(frozen=True)
class Order:
    order_id: int
    t_min: float  # phút từ 00:00
    pickup_cell: str
    drop_cell: str
    dist_km: float
    gross_vnd: int
    patience_min: float = 5.0  # khách hủy nếu chưa match sau chừng này phút (exogenous, CRN-safe)
    # toạ độ liên tục "địa chỉ thực" trong cell (hybrid lat/lng — cho movement + visualize)
    pickup_lat: float = 0.0
    pickup_lon: float = 0.0
    drop_lat: float = 0.0
    drop_lon: float = 0.0


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


def expected_demand_field(grid: Grid, cfg: Config) -> dict[int, dict[str, float]]:
    """M0-3: kỳ vọng đơn theo (giờ, cell) TỪ CONFIG — không đọc realized trace.

    λ(cell, hour) = orders_per_day × hour_share(hour) × cell_weight(cell).
    Đây là nguồn thông tin HỢP LỆ cho belief của actor (kinh nghiệm/prior),
    thay cho demand_field cũ xây từ chính orders của run (future-information leak).
    Deterministic theo config — không phụ thuộc seed."""
    orders_per_day = float(cfg.get("demand.orders_per_day"))
    hour_share = _hour_intensity(cfg)
    cell_w = _cell_weights(grid, cfg)
    return {h: {c: orders_per_day * share * w for c, w in cell_w.items()}
            for h, share in hour_share.items()}


def generate_orders(grid: Grid, cfg: Config, policy: PolicyBundle, seed: int, env=None,
                    road=None) -> list[Order]:
    """Sinh exogenous trace deterministic theo seed.

    Số đơn/giờ ~ Poisson(orders_per_day × hour_share × env.demand_factor) + event.
    Mỗi đơn: pickup cell theo zone weight (+event addend); drop cell distance-decay;
    quãng đường lognormal; gross theo policy. env=None → không biến môi trường (baseline).
    """
    rng = np.random.default_rng(seed)
    # RNG stream RIÊNG cho toạ độ điểm — tách khỏi trace ngoại sinh (cells/dist/gross/patience)
    # để thêm lat/lng KHÔNG xáo trộn trace cũ (baseline metrics bất biến, CRN-safe).
    rng_pt = np.random.default_rng(seed ^ 0xC0FFEE)
    orders_per_day = float(cfg.get("demand.orders_per_day"))
    hour_share = _hour_intensity(cfg)
    cell_w = _cell_weights(grid, cfg)
    cells = list(cell_w.keys())
    base_probs = np.array([cell_w[c] for c in cells], dtype=float)

    med = float(cfg.get("demand.trip_km_median"))
    sigma = float(cfg.get("demand.trip_km_sigma"))
    km_max = float(cfg.get("demand.trip_km_max"))
    buffer_k = int(cfg.get("world.buffer_ring_k"))
    km_per_cell = float(cfg.get("demand.drop_km_per_cell", 0.35))
    softness = float(cfg.get("demand.drop_softness_km", 0.5))
    # b0-D: mức bám cầu của điểm TRẢ khách. 0 = thuần khoảng cách (hành vi cũ, trace y hệt).
    drop_alpha = float(cfg.get("demand.drop_demand_alpha", 0.0) or 0.0)
    mu = math.log(med)  # lognormal median = exp(mu)

    pat_med = float(cfg.get("dispatcher.patience_median_min", 3.0))
    pat_sigma = float(cfg.get("dispatcher.patience_sigma", 0.5))
    pat_max = float(cfg.get("dispatcher.patience_max_min", 10.0))
    pat_mu = math.log(pat_med)

    detour_f = float(cfg.get("demand.detour_factor", 1.3))   # fallback khi matrix thiếu cặp
    # AUDIT A1 DEMAND-1 (UPDATE-065): cờ `demand.hour_interp` là cờ CHẾT — đọc rồi không
    # dùng, trong khi config khai true kèm chú thích "nội suy" (nói dối người đọc config).
    # Đã gỡ cả hai phía; nội suy cường độ giữa mốc giờ nếu muốn là việc CALIBRATION có
    # regate 30 seed (ghi DEFERRED D-SIM-19), không phải flip cờ.
    hours_sorted = sorted(hour_share.keys())

    orders: list[Order] = []
    oid = 0
    for hour in hours_sorted:
        share = hour_share[hour]
        # env demand factor tại giữa giờ (level, đã clamp tổng)
        env_f = env.demand_factor(hour * 60 + 30) if env is not None else 1.0
        lam = orders_per_day * share * env_f
        n_h = int(rng.poisson(lam))
        for _ in range(n_h):
            t_min = hour * 60 + rng.uniform(0, 60)
            # t rải ĐỀU trong giờ (không nội suy cường độ giữa mốc giờ — xem D-SIM-19)
            pickup = _sample_pickup(cells, base_probs, grid, env, t_min, rng)
            target_km = float(min(km_max, math.exp(rng.normal(mu, sigma))))
            drop = _sample_drop(grid, pickup, target_km, buffer_k, km_per_cell, softness, rng,
                                demand_w=cell_w, alpha=drop_alpha)
            patience = float(min(pat_max, math.exp(rng.normal(pat_mu, pat_sigma))))
            p_lat, p_lon = sample_point_in_cell(grid, pickup, rng_pt)
            d_lat, d_lon = sample_point_in_cell(grid, drop, rng_pt)
            # M0-9 distance contract: dist_km = haversine giữa ĐÚNG 2 endpoint đã chọn
            # (lognormal chỉ để CHỌN drop cell — shape phân phối giữ qua distance-decay).
            # Fare/time/SOC đều đi từ dist_km × detour → một nguồn khoảng cách duy nhất.
            dist_km = haversine_km(p_lat, p_lon, d_lat, d_lon)
            # SIM-XANH: cước tính trên QUÃNG ĐƯỜNG LÁI THẬT (XanhSM tính cước theo km lộ
            # trình, không phải chim bay). road=None → giữ nguyên đường cũ (haversine).
            fare_km = dist_km * road.factor(pickup, drop, detour_f) if road else dist_km
            gross = policy.gross_fare(fare_km)
            orders.append(Order(oid, t_min, pickup, drop, round(dist_km, 3), gross, round(patience, 2),
                                p_lat, p_lon, d_lat, d_lon))
            oid += 1

    # event addend: sinh cuốc cộng thêm quanh venue (CỘNG không nhân)
    if env is not None and env.events:
        oid = _add_event_orders(orders, oid, grid, cells, env, policy, mu, sigma, km_max,
                                buffer_k, km_per_cell, softness, pat_mu, pat_sigma, pat_max, rng, rng_pt,
                                road=road, detour_f=detour_f,
                                demand_w=cell_w, drop_alpha=drop_alpha)

    orders.sort(key=lambda o: (o.t_min, o.order_id))
    # đánh lại order_id theo thứ tự thời gian để deterministic + ổn định
    return [Order(i, o.t_min, o.pickup_cell, o.drop_cell, o.dist_km, o.gross_vnd, o.patience_min,
                  o.pickup_lat, o.pickup_lon, o.drop_lat, o.drop_lon)
            for i, o in enumerate(orders)]


def _sample_pickup(cells, base_probs, grid, env, t_min, rng) -> str:
    """Chọn cell đón. Baseline: theo zone weight. Có event: cộng addend vào weight."""
    if env is None or not env.events:
        return cells[rng.choice(len(cells), p=base_probs)]
    add = np.array([env.event_addend(c, t_min) for c in cells], dtype=float)
    if add.sum() <= 0:
        return cells[rng.choice(len(cells), p=base_probs)]
    w = base_probs + add / max(1.0, add.sum())
    w = w / w.sum()
    return cells[rng.choice(len(cells), p=w)]


def _add_event_orders(orders, oid, grid, cells, env, policy, mu, sigma, km_max,
                      buffer_k, km_per_cell, softness, pat_mu, pat_sigma, pat_max, rng, rng_pt,
                      road=None, detour_f=1.3, demand_w=None, drop_alpha=0.0) -> int:
    """Sinh cuốc sự kiện (cộng thêm) — sample thời điểm trong cửa sổ event, cell quanh venue."""
    for ev in env.events:
        # tổng cuốc kỳ vọng của event (xấp xỉ) = N·capture (rải theo time profile)
        n_event = int(ev.attendance * ev.capture_rate)
        # rải trong [ramp_start, t_end+egress]
        t_lo = ev.t_start_min - ev.ramp_in_min
        t_hi = ev.t_end_min + ev.egress_min
        for _ in range(n_event):
            # sample thời điểm theo profile bằng rejection đơn giản
            for _try in range(5):
                t = rng.uniform(t_lo, t_hi)
                if rng.random() < env._event_time_profile(ev, t) * 60.0:
                    break
            cell = _event_pickup_cell(grid, cells, ev, rng)
            target_km = float(min(km_max, math.exp(rng.normal(mu, sigma))))
            drop = _sample_drop(grid, cell, target_km, buffer_k, km_per_cell, softness, rng,
                                demand_w=demand_w, alpha=drop_alpha)
            patience = float(min(pat_max, math.exp(rng.normal(pat_mu, pat_sigma))))
            p_lat, p_lon = sample_point_in_cell(grid, cell, rng_pt)
            d_lat, d_lon = sample_point_in_cell(grid, drop, rng_pt)
            dist_km = haversine_km(p_lat, p_lon, d_lat, d_lon)  # M0-9 contract
            fare_km = dist_km * road.factor(cell, drop, detour_f) if road else dist_km
            orders.append(Order(oid, t, cell, drop, round(dist_km, 3), policy.gross_fare(fare_km),
                                round(patience, 2), p_lat, p_lon, d_lat, d_lon))
            oid += 1
    return oid


def _event_pickup_cell(grid, cells, ev, rng) -> str:
    from .geo import grid_disk
    disk = [c for c in grid_disk(ev.venue_cell, int(2 * ev.sigma_cells)) if grid.is_core(c)]
    return rng.choice(disk) if disk else ev.venue_cell


_ALLOWED_DROP_CACHE: dict[int, frozenset[str]] = {}


def _allowed_drop_cells(grid: Grid, buffer_k: int) -> frozenset[str]:
    """OD boundary (spec pilot-world): đích ∈ lõi ∪ vành buffer k≤buffer_k quanh LÕI.
    Precompute một lần per grid (cache theo id(grid))."""
    key = id(grid)
    cached = _ALLOWED_DROP_CACHE.get(key)
    if cached is not None:
        return cached
    allowed: set[str] = set()
    for c in grid.core_cells:
        allowed.update(grid_disk(c, buffer_k))
    out = frozenset(allowed)
    _ALLOWED_DROP_CACHE.clear()  # giữ 1 grid (tránh leak khi chạy nhiều grid)
    _ALLOWED_DROP_CACHE[key] = out
    return out


def _sample_drop(grid: Grid, pickup: str, dist_km: float, buffer_k: int,
                 km_per_cell: float, softness: float, rng,
                 demand_w: dict[str, float] | None = None,
                 alpha: float = 0.0) -> str:
    """Chọn cell trả: disk quanh pickup MỞ THEO target distance (M0-9 — không cap
    tại buffer_k+3 như baseline: cap cũ chặn mọi cuốc >~2.5km rồi vẫn tính tiền
    theo lognormal → distance contract gãy). Đích ràng buộc trong lõi ∪ buffer
    quanh LÕI (OD boundary); distance-decay ưu tiên cell gần target nhất.
    Hệ quả trung thực: pilot Đống Đa nhỏ (~3-4km ngang) nên phân phối quãng đường
    THỰC bị cắt bởi địa lý — median thấp hơn target 3.5km là giới hạn vật lý của
    pilot, ghi nhãn CALIBRATION GAP cho T-021, không che bằng số ảo.

    ## b0-D (2026-07-28, Cường chốt "sửa trước khi đo b4"): điểm trả BÁM CẦU

    Bản chỉ-theo-khoảng-cách tạo ra thế giới mà **nơi trả khách ANTI-tương quan với cầu**
    (đo seed 1000: corr = **−0,226**; 10 ô cầu cao nhất nhận 30,3% lượt đặt nhưng chỉ 2,2%
    lượt trả; **82,3%** cuốc trả ngoài lõi ⇒ deadhead 11,8% tổng thời gian). Cơ chế: vùng
    được phép trả 316 ô nhưng lõi chỉ 85, distance-decay còn đẩy ra vành — trong khi người
    thật đi TỚI chỗ đông (nhà/văn phòng/TTTM), chính nơi phát sinh cầu.

    Fix: nhân hệ số cầu **pha tuyến tính** `m(c) = 1 + alpha·(w(c)/w̄ − 1)`, kẹp ≥ 0,
    chuẩn hoá theo trung bình TRÊN DISK (scale-free từng quyết định):

    - `alpha = 0` ⇒ m ≡ 1.0 **chính xác IEEE** ⇒ trace cũ y hệt từng bit (nhánh dưới bị
      bỏ qua hoàn toàn — điều kiện để baseline cũ còn so sánh được);
    - **cố ý KHÔNG dùng luỹ thừa** `(w/w̄)^alpha` (bản preview lúc duyệt): ô buffer có
      w = 0, luỹ thừa giết SẠCH chúng ở mọi alpha > 0 ⇒ 100% cuốc trả trong lõi — sửa lố
      theo chiều ngược lại. Pha tuyến tính giữ ô buffer sống với trọng số 1−alpha.
    """
    k = max(1, int(round(dist_km / km_per_cell)) + 2)
    allowed = _allowed_drop_cells(grid, buffer_k)
    disk = [c for c in grid_disk(pickup, k) if c in allowed]
    if len(disk) <= 1:
        return pickup
    dists = np.array([abs(cell_distance_km(grid, pickup, c) - dist_km) for c in disk])
    weights = np.exp(-dists / softness)
    if alpha > 0.0 and demand_w:
        dw = np.array([float(demand_w.get(c, 0.0)) for c in disk])
        mean = dw.mean()
        if mean > 0.0:
            mult = np.maximum(0.0, 1.0 + alpha * (dw / mean - 1.0))
            if mult.sum() > 0.0:            # tất cả 0 (không thể khi mean>0, nhưng phòng thủ)
                weights = weights * mult
    weights = weights / weights.sum()
    return disk[rng.choice(len(disk), p=weights)]

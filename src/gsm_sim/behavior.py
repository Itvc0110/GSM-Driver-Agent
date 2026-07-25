"""Behavior model B-arm (bản năng — không advice).

Nguồn: advisor-optimization-layer-a.md §1. Deterministic theo RNG stream truyền vào.
Cung cấp quyết định: accept đơn, chọn hành động khi idle, chọn trạm đổi pin.

Slice v0: xấp xỉ utility model — đủ để actor hành xử hợp lý (chạy peak, nghỉ trưa,
đi đổi pin khi SOC thấp, kết ca quanh giờ quen). Tinh chỉnh tham số ở calibration (T-021).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
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


# SIM-1: trọng số kinh tế trong quyết định nhận đơn. Nhỏ (<1) để `accept_base` của
# archetype giữ vai trò chính — thực tế tài xế từ chối vì xa/mệt/cuối ca, không thuần
# theo tiền từng cuốc. ASSUMPTION, hiệu chỉnh bằng gate test ≥30 seed.
ECON_WEIGHT = 0.7


@dataclass(frozen=True)
class AcceptDecision:
    """SIM-2: quyết định nhận đơn kèm ĐỦ căn cứ để giải trình sau.

    Trước đây `accept_order` chỉ trả bool ⇒ event `order_declined` không nói được **vì sao**
    tài xế từ chối. Journey của Cường cần trả lời đúng câu đó cho TỪNG offer.
    """
    accepted: bool
    p_accept: float       # xác suất nhận tại thời điểm đó
    net_vnd: float        # gross − chi phí quãng đón
    z: float              # độ lệch chuẩn hoá của net so trung vị thị trường (đã kẹp)
    reason: str           # forced | base_behavior | economics


def decide_accept(actor: Actor, gross_vnd: int, pickup_dist_km: float, forced: bool, rng,
                  cost_per_km_vnd: float = 3000.0, logit_center_vnd: float = 6000.0,
                  logit_scale_vnd: float = 8000.0) -> AcceptDecision:
    """Quyết định nhận đơn, kèm căn cứ. Đây là NƠI CHỨA mô hình thật.

    MÔ HÌNH (hiệu chỉnh ở SIM-1, khuyết tật đã chứng minh bằng số):
      Bản cũ `x = (net − center)/scale + logit(accept_base)` có số hạng kinh tế ÁP ĐẢO:
      cuốc thường (gross 20k, pickup 1km → net 17k) cho (17000−6000)/8000 = **+1.375**,
      khiến P4 (`accept_base` 0.80) thực tế nhận **94%** và P3 (0.98) nhận 99.5%
      ⇒ **archetype gần như vô nghĩa** (accept tổng 96.3%, thực tế 0.74–0.97).

      Bản hiện tại: **`accept_base` LÀ mức nhận trung bình của archetype**, kinh tế chỉ
      **điều biến quanh** nó — `x = logit(accept_base) + w·z` với `z` **kẹp [−2, 2]** và
      `w = ECON_WEIGHT` nhỏ. Khi net ≈ center → nhận đúng `accept_base`; chỉ cuốc xa/rẻ
      (z âm) mới bị từ chối nhiều hơn. `logit_center_vnd` vì vậy mang nghĩa **net TRUNG VỊ
      của thị trường**, KHÔNG phải mốc "hoà vốn" — phải đặt theo phân phối cuốc thật.

    ⚠️ Tiêu **ĐÚNG 1** `rng.random()`, y như bản cũ. Tiêu thêm/bớt sẽ dịch chuỗi ngẫu nhiên
    ⇒ đổi kết quả SIM-1 và phá nền CRN của SIM-4 (thế giới song song phải dùng chung dòng
    ngoại sinh).

    `reason` khi TỪ CHỐI:
      - `economics`: cuốc dưới trung vị thị trường (z < 0) kéo xác suất xuống — tài xế chê
        xa/rẻ. Đây là dư địa advisor.
      - `base_behavior`: cuốc bình thường/tốt (z ≥ 0) nhưng vẫn rơi theo `accept_base` của
        archetype (mệt, sắp kết ca, tính cách kén). KHÔNG phải do tiền.
    """
    if forced:
        return AcceptDecision(True, 1.0, float(gross_vnd), 0.0, "forced")
    net = gross_vnd - pickup_dist_km * cost_per_km_vnd
    z = (net - logit_center_vnd) / max(1e-6, logit_scale_vnd)
    z = max(-2.0, min(2.0, z))
    base = min(0.999, max(0.001, actor.accept_base))
    x = math.log(base / (1 - base)) + ECON_WEIGHT * z
    p = _logistic(x)
    accepted = rng.random() < p          # ← DUY NHẤT một lần rút
    reason = "accepted" if accepted else ("economics" if z < 0 else "base_behavior")
    return AcceptDecision(accepted, p, float(net), float(z), reason)


def accept_order(actor: Actor, gross_vnd: int, pickup_dist_km: float, forced: bool, rng,
                 cost_per_km_vnd: float = 3000.0, logit_center_vnd: float = 6000.0,
                 logit_scale_vnd: float = 8000.0) -> bool:
    """Quyết định nhận đơn (chỉ bool). forced=True (auto-accept) → luôn nhận.

    SIM-2: giữ nguyên chữ ký cho caller/test cũ; mô hình thật nằm ở `decide_accept`
    (xem docstring ở đó để hiểu vì sao `accept_base` là mức trung bình còn kinh tế chỉ
    điều biến quanh nó — hiệu chỉnh SIM-1).
    """
    return decide_accept(actor, gross_vnd, pickup_dist_km, forced, rng,
                         cost_per_km_vnd, logit_center_vnd, logit_scale_vnd).accepted


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

    # 3. Giờ ăn quen + đã chạy đủ lâu → nghỉ (M0-7: đúng MỘT lần/ngày — cờ meals_taken)
    fatigue = actor.online_min / max(1.0, actor.fatigue_threshold_min)
    if (hour == actor.meal_hour and actor.meals_taken == 0
            and fatigue > 0.35 and rng.random() < 0.5):
        actor.meals_taken += 1
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

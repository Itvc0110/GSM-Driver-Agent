"""Thực thể sim: Actor, Station. Order ở demand.py.

Nguồn: specs/simulation-pilot-world.md §2.2, advisor-optimization-layer-a.md §1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ActorState(str, Enum):
    OFFLINE = "offline"
    IDLE = "idle"
    ENROUTE = "enroute"   # đang tới điểm đón
    ON_TRIP = "on_trip"
    CHARGING = "charging"  # đổi pin / sạc
    REST = "rest"


class FleetType(str, Enum):
    SWAP = "swap"     # đổi pin tại trạm
    CHARGE = "charge"  # sạc cắm tại nhà


@dataclass
class Actor:
    actor_id: int
    archetype: str            # P1..P5
    fleet: FleetType
    home_cell: str
    shift_start_min: float
    shift_end_min: float
    # tham số hành vi (từ archetype sampling)
    demand_prior_sigma: float
    accept_base: float
    fatigue_threshold_min: float
    meal_hour: int
    # trạng thái động
    state: ActorState = ActorState.OFFLINE
    cell: str = ""
    lat: float = 0.0        # vị trí liên tục hiện tại (hybrid lat/lng)
    lon: float = 0.0
    soc_pct: float = 100.0
    # đếm trong ca
    trips_done: int = 0
    orders_offered: int = 0
    orders_accepted: int = 0
    orders_completed: int = 0
    orders_cancelled: int = 0      # SIM-1: CHỈ huỷ SAU khi nhận (khớp `cancelled_count`)
    orders_soc_skipped: int = 0    # SIM-1: bỏ qua vì pin không đủ — KHÔNG phải huỷ
    gross_vnd: int = 0
    payout_vnd: int = 0
    points: int = 0
    online_min: float = 0.0
    empty_min: float = 0.0      # di chuyển không khách (pickup + relocate + deadhead)
    occupied_min: float = 0.0   # có khách (đo utilization)
    idle_min: float = 0.0       # chờ đơn tại chỗ
    rest_min: float = 0.0       # nghỉ
    charge_min: float = 0.0     # đổi pin / sạc (gồm chờ)
    stranded_count: int = 0
    meals_taken: int = 0        # M0-7: nghỉ ăn tối đa 1 lần/ngày trong meal_hour
    # SIM-4: mức NÂNG TẠM THỜI của accept_base khi tài xế nghe lời khuyên "tỷ lệ nhận của
    # anh đang dưới ngưỡng đủ điều kiện thưởng". Chỉ có hiệu lực trong ca, có trần.
    # KHÔNG phải khuyên nhận/từ chối một ĐƠN CỤ THỂ (ranh giới sản phẩm CLAUDE.md §5) —
    # đây là thay đổi ở mức TỶ LỆ, đúng cách policy đặt điều kiện.
    accept_lift: float = 0.0
    # D-SIM-03: idle tích luỹ THEO GIỜ — đầu vào cho solver S7 `idle_reduction`.
    # `idle_min` tổng không đủ: S7 cần biết chờ nhiều Ở KHUNG GIỜ NÀO mới chỉ được khung
    # đáng dồn nghỉ vào.
    idle_by_hour: dict = field(default_factory=dict)
    rest_deferred_min: float = 0.0   # D-SIM-03: tổng phút đã hoãn nghỉ theo lời khuyên
    shift_extended_min: float = 0.0   # SIM-4: số phút đã hoãn kết ca theo lời khuyên

    @property
    def effective_accept_base(self) -> float:
        """`accept_base` sau khi cộng lift, kẹp trần 0.98 (không ai nhận 100%)."""
        return min(0.98, self.accept_base + self.accept_lift)
    # kinh nghiệm cá nhân: bảng demand prior theo (cell, hour) — khởi tạo lazily
    demand_prior: dict = field(default_factory=dict)

    @property
    def acceptance_rate(self) -> float:
        return self.orders_accepted / self.orders_offered if self.orders_offered else 1.0

    @property
    def completion_rate(self) -> float:
        return self.orders_completed / self.orders_accepted if self.orders_accepted else 1.0

    def consume_soc(self, dist_km: float, pct_per_km: float) -> None:
        self.soc_pct = max(0.0, self.soc_pct - dist_km * pct_per_km)


@dataclass
class BatteryInStation:
    """Một viên pin trong tủ; sạc lại sau khi tài xế trả pin cạn."""
    soc_pct: float
    ready_at_min: float  # thời điểm đạt ready_soc (nếu đang sạc)


@dataclass
class Station:
    node_id: int
    cell: str
    lat: float
    lon: float
    slots: int
    ready_soc_pct: float
    # danh sách pin đang có trong tủ (mock: số pin sẵn sàng)
    batteries: list[BatteryInStation] = field(default_factory=list)
    queue_len: int = 0

    def available_full(self, now_min: float) -> int:
        return sum(1 for b in self.batteries if b.soc_pct >= self.ready_soc_pct and b.ready_at_min <= now_min)

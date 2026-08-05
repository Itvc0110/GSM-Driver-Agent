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
    # T-045d: phút RỖI LIÊN TỤC kể từ lần được CHÀO đơn gần nhất. Được chào = bằng chứng "ở đây
    # có cầu" ⇒ reset. Không có bằng chứng nào suốt N phút ⇒ tài xế sốt ruột đi xa hơn.
    idle_streak_min: float = 0.0
    # T-045a b2: ô ĐÍCH của chuyến di chuyển tự nguyện đang diễn ra (relocate / deadhead về lõi).
    # `ActorState.ENROUTE` một mình KHÔNG đủ: nó dùng chung cho cả đi đón khách, và `cell` chỉ
    # đổi khi tới nơi ⇒ không suy được "ai đang tới ô nào". Không có trường này thì `MarketState`
    # không trừ được CUNG ĐANG TỚI, và advisor sẽ khuyên cả đoàn dồn vào một ô.
    # `None` khi đứng yên hoặc khi đang chở khách (đích là điểm trả khách — xem miễn trừ ở
    # `tests/test_market_state_sim_producer.py`).
    enroute_cell: str | None = None
    # T-045b (Cycle P): sổ CHI PHÍ riêng — TÁCH BẠCH khỏi payout (§5 gross/payout/net).
    # `km_driven` accrue tại `consume_soc` (chốt chặn DUY NHẤT của mọi di chuyển tốn pin);
    # `cost_vnd` = km × cash_cost + phí đổi pin, mặc định config = 0 ⇒ luôn 0 (bit-identical).
    km_driven: float = 0.0
    cost_vnd: int = 0
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
    # SIM-XANH P2: rating trong sim (khách chấm sau cuốc) — reset theo ngày
    ratings_n: int = 0
    ratings_sum: int = 0
    ratings_5: int = 0
    # SIM-XANH P2: tài xế mới — tenure TĂNG theo ngày (KHÔNG reset; xem reset_for_new_day)
    tenure_days: int = 365
    newbie_topup_vnd: int = 0     # bù bảo lãnh doanh thu NGÀY (reset theo ngày)
    # SIM-XANH P2: mission ngày — tiến độ reset theo ngày
    mission_progress: dict = field(default_factory=dict)   # mission_id -> count
    mission_reward_vnd: int = 0   # thưởng mission NGÀY (reset theo ngày)
    # SIM-4: mức NÂNG TẠM THỜI của accept_base khi tài xế nghe lời khuyên "tỷ lệ nhận của
    # anh đang dưới ngưỡng đủ điều kiện thưởng". Chỉ có hiệu lực trong ca, có trần.
    # KHÔNG phải khuyên nhận/từ chối một ĐƠN CỤ THỂ (ranh giới sản phẩm CLAUDE.md §5) —
    # đây là thay đổi ở mức TỶ LỆ, đúng cách policy đặt điều kiện.
    accept_lift: float = 0.0
    # D-SIM-03: idle tích luỹ THEO GIỜ — đầu vào cho solver S7 `idle_reduction`.
    # `idle_min` tổng không đủ: S7 cần biết chờ nhiều Ở KHUNG GIỜ NÀO mới chỉ được khung
    # đáng dồn nghỉ vào.
    idle_by_hour: dict = field(default_factory=dict)
    rest_deferred_min: float = 0.0   # D-SIM-03: tổng phút đã hoãn nghỉ theo lời khuyên.
    # ⚠ D-M3-04-FIX (2026-08-05): đổi cách đếm — cộng MỘT LẦN đúng khoảng hoãn lúc CAM KẾT,
    # không phải +2′/tick như bản cũ; trần `rest_defer_max_min` (POLICY_LOCKED) nay đếm đúng
    # đại lượng nó canh.
    # D-SIM-10: khung giờ nên dồn nghỉ, do solver S7 rút ra từ idle NGÀY HÔM QUA.
    # None ở ngày đầu (chưa có lịch sử) — đó là đúng, không phải thiếu sót.
    planned_rest_hour: int | None = None
    # D-M3-04-FIX: hoãn nghỉ = CAM KẾT, không phải phủ quyết (UPDATE-140: bản phủ quyết biến
    # 86% nghỉ thành CHỜ RỖNG mà không sinh thêm đơn nào).
    #   `rest_commit_due_min`  — phút tuyệt-đối-trong-ngày của ĐẦU giờ đã hứa nghỉ; None = không
    #                            có cam kết mở. Dùng phút (không phải giờ) để sống sót ca vắt đêm.
    #   `rest_commit_broken`   — cam kết đã VỠ (bận trọn giờ X) ⇒ quyền nghỉ đã trả lại: cấm
    #                            phủ quyết mọi bản năng nghỉ cho tới khi nghỉ THẬT xảy ra.
    rest_commit_due_min: float | None = None
    rest_commit_broken: bool = False
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
        self.km_driven += float(dist_km)   # T-045b: một chốt chặn km cho sổ chi phí

    # D-SIM-10: danh sách TƯỜNG MINH những gì reset mỗi ngày. Để tường minh (thay vì "reset
    # mọi thứ trừ…") vì chỗ này dễ sai theo cả HAI chiều: quên reset ⇒ điểm/cuốc cộng dồn vô
    # hạn, thưởng ngày sai; reset nhầm ⇒ mất lịch sử, "học từ hôm qua" thành giả.
    _DAILY_RESET_INT = ("trips_done", "orders_offered", "orders_accepted", "orders_completed",
                        "orders_cancelled", "orders_soc_skipped", "gross_vnd", "payout_vnd",
                        "points", "stranded_count", "meals_taken",
                        # SIM-XANH P2 (rating/newbie-ngày/mission-ngày là trạng thái NGÀY)
                        "ratings_n", "ratings_sum", "ratings_5",
                        "newbie_topup_vnd", "mission_reward_vnd", "cost_vnd")
    _DAILY_RESET_FLOAT = ("online_min", "empty_min", "occupied_min", "idle_min", "rest_min",
                          "charge_min", "accept_lift", "rest_deferred_min", "shift_extended_min",
                          "km_driven",
                          # D-E10-01 (thêm 2026-07-31): chuỗi rỗi LIÊN TỤC là trạng thái
                          # NGÀY. Thiếu nó, ngày 2 của run multiday mở màn với streak tồn dư
                          # cuối ngày 1 ⇒ bản năng sốt ruột (`behavior.py`) và trigger E10b
                          # đọc một tài xế vừa ngủ dậy như thể đã đứng chờ 40 phút liên tục —
                          # sai theo hướng "sốt ruột hơn thực tế". Vô hại ở sim một-ngày
                          # (mọi artifact tới nay) nhưng là điều kiện tiên quyết của `D-M3-04`.
                          "idle_streak_min")

    def reset_for_new_day(self, soc_pct: float, shift_start_min: float,
                          shift_end_min: float) -> None:
        """Sang ngày mới: xoá trạng thái NGÀY, giữ nguyên DANH TÍNH.

        KHÔNG đụng: `actor_id`, `archetype`, `fleet`, `home_cell`, `accept_base`,
        `demand_prior_sigma`, `fatigue_threshold_min`, `meal_hour` — đó là con người, không
        phải trạng thái ngày. Lịch sử cuộn nằm ở `DriverMemory` (ngoài Actor) nên cũng an toàn.
        """
        for name in self._DAILY_RESET_INT:
            setattr(self, name, 0)
        for name in self._DAILY_RESET_FLOAT:
            setattr(self, name, 0.0)
        self.idle_by_hour = {}
        self.mission_progress = {}
        self.demand_prior = {}
        self.enroute_cell = None               # T-045a: đích di chuyển là trạng thái NGÀY
        # D-M3-04-FIX: cam kết nghỉ là trạng thái NGÀY — dòng TƯỜNG MINH (không nhét vào
        # _DAILY_RESET_FLOAT vì giá trị reset là None/False, không phải 0.0). Bẫy D-E10-01:
        # quên dòng này ⇒ ngày 2 mở màn với cam kết tồn dư của hôm qua.
        self.rest_commit_due_min = None
        self.rest_commit_broken = False
        # tenure TĂNG 1 mỗi sáng — thời gian trôi là danh tính động duy nhất
        self.tenure_days += 1
        self.state = ActorState.OFFLINE
        self.soc_pct = float(soc_pct)          # sạc/đổi pin qua đêm
        self.shift_start_min = float(shift_start_min)
        self.shift_end_min = float(shift_end_min)
        self.cell = self.home_cell             # sáng ra xuất phát từ nhà


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

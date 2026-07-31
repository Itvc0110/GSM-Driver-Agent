"""SimPy world — ghép mọi thứ chạy 1 ngày (1 arm B).

Nguồn: specs/simulation-pilot-world.md, advisor-optimization-layer-a.md §1/§4.
Kiến trúc: pure DES cho trip/swap lifecycle + dispatch tick 5s. Event log append vào list.

Slice v0: 1 arm (B, không advice). Twin-runner 3 arm ở vòng sau.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import h3
import numpy as np
import simpy

from .behavior import IdleAction, choose_idle_action, choose_station, decide_accept
from .config import Config
from .dispatcher import _speed_kmh, match_batch
from .entities import Actor, ActorState, BatteryInStation, FleetType, Station
from .geo import Grid, cell_distance_km, grid_disk
from .policy import PolicyBundle

# D-M3-01: kind event cho các nhánh KHÔNG tự log của hai kênh từng thiếu mẫu số —
# "đã NÓI mà không theo" và "đã theo nhưng thế giới không thi hành được".
# CÙNG kind với nhánh đã-theo-thi-hành-được: khác nhau ở cờ `followed` + `reason`, KHÔNG khác
# ở kind — `projections` gom mẫu số theo kind, nên tách kind ra là tách mẫu số khỏi tử số.
# ⚠ Event ở nhánh này mang `added_min=0.0`: consumer đo ĐỘ LỚN can thiệp phải dùng
# `added_min`, không dùng SỐ EVENT (xem `b0-A` trong advice_bridge.check_shift_extend).
_SPOKEN_OUTCOME_KIND = {
    "shift_extend": "advice_shift_extend",
    "rest_window": "advice_rest_window",
}


# D-M3-05: phân phối nghỉ ngắn của bản năng — literal cũ `uniform(20, 45)` nâng thành hằng
# để guardrail tầng 5 DẪN XUẤT ngưỡng break từ cùng nguồn sự thật (đổi phân phối nghỉ mà
# không căn lại ngưỡng ⇒ test T7 đỏ, không đổi nghĩa im lặng).
REST_MIN_MINUTES, REST_MAX_MINUTES = 20.0, 45.0


@dataclass
class Event:
    t_min: float
    actor_id: int
    kind: str
    cell: str = ""
    detail: dict = field(default_factory=dict)
    # ĐA-05 Cycle W (chốt Cường: "sim để RAM, chỉ thêm run_id"): identity deterministic
    # của run (runner.derive_run_id) — vũ trụ song song A/B cùng seed phân biệt được,
    # lifecycle event export/join được. "" = World tạo tay ngoài runner (test cũ).
    run_id: str = ""


class World:
    def __init__(self, grid: Grid, cfg: Config, policy: PolicyBundle, orders: list, actors: list[Actor],
                 seed: int, environment=None, congestion=None, run_id: str = ""):
        self.grid = grid
        self.cfg = cfg
        self.run_id = run_id  # ĐA-05: identity deterministic của run — stamp vào mọi Event
        self.policy = policy
        self.orders = orders
        self.actors = {a.actor_id: a for a in actors}
        self.seed = seed
        self.envctx = environment  # EnvironmentContext | None
        self.congestion = congestion  # CongestionField | None (spatiotemporal)
        # traj: waypoint (t_min, actor_id, lat, lon, state) tại mọi transition — fallback/debug
        self.traj: list[tuple] = []
        # segments: mỗi hoạt động (enroute/on_trip/relocate/charge/rest) với t0/t1/from/to CHÍNH XÁC
        # → nền cho Gantt + TripsLayer (idle = khoảng trống giữa các segment).
        self.segments: list[dict] = []
        self.env = simpy.Environment()
        self.events: list[Event] = []
        self.speed_cfg = cfg.get("speed_kmh")
        self.disp_cfg = cfg.get("dispatcher")
        self.veh = cfg.get("vehicle")
        self.detour = float(cfg.get("demand.detour_factor", 1.3))  # A4
        # SIM-XANH Phase 1: hệ số đường THẬT theo cặp cell (OSRM, cache offline).
        # None (routing.enabled=false / thiếu file) → mọi chỗ rơi về detour hằng — hành vi
        # y hệt trước SIM-XANH (cổng an toàn, có test).
        from .geo import load_road_matrix
        self.road = load_road_matrix(cfg, grid)
        bcfg = cfg.get("behavior", {})
        # B4: tên cũ accept_cost_* gây hiểu nhầm là TIỀN — đây là disutility cảm nhận
        # (behavior.py đã đổi tên hàm từ Cycle P; nay config/reader đồng bộ).
        self.pickup_disutility_km = float(bcfg.get("pickup_disutility_vnd_per_km", 3000.0))
        self.accept_center = float(bcfg.get("accept_logit_center_vnd", 6000.0))
        self.accept_scale = float(bcfg.get("accept_logit_scale_vnd", 8000.0))
        # SIM-1 fix C: huỷ SAU KHI nhận (khách bom/khách huỷ/sự cố). Sim cũ hoàn thành
        # 99.6% cuốc đã nhận — "quá sạch" so thực tế (~95%). Xảy ra khi tài xế ĐANG
        # trên đường đón (chưa gặp khách) → tốn thời gian + pin, KHÔNG có doanh thu.
        self.cancel_after_accept = float(bcfg.get("cancel_after_accept_rate", 0.05))

        # RNG stream riêng cho hành vi actor (nền CRN: ngoại sinh đã ở orders)
        self.rng = np.random.default_rng(seed ^ 0xBEEF)
        # SIM-XANH P2: stream RIÊNG cho rating — chèn vào stream hành vi sẽ dịch chuỗi
        # ngẫu nhiên và làm trôi TOÀN BỘ hiệu chỉnh SIM-1/P1 (bài học decide_accept).
        self.rng_rating = np.random.default_rng(seed ^ 0x5A7E5)
        rcfg2 = cfg.get("rating", {}) or {}
        self.rating_p = float(rcfg2.get("p_rated", 0.75))
        self.rating_p5 = dict(rcfg2.get("p5_by_archetype", {}) or {})
        self.rating_p4s = float(rcfg2.get("p4_star", 0.75))
        # SIM-XANH P2: chương trình tân binh + mission (số PROXY/MOCK có nhãn trong config)
        ncfg = cfg.get("newbie_program", {}) or {}
        self.newbie = ncfg if ncfg.get("enabled", False) else None
        mcfg = cfg.get("missions", {}) or {}
        self.mission_catalog = list(mcfg.get("daily_catalog", []) or [])             if mcfg.get("enabled", False) else []

        # SIM-3: cầu nối advice→action. Mặc định TẮT ⇒ World A (tự làm) không đổi gì.
        from .advice_bridge import AdviceActionBridge
        self.advice = AdviceActionBridge(cfg, policy, seed)
        # T-045b (Cycle P): tham số CHI PHÍ, mặc định 0 ⇒ sổ chi phí luôn 0, hành vi y hệt.
        # Nguồn số cho sweep: research/economics/driver-cost-structure-2026.md (swap Platform
        # = 0đ official tới 31/03/2029; sạc nhà 70–93đ/km; sau ưu đãi 150đ/km).
        self.swap_fee_vnd = int(self.veh.get("swap_fee_vnd", 0) or 0)
        self.cash_cost_km = float(self.veh.get("cash_cost_vnd_per_km", 0) or 0)
        # Cycle P/①: policy có hạn hiệu lực (nếu meta khai) — cảnh báo FAIL-LOUD, không im lặng.
        if self.advice.policy_valid_today is False:
            self.log(-1, "policy_outside_validity", "",
                     effective_from=self.advice.policy.effective_from,
                     effective_to=self.advice.policy.effective_to)

        # đơn mở theo thời điểm — dùng con trỏ
        self.orders_sorted = sorted(orders, key=lambda o: (o.t_min, o.order_id))
        self._order_ptr = 0
        self.open_orders: dict[int, object] = {}     # order_id -> Order
        self.order_open_since: dict[int, float] = {}
        # M0-5: order lifecycle state machine — mỗi đơn đúng 1 terminal state.
        # CREATED → OPEN → MATCHED → PICKED_UP → COMPLETED | EXPIRED | CENSORED_END_OF_RUN
        self.order_states: dict[int, tuple[str, float]] = {
            o.order_id: ("CREATED", o.t_min) for o in orders}
        # M0-2: offer history (order_id, actor_id) -> t phút lần chào gần nhất (cooldown)
        self.offer_history: dict[tuple[int, int], float] = {}
        self.offer_cooldown = float(cfg.get("dispatcher.offer_cooldown_min", 10.0))
        # M0-4: mốc tích lũy online_min per-actor (flush được lúc censor cuối ngày)
        self._last_accrual: dict[int, float] = {}

        # trạm
        self.stations: list[Station] = self._build_stations()
        self.station_by_id = {s.node_id: s for s in self.stations}

        self.metrics_start = float(cfg.get("time.start_min")) + float(cfg.get("time.warmup_min"))
        self.end_min = float(cfg.get("time.end_min"))

        # M0-3: expected demand field TỪ CONFIG (không phải realized trace của run —
        # tránh future-information leak). Nền cho "kinh nghiệm cá nhân" của actor.
        from .demand import expected_demand_field
        self.demand_field: dict[int, dict[str, float]] = expected_demand_field(grid, cfg)
        # M0-4: belief cache per (actor_id, hour) — sample nhiễu MỘT LẦN rồi giữ ổn định
        # trong ngày (không resample mỗi idle-check). Key deterministic, không phụ thuộc
        # thứ tự set-iteration (đã prove PYTHONHASHSEED làm lệch metrics cross-process).
        self._belief_cache: dict[tuple[int, int], dict[str, float]] = {}

        # T-045a b3 — kênh VỊ TRÍ (S4 batch tick). CHỈ dựng khi bật: cờ OFF phải cho trace
        # y hệt config không có cờ, từng bit (test canh). `standby_plan` là bảng gán hiện
        # hành {actor_id: cell}, do `_standby_planner` ghi mỗi bucket; vòng idle chỉ ĐỌC.
        self.standby_plan: dict[int, str] = {}
        # ĐA-05: decision_id của phân công standby — sinh MỘT lần lúc GÁN (bucket của
        # planner tick), dùng lại lúc follow để hai event join được dù khác bucket.
        self.standby_decision: dict[int, str] = {}
        self.market = None
        if self.advice.enabled and self.advice.positioning_overrides != "off":
            from .market_state import MarketStateProducer
            self.market = MarketStateProducer(
                self, bucket_min=self.advice.bucket_min,
                supply_available=self.advice.market_supply_available)

    def _build_stations(self) -> list[Station]:
        slots = int(self.cfg.get("station.slots"))
        ready = float(self.cfg.get("station.ready_soc_pct"))
        out = []
        for s in self.grid.stations:
            batteries = [BatteryInStation(soc_pct=100.0, ready_at_min=0.0) for _ in range(slots - 1)]
            out.append(Station(node_id=s.node_id, cell=s.cell, lat=s.lat, lon=s.lon,
                               slots=slots, ready_soc_pct=ready, batteries=batteries))
        return out

    def log(self, actor_id: int, kind: str, cell: str = "", **detail):
        self.events.append(Event(round(self.env.now, 3), actor_id, kind, cell, detail,
                                 self.run_id))

    def _decision_id(self, actor_id: int, channel: str, now: float,
                     bucket_min: float | None = None) -> str:
        """decision_id deterministic của sim (ĐA-05) — theo công thức spec
        `adherence-measurement.md` §"advice_id": (driver, channel, bucket).

        Cùng tick advice_given/followed/suppressed ⇒ cùng bucket ⇒ CÙNG decision (join
        được); re-check mỗi tick trong cùng bucket gộp thành MỘT quyết định logic.

        Bucket KHÔNG hardcode 30': planner chạy theo `advice.bucket_min`, nên hạ nó
        xuống 15 làm hai phân công KHÁC NHAU rơi vào cùng bucket 30' ⇒ chung
        decision_id ⇒ event bị nuốt (review đối kháng đo được 23 event mất ở
        `bucket_min=15`). Kênh vị trí vì thế dùng đúng bucket của planner."""
        from gsm_core.lifecycle.cadence import decision_bucket
        return f"slth-{self.run_id}-{actor_id}-{channel}-{decision_bucket(now, bucket_min)}"

    def _order_transition(self, oid: int, state: str) -> None:
        """M0-5: ghi chuyển trạng thái đơn (terminal chỉ ghi 1 lần — không ghi đè)."""
        cur = self.order_states.get(oid, ("CREATED", 0.0))[0]
        if cur in ("COMPLETED", "EXPIRED", "CENSORED_END_OF_RUN", "CANCELLED_AFTER_ACCEPT"):
            return  # terminal là bất biến
        self.order_states[oid] = (state, round(self.env.now, 3))

    def _cell_point(self, cell: str) -> tuple[float, float]:
        """Toạ độ đại diện của cell (centroid) — dùng cho endpoint relocate/charge/online."""
        return self.grid.cell_centroid.get(cell) or (0.0, 0.0)

    def _set_pos(self, actor: Actor, lat: float, lon: float) -> None:
        """M0-10: movement ATOMIC — lat/lon và H3 cell cập nhật cùng nhau.
        Caller KHÔNG tự gán actor.cell nữa (một nguồn sự thật duy nhất)."""
        actor.lat, actor.lon = lat, lon
        actor.cell = h3.latlng_to_cell(lat, lon, self.grid.res)
        self.traj.append((round(self.env.now, 3), actor.actor_id, lat, lon, actor.state.value))

    def _seg(self, actor_id: int, t0: float, t1: float, kind: str,
             frm: tuple, to: tuple, **meta) -> None:
        """Ghi 1 đoạn hoạt động (từ frm=(lat,lon) tới to=(lat,lon))."""
        self.segments.append({
            "actor_id": actor_id, "t0": round(t0, 3), "t1": round(t1, 3), "kind": kind,
            "from_lat": frm[0], "from_lon": frm[1], "to_lat": to[0], "to_lon": to[1], **meta,
        })

    def _congestion_r(self, cell: str | None, hour: int) -> float:
        if self.congestion is None or cell is None:
            return 0.0
        return self.congestion.r(cell, hour)

    def _eff_speed(self, hour: int, cell: str | None = None) -> float:
        """Tốc độ hiệu dụng = base(giờ) × survival(mưa × tắc cục bộ cell), có sàn.

        Congestion spatiotemporal suy từ mật độ đơn theo (cell, giờ). Tắt (congestion=None
        hoặc cell=None) + không env → trả base (baseline bất biến)."""
        base = _speed_kmh(hour, self.speed_cfg)
        r_cong = self._congestion_r(cell, hour)
        if self.envctx is not None:
            # env.speed_factor = (1-r_rain)·(1-r_cong) survival product
            v = base * self.envctx.speed_factor(self.env.now, r_cong)
            return max(self.envctx.v_floor, v)
        if r_cong <= 0.0:
            return base
        return max(7.0, base * (1.0 - min(0.95, r_cong)))

    def _dfac(self, a: str | None, b: str | None) -> float:
        """Hệ số đường cho cặp cell (a→b): OSRM nếu có, detour hằng nếu không."""
        if self.road is None or a is None or b is None:
            return self.detour
        return self.road.factor(a, b, self.detour)

    def _travel_min(self, dist_km: float, hour: int, cell: str | None = None,
                    fac: float | None = None) -> float:
        """Thời gian di chuyển = quãng đường thực (× hệ số đường) / tốc độ hiệu dụng.

        SIM-XANH: `fac` là hệ số đường THEO CẶP CELL (`_dfac`); None → detour hằng (đường cũ).
        """
        f = self.detour if fac is None else fac
        return (dist_km * f) / self._eff_speed(hour, cell) * 60.0

    def _pct_per_km(self, actor: Actor) -> float:
        """Tiêu pin/km, điều chỉnh theo nhiệt độ (range giảm → tiêu hao tăng)."""
        base = float(self.veh["swap_consume_pct_per_km"] if actor.fleet == FleetType.SWAP
                     else self.veh["charge_consume_pct_per_km"])
        if self.envctx is None:
            return base
        return base / max(0.5, self.envctx.range_factor(self.env.now))

    # --- Processes ---

    def run(self):
        self.env.process(self._dispatcher_proc())
        self.env.process(self._order_expiry_proc())
        if self.market is not None:
            self.env.process(self._standby_planner())
        if bool(self.cfg.get("probe.wait_stats", False)):
            self.env.process(self._wait_stats_probe())
        for a in self.actors.values():
            self.env.process(self._actor_proc(a))
        self.env.run(until=self.end_min)
        self._settle_end_of_run()
        return self.events

    def _wait_stats_probe(self):
        """E10b §4.7 — observer LOG-ONLY cho control-run: per-cell `(n_idle, median streak)`
        + streak per-actor (biến này không nằm trong event nào — tái dựng từ timeline sẽ là
        đường recompute thứ hai dễ sai). 0 RNG, 0 ghi state ⇒ fingerprint bật/tắt cờ phải
        IDENTICAL (test T18). WAIT-share/precision tính hậu-kiểm từ event log, không ở đây."""
        from .market_state import count_idle_wait
        b = float(self.advice.bucket_min)
        while self.env.now < self.end_min:
            stats = count_idle_wait(self.actors.values())
            self.log(-1, "probe_wait_stats", "",
                     cells={c: [n, round(med, 3)] for c, (n, med) in sorted(stats.items())},
                     streaks={str(a.actor_id): [a.cell, round(float(a.idle_streak_min), 1)]
                              for a in self.actors.values()
                              if a.state == ActorState.IDLE})
            yield self.env.timeout(b)

    # --- T-045a b3: batch tick S4 — gán tài xế rỗi vào ô CÒN TRẦN, mỗi bucket một lần ---

    def _standby_planner(self):
        """Kiến trúc Cường chốt (2026-07-28): gán theo LÔ đúng bản chất S4 (Hungarian), không
        greedy trừ dần — giữ tính gán tối ưu và so được với phân bổ tập trung (ĐA-09 §2.2).

        Trần do `MarketStateView` tính (đã trừ cung tại chỗ + CUNG ĐANG TỚI + advice vừa phát);
        S4 chỉ THI HÀNH — không có chỗ thứ hai tự tính trần (mẫu lỗi T-046).

        Adherence rút MỘT LẦN tại thời điểm gán (`standby_follow_draw`) — không re-roll mỗi
        vòng poll (lỗi D-SIM-14). Người không nghe: không vào plan, không ai nhắc lại trong
        bucket đó.
        """
        from gsm_core.features.allocation import derive_allocation_input
        from gsm_core.solvers import capacity_alloc
        from .advice_bridge import _iso

        b = float(self.advice.bucket_min)
        while self.env.now < self.end_min:
            now = self.env.now
            view = self.market.view(now)
            if not (view["positioning_allowed"] and view["ranked_cells"]):
                yield self.env.timeout(b)
                continue
            ranked = view["ranked_cells"]
            cap_left = {c: int(view["cells"][c]["capacity_left"] or 0) for c in ranked}

            # E10b (spec e10-advisor-noisy §4): trigger `wait` — ứng viên theo THỜI GIAN CHỜ
            # của Ô thay vì cap_left==0. Nhánh `capacity` (default) đi đúng đường cũ từng
            # ký tự: fired rỗng, `ranked_eff` là CHÍNH `ranked` (test fingerprint canh).
            wait_mode = self.advice.positioning_trigger == "wait"
            if wait_mode:
                from .market_state import count_idle_wait, wait_fired_cells
                wait_T = self.advice.positioning_wait_threshold_min
                fired = wait_fired_cells(count_idle_wait(self.actors.values()),
                                         wait_T, self.advice.positioning_wait_min_idle)
                # ZONE-VETO §4.4 — thuộc ĐỊNH NGHĨA trigger, không phải tuỳ chọn: ô fired bị
                # loại khỏi tập ĐÍCH của batch. Vì ứng viên chỉ sinh từ ô fired, own-cell ∉
                # zones ⇒ Hungarian KHÔNG THỂ stagger về chỗ đứng (capacity_alloc.py cost
                # lệch target = pen+10, không phải LARGE — lỗ tự-gán là thật, test T14);
                # và ô fired không nhận người vào (đóng nguồn-đích chồng nhau cùng batch).
                ranked_eff = [c for c in ranked if c not in fired]
                if not ranked_eff:
                    # không còn đích hợp lệ ⇒ KHÔNG làm ứng viên: không rút coin, không
                    # đếm decided (test T15)
                    yield self.env.timeout(b)
                    continue
            else:
                fired, ranked_eff = set(), ranked

            cands = []
            for a in self.actors.values():
                if a.state != ActorState.IDLE or not self.advice.covers(a):
                    continue
                if a.actor_id in self.standby_plan:
                    continue                     # đã có phân công còn hiệu lực
                if wait_mode:
                    if a.cell not in fired:
                        continue                 # nguồn = CHỈ ô đã fire (W > T ∧ n ≥ n_min)
                    if a.idle_streak_min < wait_T:
                        continue                 # cổng cá nhân §4.3: không kéo người vừa tới
                                                 # (ô fire {50′,40′,5′} không được kéo người 5′)
                elif cap_left.get(a.cell, 0) > 0:
                    continue                     # đang đứng ở ô CÒN TRẦN — kéo đi là churn
                # ĐA-04: positioning nằm NGOÀI nhịp theo mặc định (kênh dương SIG duy nhất).
                # Chỉ khi bật cờ đo `count_positioning_in_budget` nó mới chịu cooldown/ngân
                # sách. Nhánh mặc định phải đi đúng đường cũ — nếu không, mọi số A/B đã đo
                # với positioning sẽ đổi âm thầm.
                if (self.advice.cadence_counts_positioning
                        and not self.advice.cadence_allows(a, "positioning", now)):
                    continue
                # preferred = ô còn trần GẦN NHẤT (đỡ km rỗng — veto b4); tie-break theo tên
                # ô để deterministic. Hungarian tự stagger phần tranh chấp.
                pref = min(ranked_eff, key=lambda c: (cell_distance_km(self.grid, a.cell, c), c))
                # priority_soc của S4: giá trị THẤP được xếp trước. Đảo SOC để ưu tiên người
                # NHIỀU pin (đi xa được); người ít pin không nên bị kéo chạy rỗng.
                cands.append({"driver_id": f"d-{a.actor_id}", "advice_kind": "standby_zone",
                              "target": pref, "priority_soc": round(100.0 - a.soc_pct, 1)})
            if not cands:
                yield self.env.timeout(b)
                continue

            zones = [{"zone": c, "capacity": cap_left[c]} for c in ranked_eff]
            ai = derive_allocation_input(_iso(now), cands, [], zones,
                                         bucket_min=int(b))
            sol = capacity_alloc.solve(ai)["solution"]
            # E10b §4.4: bất biến zone-veto — không ai bị gán VÀO ô fired (kỳ vọng cấu trúc:
            # fired ∉ zones ⇒ Hungarian không có slot ở đó; assert để thủng là nổ, không im)
            assert all(al["assigned_target"] not in fired for al in sol["allocations"]),                 "zone-veto thủng: có người bị gán vào ô fired"

            n_follow = 0
            per_cell: dict[str, int] = {}
            flags_by_cell: dict[str, list] = {}
            # ĐA-05: MẪU SỐ của kênh vị trí = người ĐƯỢC GÁN (kể cả người không theo).
            # Không ghi lại đây thì lifecycle chỉ thấy `standby_followed` ⇒ adherence
            # luôn 100% (đo được 36/36 trong khi sự thật 42/86). Ghi vào detail của
            # event SẴN CÓ, không thêm kind mới ⇒ mọi consumer đếm theo kind giữ nguyên số.
            assigned_by_cell: dict[str, list] = {}
            dids_by_cell: dict[str, dict] = {}
            for al in sol["allocations"]:
                cell = al["assigned_target"]
                per_cell[cell] = per_cell.get(cell, 0) + 1
                flags_by_cell.setdefault(cell, al.get("safety_flags") or [])
                aid = int(al["driver_id"][2:])
                did = self._decision_id(aid, "positioning", now, bucket_min=b)
                assigned_by_cell.setdefault(cell, []).append(aid)
                dids_by_cell.setdefault(cell, {})[str(aid)] = did
                # "Đã nói" = advisor đưa lời khuyên, KHÔNG phụ thuộc tài xế có theo hay không
                # (ngân sách là ngân sách CHÚ Ý của người nghe). Chỉ ghi khi cờ đo bật.
                if self.advice.cadence_counts_positioning:
                    self.advice.cadence_note_spoken(self.actors[aid], "positioning", now)
                if self.advice.standby_follow_draw(self.actors[aid], now, cell):
                    self.standby_plan[aid] = cell
                    # decision sinh tại lúc GÁN — follow (có thể ở bucket sau) dùng lại
                    self.standby_decision[aid] = did
                    self.market.pending_targets[aid] = cell   # trừ trần NGAY cho người hỏi sau
                    n_follow += 1
            for cell in sorted(per_cell):
                self.log(-1, "standby_alloc", cell, n_assigned=per_cell[cell],
                         capacity_left=cap_left[cell], safety_flags=flags_by_cell[cell],
                         assigned_ids=sorted(assigned_by_cell.get(cell, [])),
                         decision_ids=dids_by_cell.get(cell, {}))
            self.log(-1, "standby_planner", "",
                     n_candidates=len(cands), n_assigned=sol["n_assigned"],
                     n_unassigned=len(sol["unassigned"]), n_follow=n_follow,
                     herding_avoided=sol["herding_avoided"],
                     # E10b: chỉ wait-mode mang thêm khoá (capacity mode giữ detail cũ
                     # NGUYÊN VẸN — neutrality từng bit); fired ghi lại để diff/volume §5.4
                     # và test tự kiểm "không gán vào ô fired" đọc được từ event log
                     **({"n_fired_cells": len(fired), "fired_cells": sorted(fired)}
                        if wait_mode else {}))
            yield self.env.timeout(b)

    def _settle_end_of_run(self):
        """M0-6 + M0-4: chốt cuối ngày — flush time cho actor còn bận, censor đơn in-flight,
        rồi mới tính thưởng ngày. SimPy bỏ rơi timeout đang treo nên phải reconcile tường minh."""
        # T-045b: chốt chi phí km MỘT lần cuối ngày (mặc định cash_cost = 0 ⇒ +0, bit-identical)
        if self.cash_cost_km:
            for a in self.actors.values():
                a.cost_vnd += int(round(a.km_driven * self.cash_cost_km))
        # 1. M0-4: actor chưa offline → cộng nốt đoạn [last_accrual, end_min] vào online_min
        for a in self.actors.values():
            if a.state == ActorState.OFFLINE:
                continue
            last = self._last_accrual.get(a.actor_id)
            if last is not None and self.end_min > last:
                a.online_min += self.end_min - last
                self._last_accrual[a.actor_id] = self.end_min
            # actor đang giữa hoạt động (không idle) → đánh dấu censored để metrics/UI biết
            if a.state in (ActorState.ENROUTE, ActorState.ON_TRIP, ActorState.CHARGING, ActorState.REST):
                self.log(a.actor_id, "censored_end_of_run", a.cell, state=a.state.value)
        # 2. M0-6/M0-5: đơn không terminal (đang matched/picked_up hoặc còn open) → CENSORED
        for oid, (state, _t) in list(self.order_states.items()):
            if state in ("COMPLETED", "EXPIRED"):
                continue
            if state in ("MATCHED", "PICKED_UP"):
                self.order_states[oid] = ("CENSORED_END_OF_RUN", self.end_min)
                self.log(-1, "order_censored", order_id=oid, last_state=state)
            elif state in ("CREATED", "OPEN"):
                # đơn chưa từng match tới hết ngày = hết hạn theo nghĩa vận hành
                self.order_states[oid] = ("EXPIRED", self.end_min)
                self.log(-1, "order_expired", order_id=oid, reason="end_of_run")
        # 3. thưởng ngày cho actor vẫn online lúc hết run (chưa qua nhánh end_shift)
        for a in self.actors.values():
            if a.state != ActorState.OFFLINE:
                self._newbie_settle(a)     # SIM-XANH P2: quyết toán tân binh trước chốt sổ
                bonus = self.policy.day_bonus(a.points, a.acceptance_rate, a.completion_rate)
                a.payout_vnd += bonus
                self.log(a.actor_id, "day_end_settle", a.cell,
                         trips=a.trips_done, payout=a.payout_vnd, points=a.points, day_bonus=bonus)


    def _newbie_settle(self, actor: Actor) -> None:
        """SIM-XANH P2 — quyết toán TÂN BINH cuối ngày (gọi ở CẢ end_shift lẫn censor).

        Cấu trúc THẬT (greensm.com, Q-01 fetch 2026-07-26); SỐ TIỀN là PROXY có nhãn ở
        config. Hai lớp:
        1. **Bảo lãnh doanh thu 90 ngày** (mức NGÀY): gross < sàn và online đủ chuyên cần
           → bù phần thiếu. Điều kiện online chống lạm dụng (không vận doanh không bù).
        2. **Mốc ≥50 cuốc trong 7 ngày đầu** (mức TÍCH LUỸ): đọc lịch sử các ngày ĐÃ XONG
           từ DriverMemory (qua bridge, không rò tương lai) + hôm nay; trả MỘT lần.
        """
        if not self.newbie or actor.tenure_days > int(self.newbie["tenure_newbie_max_days"]):
            return
        # 1) bảo lãnh doanh thu ngày
        if actor.tenure_days <= int(self.newbie["guarantee_days"]):
            floor = int(self.newbie["guarantee_gross_floor_vnd"])
            min_online = float(self.newbie["guarantee_min_online_h"]) * 60.0
            if actor.online_min >= min_online and actor.gross_vnd < floor:
                topup = int(round((floor - actor.gross_vnd)
                                  * self.policy.driver_share))   # bù phần TÀI XẾ của khoảng thiếu
                actor.newbie_topup_vnd += topup
                actor.payout_vnd += topup
                self.log(actor.actor_id, "newbie_guarantee_topup", actor.cell,
                         tenure_days=actor.tenure_days, gross_day=actor.gross_vnd,
                         floor_vnd=floor, topup_vnd=topup)
        # 2) mốc 50 cuốc / 7 ngày đầu — cần lịch sử (multi-day); single-day chỉ xét hôm nay
        if actor.tenure_days <= 7:
            mem = (self.advice.memory or {}).get(actor.actor_id)
            prior = sum(mem.trips_hist[-(actor.tenure_days - 1):]) if (
                mem and actor.tenure_days > 1) else 0
            already = bool(getattr(mem, "newbie_week1_paid", False)) if mem else False
            total7 = prior + actor.trips_done
            if not already and total7 >= int(self.newbie["first_week_trip_target"]):
                bonus = int(self.newbie["first_week_bonus_vnd"])
                actor.payout_vnd += bonus
                self.log(actor.actor_id, "newbie_week1_bonus", actor.cell,
                         tenure_days=actor.tenure_days, trips_7d=total7, bonus_vnd=bonus)
                if mem:
                    mem.newbie_week1_paid = True   # ghi SỰ KIỆN đã xong tại settle — không rò tương lai

    def _inject_orders(self):
        """Đưa các đơn tới thời điểm hiện tại vào open pool."""
        now = self.env.now
        while self._order_ptr < len(self.orders_sorted) and self.orders_sorted[self._order_ptr].t_min <= now:
            o = self.orders_sorted[self._order_ptr]
            self.open_orders[o.order_id] = o
            self.order_open_since[o.order_id] = now
            self._order_transition(o.order_id, "OPEN")
            self._order_ptr += 1

    def _order_expiry_proc(self):
        """Khách hủy khi chưa match quá patience (per-order, exogenous — CRN-safe)."""
        while True:
            yield self.env.timeout(0.5)  # quét mỗi 30s-sim (đơn vị thời gian = phút)
            now = self.env.now
            expired = [oid for oid, t0 in self.order_open_since.items()
                       if oid in self.open_orders
                       and (now - t0) > self.open_orders[oid].patience_min]
            for oid in expired:
                self.open_orders.pop(oid, None)
                self.order_open_since.pop(oid, None)
                self._order_transition(oid, "EXPIRED")
                self.log(-1, "order_expired", order_id=oid)

    def _dispatcher_proc(self):
        tick_min = float(self.cfg.get("time.dispatch_tick_s")) / 60.0
        while True:
            yield self.env.timeout(tick_min)
            self._inject_orders()
            if not self.open_orders:
                continue
            idle = [a for a in self.actors.values() if a.state == ActorState.IDLE]
            if not idle:
                continue
            hour = int(self.env.now // 60) % 24
            assigns = match_batch(list(self.open_orders.values()), idle, self.grid, hour,
                                  self.speed_cfg, self.disp_cfg,
                                  speed_fn=lambda cell, h: self._eff_speed(h, cell), detour=self.detour,
                                  factor_fn=self._dfac if self.road else None)
            for asg in assigns:
                order = self.open_orders.get(asg.order_id)
                actor = self.actors.get(asg.actor_id)
                if order is None or actor is None or actor.state != ActorState.IDLE:
                    continue
                # M0-2: không chào lại cùng (đơn, tài xế) trong cooldown sau decline/SOC-fail
                pair = (asg.order_id, asg.actor_id)
                t_last = self.offer_history.get(pair)
                if t_last is not None and (self.env.now - t_last) < self.offer_cooldown:
                    continue
                self.offer_history[pair] = self.env.now
                actor.orders_offered += 1
                actor.idle_streak_min = 0.0   # T-045d: được CHÀO = bằng chứng ở đây có cầu
                # SOC đủ hoàn thành? (pickup + trip, quãng đường thực theo hệ số TỪNG chặng)
                total_km = (asg.pickup_dist_km * self._dfac(actor.cell, order.pickup_cell)
                            + order.dist_km * self._dfac(order.pickup_cell, order.drop_cell))
                enough = actor.soc_pct - total_km * self._pct_per_km(actor) > 8.0
                forced = actor.acceptance_rate < 0.5 and actor.orders_offered > 5
                if not enough:
                    # SIM-1: KHÔNG còn tính là "cancelled" — tài xế chưa hề nhận đơn.
                    # `orders_cancelled` từ nay CHỈ đếm huỷ SAU khi nhận (khớp nghĩa cột
                    # `cancelled_count` trong `driver_statistic_daily`).
                    actor.orders_soc_skipped += 1
                    # SIM-2: trước đây nhánh này CHỈ tăng counter ⇒ vô hình trên timeline.
                    # Không giải thích được vì sao tài xế "biến mất" khỏi thị trường một lúc.
                    self.log(actor.actor_id, "order_skipped_soc", actor.cell,
                             order_id=order.order_id, soc_pct=round(actor.soc_pct, 1),
                             need_km=round(total_km, 2))
                    continue
                dec = decide_accept(actor, order.gross_vnd, asg.pickup_dist_km, forced, self.rng,
                                    self.pickup_disutility_km, self.accept_center, self.accept_scale)
                if not dec.accepted:
                    # SIM-2: ghi ĐỦ căn cứ — trả lời được "vì sao từ chối cuốc NÀY?"
                    self.log(actor.actor_id, "order_declined", actor.cell,
                             order_id=order.order_id, reason=dec.reason,
                             net_vnd=round(dec.net_vnd), pickup_km=round(asg.pickup_dist_km, 2),
                             gross_vnd=order.gross_vnd, p_accept=round(dec.p_accept, 4))
                    continue
                # nhận đơn
                actor.orders_accepted += 1
                self.open_orders.pop(order.order_id, None)
                self.order_open_since.pop(order.order_id, None)
                self._order_transition(order.order_id, "MATCHED")
                # SIM-2: ghi cùng bộ số như lúc từ chối ⇒ so sánh được cuốc NHẬN vs cuốc BỎ
                self.log(actor.actor_id, "order_matched", actor.cell, order_id=order.order_id,
                         net_vnd=round(dec.net_vnd), pickup_km=round(asg.pickup_dist_km, 2),
                         gross_vnd=order.gross_vnd, p_accept=round(dec.p_accept, 4),
                         reason=dec.reason)
                # ENROUTE_EXEMPT (T-045a b2): đi ĐÓN KHÁCH thì KHÔNG đặt `enroute_cell`.
                # Đích thật của chuyến này là điểm TRẢ khách, cách đây một quãng bất định và có
                # thể vài chục phút. Coi tài xế đang chở khách là "cung sắp tới ô Y" sẽ thổi
                # phồng cung ở khắp nơi và làm advisor thôi khuyên tới những ô thực ra đang
                # thiếu người. Giới hạn này có nhãn, không phải bỏ sót — xem
                # `tests/test_market_state_sim_producer.py::test_every_enroute_transition_sets_a_target`.
                actor.state = ActorState.ENROUTE
                self.env.process(self._serve_trip(actor, order, asg))

    def _serve_trip(self, actor: Actor, order, asg):
        hour = int(self.env.now // 60) % 24
        pct_per_km = self._pct_per_km(actor)
        origin_cell = actor.cell
        t_assign = self.env.now
        frm = (actor.lat, actor.lon)   # vị trí trước khi đi đón
        # SIM-XANH: hệ số đường THẬT theo từng chặng (OSRM); fallback detour hằng
        fac_pick = self._dfac(origin_cell, order.pickup_cell)
        fac_trip = self._dfac(order.pickup_cell, order.drop_cell)
        pickup_min = self._travel_min(asg.pickup_dist_km, hour, origin_cell, fac=fac_pick)

        # --- SIM-1 fix C: huỷ sau khi nhận, xảy ra GIỮA ĐƯỜNG ĐI ĐÓN ---
        # Quyết định TRƯỚC khi timeout (không nhìn tương lai: chỉ dùng rng, không dùng
        # kết quả cuốc). Tài xế đã đi được một phần quãng đón thì đơn bị huỷ.
        if self.rng.random() < self.cancel_after_accept:
            frac = float(self.rng.uniform(0.3, 1.0))    # đã đi được 30-100% quãng đón
            spent = pickup_min * frac
            yield self.env.timeout(spent)
            actor.consume_soc(asg.pickup_dist_km * fac_pick * frac, pct_per_km)
            actor.empty_min += spent                    # THIỆT HẠI THẬT: thời gian + pin, 0đ
            actor.orders_cancelled += 1
            lat = actor.lat + (order.pickup_lat - actor.lat) * frac
            lon = actor.lon + (order.pickup_lon - actor.lon) * frac
            self._set_pos(actor, lat, lon)
            self._seg(actor.actor_id, t_assign, self.env.now, "enroute", frm, (lat, lon),
                      order_id=order.order_id)
            self._order_transition(order.order_id, "CANCELLED_AFTER_ACCEPT")
            self.log(actor.actor_id, "order_cancelled_after_accept", actor.cell,
                     order_id=order.order_id, wasted_min=round(spent, 2))
            actor.state = ActorState.IDLE
            return

        yield self.env.timeout(pickup_min)
        actor.consume_soc(asg.pickup_dist_km * fac_pick, pct_per_km)
        actor.empty_min += pickup_min
        actor.state = ActorState.ON_TRIP
        self._set_pos(actor, order.pickup_lat, order.pickup_lon)  # vị trí = điểm đón THẬT
        self._seg(actor.actor_id, t_assign, self.env.now, "enroute", frm,
                  (order.pickup_lat, order.pickup_lon), order_id=order.order_id)
        self._order_transition(order.order_id, "PICKED_UP")
        self.log(actor.actor_id, "pickup", order.pickup_cell,
                 order_id=order.order_id, eta_min=round(pickup_min, 2))
        # chở khách
        hour = int(self.env.now // 60) % 24
        t_pickup = self.env.now
        trip_min = self._travel_min(order.dist_km, hour, order.pickup_cell, fac=fac_trip)
        yield self.env.timeout(trip_min)
        actor.occupied_min += trip_min
        actor.consume_soc(order.dist_km * fac_trip, pct_per_km)
        # kiểm tra stranded (variance): nếu SOC <= 0 giữa đường
        if actor.soc_pct <= 0.0:
            actor.stranded_count += 1
            self.log(actor.actor_id, "battery_stranded", order.drop_cell, order_id=order.order_id)
        actor.trips_done += 1
        actor.orders_completed += 1
        actor.gross_vnd += order.gross_vnd
        actor.payout_vnd += self.policy.driver_payout_from_gross(order.gross_vnd)
        actor.points += self.policy.trip_points(int(order.t_min // 60) % 24)
        # vị trí SAU CUỐC = điểm trả khách THẬT (không teleport về lõi)
        self._set_pos(actor, order.drop_lat, order.drop_lon)
        self._seg(actor.actor_id, t_pickup, self.env.now, "on_trip",
                  (order.pickup_lat, order.pickup_lon), (order.drop_lat, order.drop_lon),
                  order_id=order.order_id, gross=order.gross_vnd,
                  payout=self.policy.driver_payout_from_gross(order.gross_vnd), dist_km=order.dist_km)
        self._order_transition(order.order_id, "COMPLETED")
        self.log(actor.actor_id, "dropoff", order.drop_cell,
                 order_id=order.order_id, gross=order.gross_vnd, dist_km=order.dist_km)

        # --- SIM-XANH P2: khách CHẤM SAO sau cuốc (stream rating riêng) ---
        if self.rng_rating.random() < self.rating_p:
            p5 = float(self.rating_p5.get(actor.archetype, 0.78))
            u = self.rng_rating.random()
            if u < p5:
                stars = 5
            elif u < p5 + (1 - p5) * self.rating_p4s:
                stars = 4
            else:
                stars = int(self.rng_rating.integers(1, 4))   # 1-3★ hiếm
            actor.ratings_n += 1
            actor.ratings_sum += stars
            actor.ratings_5 += int(stars == 5)
            self.log(actor.actor_id, "trip_rated", order.drop_cell,
                     order_id=order.order_id, stars=stars)

        # --- SIM-XANH P2: tiến độ MISSION (deterministic, không RNG) ---
        done_hour = int(self.env.now // 60) % 24
        for m in self.mission_catalog:
            w = m.get("window")
            if w is not None and not (int(w[0]) <= done_hour < int(w[1])):
                continue
            mid = m["mission_id"]
            cur = actor.mission_progress.get(mid, 0)
            if cur >= int(m["target"]):
                continue                               # đã xong — thưởng chỉ MỘT lần
            actor.mission_progress[mid] = cur + 1
            if cur + 1 == int(m["target"]):
                reward = int(m["reward_vnd"])
                actor.mission_reward_vnd += reward
                actor.payout_vnd += reward
                self.log(actor.actor_id, "mission_completed", order.drop_cell,
                         mission_id=mid, reward_vnd=reward, name=m.get("name", mid))

        actor.state = ActorState.IDLE

    def _relocate_to_core(self, actor: Actor):
        """Sau cuốc trả ngoài lõi → chạy (deadhead) về cell lõi gần nhất. Là 1 đoạn di
        chuyển THẬT (tốn thời gian/pin), khởi hành TỪ điểm trả — hiện dưới dạng relocate."""
        target = None
        for r in range(1, 8):
            for c in grid_disk(actor.cell, r):
                if self.grid.is_core(c):
                    target = c
                    break
            if target:
                break
        if target is None:
            target = self.grid.core_cells[0]
        d = cell_distance_km(self.grid, actor.cell, target)
        fac = self._dfac(actor.cell, target)
        hour = int(self.env.now // 60) % 24
        pct_per_km = self._pct_per_km(actor)
        t0 = self.env.now
        frm = (actor.lat, actor.lon)
        t = self._travel_min(d, hour, actor.cell, fac=fac)
        actor.state = ActorState.ENROUTE
        actor.enroute_cell = target        # T-045a: cung ĐANG TỚI ô lõi này
        yield self.env.timeout(t)
        actor.consume_soc(d * fac, pct_per_km)
        actor.empty_min += t
        clat, clon = self._cell_point(target)
        actor.state = ActorState.IDLE
        actor.enroute_cell = None          # tới nơi ⇒ thành cung TẠI CHỖ, hết là cung đang tới
        self._set_pos(actor, clat, clon)  # M0-10: cell sync trong _set_pos
        self._seg(actor.actor_id, t0, self.env.now, "relocate", frm, (clat, clon), reason="deadhead_to_core")
        self.log(actor.actor_id, "relocate", target, reason="deadhead_to_core")

    def _actor_proc(self, actor: Actor):
        # chờ tới giờ bắt đầu ca
        if actor.shift_start_min > self.env.now:
            yield self.env.timeout(actor.shift_start_min - self.env.now)
        actor.state = ActorState.IDLE
        alat, alon = self._cell_point(actor.cell)   # vị trí xuất phát = home cell
        self._set_pos(actor, alat, alon)
        self.log(actor.actor_id, "go_online", actor.cell)
        last = self.env.now
        self._last_accrual[actor.actor_id] = last  # M0-4: cho settle cuối ngày flush đoạn bận

        # online_min = tổng span từ go_online tới offline; cộng mỗi lần ở top vòng
        # (KHÔNG reset `last` trong nhánh action — nếu không sẽ mất thời gian chờ/serve).
        while self.env.now < self.end_min:
            # nếu đang bận (enroute/on_trip/charging) → nhường, kiểm lại sau
            if actor.state in (ActorState.ENROUTE, ActorState.ON_TRIP, ActorState.CHARGING, ActorState.REST):
                yield self.env.timeout(1.0)
                continue
            if actor.state == ActorState.OFFLINE:
                break
            now = self.env.now
            actor.online_min += (now - last)  # gộp toàn bộ thời gian đã trôi (chờ + serve + charge)
            last = now
            self._last_accrual[actor.actor_id] = last  # M0-4
            # sau cuốc trả ngoài lõi → chạy về lõi (deadhead) rồi kiểm lại
            if not self.grid.is_core(actor.cell):
                yield from self._relocate_to_core(actor)
                continue
            hour = int(now // 60) % 24
            hint = self._actor_demand_hint(actor, hour)
            action, target = choose_idle_action(actor, now, self.grid, self.veh, hour, hint,
                                                self.rng, self.cfg.get("behavior", {}) or {})

            # --- SIM-3: hỏi advisor (nếu tài xế này được phủ + tới hạn) ---
            # ĐẶT SAU `choose_idle_action` CÓ CHỦ Ý: hành vi bản năng vẫn được tính (và tiêu
            # RNG) y như World A ⇒ bật advice KHÔNG dịch dòng ngẫu nhiên của actor. Advice
            # chỉ GHI ĐÈ kết quả. Đây là điều kiện để paired-seed (CRN) ở SIM-4 có nghĩa.
            # SIM-4 kênh `accept_lift`: cảnh báo tỷ lệ nhận dưới ngưỡng ĐỦ ĐIỀU KIỆN thưởng.
            # Đây là kênh giá trị nhất: `day_bonus` trả 0 khi acceptance < ngưỡng, BẤT KỂ điểm.
            gate = self.advice.check_bonus_gate(actor, now)
            if gate is not None:
                self.log(actor.actor_id, "advice_bonus_gate", actor.cell,
                         acceptance=gate.acceptance_now, threshold=gate.threshold,
                         lift=gate.lift_applied, followed=gate.followed,
                         accept_lift_total=round(actor.accept_lift, 4),
                         decision_id=self._decision_id(actor.actor_id, "accept_lift", now),
                         channel="accept_lift")

            # SIM-4 kênh `shift_extend`: hoãn kết ca khi SÁT mốc điểm (có trần)
            added = self.advice.check_shift_extend(actor, now)
            if added:
                self.log(actor.actor_id, "advice_shift_extend", actor.cell,
                         added_min=round(added, 1), points=int(actor.points),
                         new_shift_end=round(actor.shift_end_min, 1), followed=True,
                         decision_id=self._decision_id(actor.actor_id, "shift_extend", now),
                         channel="shift_extend")

            adv = self.advice.consult(actor, now, self._actor_demand_hint, actor.shift_end_min)
            if adv is not None:
                # ĐA-05: cùng tick ⇒ given/followed/suppressed chia sẻ MỘT decision_id
                did = self._decision_id(actor.actor_id, "shift_plan", now)
                self.log(actor.actor_id, "advice_given", actor.cell,
                         solver_action=adv.solver_action, adherence=adv.adherence,
                         followed=adv.followed, instinct_action=action.value,
                         plan_next=adv.plan_next_action, reason=adv.reason,
                         decision_id=did, channel="shift_plan")
                if adv.followed and adv.mapped_action is not None:
                    # BUG-ADVICE-OVERRIDE (UPDATE-082): `REST` của S2 nghĩa là *"khung này
                    # ĐỪNG ở trạng thái ONLINE kiếm tiền"*. Nhưng `go_swap`/`go_charge`/
                    # `relocate` **vốn đã KHÔNG PHẢI** ONLINE kiếm tiền — chúng là hành động
                    # chuyển tiếp mà DP **không hề mô hình hoá** (action space của solver chỉ
                    # có ONLINE/REST/SWAP/END, thô hơn của actor).
                    #
                    # Ghi đè chúng bằng REST vì thế vừa THỪA (ý định của DP đã được thoả) vừa
                    # PHÁ HOẠI: đo được 6 seed — 47 lần ép tài xế đang đi ĐỔI PIN quay ra nghỉ,
                    # 45 lần ép tài xế đang DỊCH tới khu đông khách quay ra nghỉ. Đó là
                    # **92/166 = 55%** tổng số can thiệp của advisor.
                    if (self.advice.rest_only_overrides_wait
                            and adv.mapped_action == IdleAction.REST
                            and action in (IdleAction.GO_SWAP, IdleAction.GO_CHARGE,
                                           IdleAction.RELOCATE)):
                        self.log(actor.actor_id, "advice_suppressed", actor.cell,
                                 solver_action=adv.solver_action,
                                 instinct_action=action.value,
                                 reason="rest_would_override_productive_action",
                                 decision_id=did, channel="shift_plan")
                    else:
                        if adv.mapped_action != action:
                            self.log(actor.actor_id, "advice_followed", actor.cell,
                                     from_action=action.value, to_action=adv.mapped_action.value,
                                     decision_id=did, channel="shift_plan")
                        action = adv.mapped_action
                    target = None      # advice không chỉ định cell (product boundary D-004)

            # --- T-045a b3: kênh VỊ TRÍ — vòng idle chỉ ĐỌC `standby_plan` do planner gán ---
            # D-004 cấm reposition ở SẢN PHẨM; trong SIM được mở (2026-07-21) để nghiên cứu
            # rủi ro hệ thống. Adherence đã rút MỘT LẦN lúc gán — ở đây không rút lại.
            reloc_reason = "demand_seek"
            sb_cell = self.standby_plan.get(actor.actor_id)
            if sb_cell is not None:
                mode = self.advice.positioning_overrides
                if sb_cell == actor.cell:
                    # đã ở đúng ô — phân công hoàn thành, đứng chờ tại chỗ là đúng ý nó
                    self.standby_plan.pop(actor.actor_id, None)
                    self.standby_decision.pop(actor.actor_id, None)
                    self.market.pending_targets.pop(actor.actor_id, None)
                elif (action == IdleAction.WAIT if mode == "wait_only"
                      else action in (IdleAction.WAIT, IdleAction.RELOCATE)):
                    # BÀI HỌC REST (đo được −14k → −32k khi ghi đè quá tay): không bao giờ
                    # cướp quyền của go_swap (pin) / rest (sức khoẻ) / end_shift (kết ca).
                    self.standby_plan.pop(actor.actor_id, None)
                    self.market.pending_targets.pop(actor.actor_id, None)
                    self.log(actor.actor_id, "standby_followed", actor.cell,
                             from_action=action.value, to_cell=sb_cell,
                             decision_id=self.standby_decision.pop(actor.actor_id, ""),
                             channel="positioning")
                    action, target, reloc_reason = IdleAction.RELOCATE, sb_cell, "standby"

            # ĐA-04: các lần bị nhịp chung NÉN — log typed reason (một lần/quyết định)
            for (t_s, aid_s, topic_s, reason_s) in self.advice.drain_suppressed():
                # decision_id RIÊNG (hậu tố -sup): cái bị nén là một CANDIDATE MỚI,
                # KHÔNG phải quyết định đã nói trong cùng bucket — dùng chung id sẽ khiến
                # event suppressed ĐÈ trạng thái `followed` của quyết định trước (đo được:
                # decision_adherence tụt 0,25 trong khi event-level 0,68).
                self.log(aid_s, "advice_suppressed", "",
                         channel=topic_s, reason=reason_s,
                         decision_id=self._decision_id(aid_s, topic_s, t_s) + "-sup")

            # --- D-SIM-03 kênh `rest_window`: dồn nghỉ/đổi pin vào khung vắng khách (solver S7) ---
            # Chỉ HOÃN, không bao giờ ÉP nghỉ: nếu bản năng chưa muốn nghỉ thì không can thiệp.
            if action in (IdleAction.REST, IdleAction.GO_SWAP, IdleAction.GO_CHARGE):
                defer, why = self.advice.should_defer_rest(
                    actor, now, hour, self._actor_demand_hint,
                    float(self.veh["swap_soc_threshold_pct"]))
                if defer:
                    actor.rest_deferred_min += 2.0
                    self.log(actor.actor_id, "advice_rest_window", actor.cell,
                             deferred_from=action.value, reason=why, followed=True,
                             deferred_total_min=round(actor.rest_deferred_min, 1),
                             decision_id=self._decision_id(actor.actor_id, "rest_window", now),
                             channel="rest_window")
                    action, target = IdleAction.WAIT, None
                else:
                    # D-M3-05 guardrail tầng 5: kết cục KHÔNG-defer cũng phải quan sát được —
                    # veto lan can (soc_low/fatigued/defer_cap) là bằng chứng "lan can còn
                    # sống"; ai xoá lan can thì veto SỤP VỀ 0 và tầng 5 tố giác (kịch bản
                    # guardrail 4 tầng từng mù). Log-only: KHÔNG decision_id/followed (không
                    # được lọt mẫu số adherence — test T8), 0 RNG, 0 đổi state/action.
                    self.log(actor.actor_id, "advice_rest_veto", actor.cell,
                             reason=why or "cadence_suppressed", from_action=action.value,
                             channel="rest_window")

            # D-M3-01: kết cục của quyết định ĐÃ NÓI mà nhánh đó không tự log. Drain SAU cả hai
            # chỗ gọi (`check_shift_extend` ở trên, `should_defer_rest` ngay trên) — drain
            # sớm hơn thì bản ghi của tick này rơi sang tick sau.
            #
            # Không có nhánh này thì event của hai kênh đó chỉ tồn tại ở ca ĐÃ THEO ⇒ mẫu số
            # adherence chỉ chứa người đã theo ⇒ `decision_adherence` = 1,0 THEO CẤU TRÚC.
            # Đúng họ lỗi `F-1` (mẫu số `positioning` từng hụt) và `BUG-EVAL-ARGMAX`.
            #
            # `decision_id` tính từ `t_nf` (lúc NÓI), KHÔNG từ `now` (lúc drain), để trùng
            # đúng quyết định ở nhánh đã-theo. Và KHÔNG có hậu tố `-sup`: đây không phải bị
            # nén — advisor ĐÃ nói, tài xế nghe rồi không làm. Nó thuộc mẫu số.
            for (t_nf, aid_nf, topic_nf, followed_nf, reason_nf) in \
                    self.advice.drain_spoken_outcomes():
                self.log(aid_nf, _SPOKEN_OUTCOME_KIND[topic_nf], "",
                         channel=topic_nf, followed=followed_nf, reason=reason_nf,
                         added_min=0.0,
                         decision_id=self._decision_id(aid_nf, topic_nf, t_nf))

            if action == IdleAction.END_SHIFT:
                actor.state = ActorState.OFFLINE
                self._newbie_settle(actor)   # SIM-XANH P2: quyết toán tân binh trước chốt sổ
                # lớp thưởng ngày (rule component — realism: thưởng chiếm 20-30% thu nhập)
                bonus = self.policy.day_bonus(actor.points, actor.acceptance_rate, actor.completion_rate)
                actor.payout_vnd += bonus
                self.log(actor.actor_id, "end_shift", actor.cell,
                         trips=actor.trips_done, payout=actor.payout_vnd,
                         points=actor.points, day_bonus=bonus)
                break
            elif action in (IdleAction.GO_SWAP, IdleAction.GO_CHARGE):
                yield from self._do_charge(actor, action)
            elif action == IdleAction.REST:
                actor.state = ActorState.REST
                self.log(actor.actor_id, "rest", actor.cell)
                t0 = now
                rest_min = self.rng.uniform(REST_MIN_MINUTES, REST_MAX_MINUTES)
                actor.rest_min += rest_min
                yield self.env.timeout(rest_min)
                actor.state = ActorState.IDLE
                self._seg(actor.actor_id, t0, self.env.now, "rest",
                          (actor.lat, actor.lon), (actor.lat, actor.lon))
            elif action == IdleAction.RELOCATE and target:
                d = cell_distance_km(self.grid, actor.cell, target)
                fac_rel = self._dfac(actor.cell, target)
                t0 = now
                frm = (actor.lat, actor.lon)
                t = self._travel_min(d, hour, actor.cell, fac=fac_rel)
                actor.state = ActorState.ENROUTE
                actor.enroute_cell = target    # T-045a: cung ĐANG TỚI ô này
                yield self.env.timeout(t)
                # relocate tự nguyện cũng tốn pin theo đường thật (trước đây block này
                # KHÔNG trừ SOC — di chuyển miễn phí năng lượng là phi vật lý)
                actor.consume_soc(d * fac_rel, self._pct_per_km(actor))
                actor.empty_min += t
                clat, clon = self._cell_point(target)
                actor.state = ActorState.IDLE
                actor.enroute_cell = None     # tới nơi ⇒ hết là cung ĐANG TỚI
                self._set_pos(actor, clat, clon)  # M0-10
                self._seg(actor.actor_id, t0, self.env.now, "relocate", frm, (clat, clon), reason=reloc_reason)
                actor.idle_streak_min = 0.0   # đã dịch chuyển ⇒ đếm lại từ đầu
                self.log(actor.actor_id, "relocate", target, reason=reloc_reason)
            else:  # WAIT
                actor.idle_min += 2.0
                actor.idle_streak_min += 2.0   # T-045d: chuỗi rỗi LIÊN TỤC (reset khi được chào)
                # D-SIM-03: ghi idle THEO GIỜ để solver S7 chỉ được khung nên dồn nghỉ
                actor.idle_by_hour[hour] = actor.idle_by_hour.get(hour, 0.0) + 2.0
                yield self.env.timeout(2.0)  # chờ đơn, kiểm lại sau 2 phút

    def _actor_demand_hint(self, actor: Actor, hour: int) -> dict[str, float]:
        """M0-3/M0-4: kinh nghiệm cá nhân = EXPECTED field (config) × nhiễu per-actor
        sample MỘT LẦN cho mỗi (actor, giờ) rồi cache — belief ổn định trong ngày,
        không đọc realized trace (hết future leak), không resample mỗi idle-check.

        Nhiễu per-cell dùng RNG con deterministic theo (seed, actor_id, hour) và
        duyệt cell theo thứ tự SORTED — kết quả không phụ thuộc PYTHONHASHSEED
        (root cause cross-process nondeterminism đã prove ở T-030 baseline)."""
        key = (actor.actor_id, hour, actor.cell)  # cell trong key: tầm nhìn đổi khi di chuyển
        cached = self._belief_cache.get(key)
        if cached is not None:
            return cached
        field = self.demand_field.get(hour, {})
        if not field:
            self._belief_cache[key] = {}
            return {}
        sigma = actor.demand_prior_sigma
        hint: dict[str, float] = {}
        from .geo import grid_disk
        for c in sorted(grid_disk(actor.cell, 2)):
            base = field.get(c, 0.0)
            # A6: nhiễu lognormal (luôn dương) — sai số nhân; lão làng σ nhỏ chính xác hơn.
            # Nhiễu PER-CELL deterministic theo (seed, actor, hour, cell): cùng cell luôn
            # cùng nhiễu dù actor nhìn từ vị trí nào — "trí nhớ" nhất quán, không phụ
            # thuộc thứ tự duyệt hay PYTHONHASHSEED.
            rng_c = np.random.default_rng((self.seed, actor.actor_id, hour, int(c, 16)))
            noise = math.exp(rng_c.normal(0.0, sigma))
            hint[c] = base * noise
        self._belief_cache[key] = hint
        return hint

    def _do_charge(self, actor: Actor, action: IdleAction):
        if action == IdleAction.GO_CHARGE:
            # M0-8: VỀ NHÀ rồi mới sạc cắm — leg di chuyển thật (thời gian + pin + segment),
            # không teleport/sạc tại chỗ như baseline.
            hour = int(self.env.now // 60) % 24
            pct_per_km = self._pct_per_km(actor)
            actor.state = ActorState.CHARGING
            if actor.cell != actor.home_cell:
                d = cell_distance_km(self.grid, actor.cell, actor.home_cell)
                fac = self._dfac(actor.cell, actor.home_cell)
                t0 = self.env.now
                frm = (actor.lat, actor.lon)
                t = self._travel_min(d, hour, actor.cell, fac=fac)
                yield self.env.timeout(t)
                actor.consume_soc(d * fac, pct_per_km)
                actor.empty_min += t
                hlat, hlon = self._cell_point(actor.home_cell)
                self._set_pos(actor, hlat, hlon)  # M0-10
                self._seg(actor.actor_id, t0, self.env.now, "relocate", frm, (hlat, hlon),
                          reason="go_home_charge")
            self.log(actor.actor_id, "charge_home_start", actor.cell)
            t0 = self.env.now
            dur = float(self.veh["home_charge_min"])
            actor.charge_min += dur
            yield self.env.timeout(dur)
            actor.soc_pct = 100.0
            actor.state = ActorState.IDLE
            self._seg(actor.actor_id, t0, self.env.now, "charge",
                      (actor.lat, actor.lon), (actor.lat, actor.lon), mode="home")
            self.log(actor.actor_id, "charge_home_end", actor.cell)
            return
        # đổi pin tại trạm
        station = choose_station(actor, self.grid, self.stations, self.env.now, self.rng)
        if station is None:
            # không có trạm nào trong world (config degenerate) — fallback có nhãn, không im lặng
            actor.soc_pct = 100.0
            actor.state = ActorState.IDLE
            self.log(actor.actor_id, "swap_fallback_no_station", actor.cell)
            return
        hour = int(self.env.now // 60) % 24
        pct_per_km = self._pct_per_km(actor)
        d = cell_distance_km(self.grid, actor.cell, station.cell)
        fac = self._dfac(actor.cell, station.cell)
        travel = self._travel_min(d, hour, actor.cell, fac=fac)
        t0 = self.env.now
        frm = (actor.lat, actor.lon)
        actor.state = ActorState.CHARGING
        self.log(actor.actor_id, "go_swap", actor.cell, station=station.node_id)
        yield self.env.timeout(travel)
        actor.consume_soc(d * fac, pct_per_km)
        self._set_pos(actor, station.lat, station.lon)  # vị trí = trạm THẬT; cell sync M0-10
        actor.empty_min += travel
        # đoạn di chuyển tới trạm (enroute-to-swap)
        self._seg(actor.actor_id, t0, self.env.now, "relocate", frm, (station.lat, station.lon),
                  reason="go_swap", station=station.node_id)
        t_arrive = self.env.now
        # xếp hàng — M0-1: chỉ swap khi THẬT SỰ có pin ready; hết wait-cap → swap_failed
        station.queue_len += 1
        wait = 0.0
        wait_cap = float(self.cfg.get("station.wait_cap_min", 60.0))
        swapped = False
        recharge = float(self.cfg.get("station.battery_recharge_min"))
        while wait <= wait_cap:
            full = [b for b in station.batteries
                    if b.soc_pct >= station.ready_soc_pct and b.ready_at_min <= self.env.now]
            if full:
                # M0-1: đổi 1-1 ATOMIC ngay lúc bắt đầu swap — pin đầy ra, pin cạn vào khe
                # sạc ngay (tổng pin tủ bất biến mọi thời điểm; chống race 2 actor 1 pin).
                full.sort(key=lambda b: b.ready_at_min)
                station.batteries.remove(full[0])
                station.batteries.append(
                    BatteryInStation(soc_pct=100.0, ready_at_min=self.env.now + recharge))
                swapped = True
                break
            yield self.env.timeout(1.0)
            wait += 1.0
        station.queue_len = max(0, station.queue_len - 1)
        if not swapped:
            # M0-1: không còn pin ready trong wait_cap → rời trạm SOC nguyên (không pin ma).
            # Behavior sẽ re-trigger GO_SWAP ở decision point sau (pin trạm giờ hồi được → hết livelock).
            actor.charge_min += travel + wait
            actor.state = ActorState.IDLE
            self._seg(actor.actor_id, t_arrive, self.env.now, "charge",
                      (station.lat, station.lon), (station.lat, station.lon),
                      mode="swap_failed", wait_min=round(wait, 1), station=station.node_id)
            self.log(actor.actor_id, "swap_failed", station.cell,
                     station=station.node_id, wait_min=round(wait, 1))
            return
        swap_s = self.rng.uniform(float(self.cfg.get("station.swap_time_s_min")),
                                  float(self.cfg.get("station.swap_time_s_max")))
        yield self.env.timeout(swap_s / 60.0)
        actor.charge_min += travel + wait + swap_s / 60.0
        # (đổi pin 1-1 đã thực hiện atomic ở vòng chờ phía trên)
        actor.soc_pct = 100.0
        actor.state = ActorState.IDLE
        self._seg(actor.actor_id, t_arrive, self.env.now, "charge",
                  (station.lat, station.lon), (station.lat, station.lon),
                  mode="swap", wait_min=round(wait, 1), station=station.node_id)
        actor.cost_vnd += self.swap_fee_vnd   # T-045b: mặc định 0 — sổ riêng, KHÔNG đụng payout
        self.log(actor.actor_id, "swap_done", station.cell, station=station.node_id, wait_min=round(wait, 1))

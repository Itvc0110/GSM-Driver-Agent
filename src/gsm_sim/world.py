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

from .behavior import IdleAction, accept_order, choose_idle_action, choose_station
from .config import Config
from .dispatcher import _speed_kmh, match_batch
from .entities import Actor, ActorState, BatteryInStation, FleetType, Station
from .geo import Grid, cell_distance_km, grid_disk
from .policy import PolicyBundle


@dataclass
class Event:
    t_min: float
    actor_id: int
    kind: str
    cell: str = ""
    detail: dict = field(default_factory=dict)


class World:
    def __init__(self, grid: Grid, cfg: Config, policy: PolicyBundle, orders: list, actors: list[Actor],
                 seed: int, environment=None, congestion=None):
        self.grid = grid
        self.cfg = cfg
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
        bcfg = cfg.get("behavior", {})
        self.accept_cost_km = float(bcfg.get("accept_cost_per_pickup_km_vnd", 3000.0))
        self.accept_center = float(bcfg.get("accept_logit_center_vnd", 6000.0))
        self.accept_scale = float(bcfg.get("accept_logit_scale_vnd", 8000.0))
        # SIM-1 fix C: huỷ SAU KHI nhận (khách bom/khách huỷ/sự cố). Sim cũ hoàn thành
        # 99.6% cuốc đã nhận — "quá sạch" so thực tế (~95%). Xảy ra khi tài xế ĐANG
        # trên đường đón (chưa gặp khách) → tốn thời gian + pin, KHÔNG có doanh thu.
        self.cancel_after_accept = float(bcfg.get("cancel_after_accept_rate", 0.05))

        # RNG stream riêng cho hành vi actor (nền CRN: ngoại sinh đã ở orders)
        self.rng = np.random.default_rng(seed ^ 0xBEEF)

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
        self.events.append(Event(round(self.env.now, 3), actor_id, kind, cell, detail))

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

    def _travel_min(self, dist_km: float, hour: int, cell: str | None = None) -> float:
        """Thời gian di chuyển = quãng đường THỰC (× detour) / tốc độ hiệu dụng (tại cell gốc)."""
        return (dist_km * self.detour) / self._eff_speed(hour, cell) * 60.0

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
        for a in self.actors.values():
            self.env.process(self._actor_proc(a))
        self.env.run(until=self.end_min)
        self._settle_end_of_run()
        return self.events

    def _settle_end_of_run(self):
        """M0-6 + M0-4: chốt cuối ngày — flush time cho actor còn bận, censor đơn in-flight,
        rồi mới tính thưởng ngày. SimPy bỏ rơi timeout đang treo nên phải reconcile tường minh."""
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
                bonus = self.policy.day_bonus(a.points, a.acceptance_rate, a.completion_rate)
                a.payout_vnd += bonus
                self.log(a.actor_id, "day_end_settle", a.cell,
                         trips=a.trips_done, payout=a.payout_vnd, points=a.points, day_bonus=bonus)

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
                                  speed_fn=lambda cell, h: self._eff_speed(h, cell), detour=self.detour)
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
                # SOC đủ hoàn thành? (pickup + trip, quãng đường thực × detour)
                total_km = (asg.pickup_dist_km + order.dist_km) * self.detour
                enough = actor.soc_pct - total_km * self._pct_per_km(actor) > 8.0
                forced = actor.acceptance_rate < 0.5 and actor.orders_offered > 5
                if not enough:
                    # SIM-1: KHÔNG còn tính là "cancelled" — tài xế chưa hề nhận đơn.
                    # `orders_cancelled` từ nay CHỈ đếm huỷ SAU khi nhận (khớp nghĩa cột
                    # `cancelled_count` trong `driver_statistic_daily`).
                    actor.orders_soc_skipped += 1
                    continue
                if not accept_order(actor, order.gross_vnd, asg.pickup_dist_km, forced, self.rng,
                                    self.accept_cost_km, self.accept_center, self.accept_scale):
                    self.log(actor.actor_id, "order_declined", actor.cell, order_id=order.order_id)
                    continue
                # nhận đơn
                actor.orders_accepted += 1
                self.open_orders.pop(order.order_id, None)
                self.order_open_since.pop(order.order_id, None)
                self._order_transition(order.order_id, "MATCHED")
                self.log(actor.actor_id, "order_matched", actor.cell, order_id=order.order_id)
                actor.state = ActorState.ENROUTE
                self.env.process(self._serve_trip(actor, order, asg))

    def _serve_trip(self, actor: Actor, order, asg):
        hour = int(self.env.now // 60) % 24
        pct_per_km = self._pct_per_km(actor)
        origin_cell = actor.cell
        t_assign = self.env.now
        frm = (actor.lat, actor.lon)   # vị trí trước khi đi đón
        # tới điểm đón (quãng đường thực × detour / tốc độ hiệu dụng tại cell gốc)
        pickup_min = self._travel_min(asg.pickup_dist_km, hour, origin_cell)

        # --- SIM-1 fix C: huỷ sau khi nhận, xảy ra GIỮA ĐƯỜNG ĐI ĐÓN ---
        # Quyết định TRƯỚC khi timeout (không nhìn tương lai: chỉ dùng rng, không dùng
        # kết quả cuốc). Tài xế đã đi được một phần quãng đón thì đơn bị huỷ.
        if self.rng.random() < self.cancel_after_accept:
            frac = float(self.rng.uniform(0.3, 1.0))    # đã đi được 30-100% quãng đón
            spent = pickup_min * frac
            yield self.env.timeout(spent)
            actor.consume_soc(asg.pickup_dist_km * self.detour * frac, pct_per_km)
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
        actor.consume_soc(asg.pickup_dist_km * self.detour, pct_per_km)
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
        trip_min = self._travel_min(order.dist_km, hour, order.pickup_cell)
        yield self.env.timeout(trip_min)
        actor.occupied_min += trip_min
        actor.consume_soc(order.dist_km * self.detour, pct_per_km)
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
        hour = int(self.env.now // 60) % 24
        pct_per_km = self._pct_per_km(actor)
        t0 = self.env.now
        frm = (actor.lat, actor.lon)
        t = self._travel_min(d, hour, actor.cell)
        actor.state = ActorState.ENROUTE
        yield self.env.timeout(t)
        actor.consume_soc(d * self.detour, pct_per_km)
        actor.empty_min += t
        clat, clon = self._cell_point(target)
        actor.state = ActorState.IDLE
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
            action, target = choose_idle_action(actor, now, self.grid, self.veh, hour, hint, self.rng)

            if action == IdleAction.END_SHIFT:
                actor.state = ActorState.OFFLINE
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
                rest_min = self.rng.uniform(20, 45)
                actor.rest_min += rest_min
                yield self.env.timeout(rest_min)
                actor.state = ActorState.IDLE
                self._seg(actor.actor_id, t0, self.env.now, "rest",
                          (actor.lat, actor.lon), (actor.lat, actor.lon))
            elif action == IdleAction.RELOCATE and target:
                d = cell_distance_km(self.grid, actor.cell, target)
                t0 = now
                frm = (actor.lat, actor.lon)
                t = self._travel_min(d, hour, actor.cell)
                actor.state = ActorState.ENROUTE
                yield self.env.timeout(t)
                actor.empty_min += t
                clat, clon = self._cell_point(target)
                actor.state = ActorState.IDLE
                self._set_pos(actor, clat, clon)  # M0-10
                self._seg(actor.actor_id, t0, self.env.now, "relocate", frm, (clat, clon), reason="demand_seek")
                self.log(actor.actor_id, "relocate", target, reason="demand_seek")
            else:  # WAIT
                actor.idle_min += 2.0
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
                t0 = self.env.now
                frm = (actor.lat, actor.lon)
                t = self._travel_min(d, hour, actor.cell)
                yield self.env.timeout(t)
                actor.consume_soc(d * self.detour, pct_per_km)
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
        travel = self._travel_min(d, hour, actor.cell)
        t0 = self.env.now
        frm = (actor.lat, actor.lon)
        actor.state = ActorState.CHARGING
        self.log(actor.actor_id, "go_swap", actor.cell, station=station.node_id)
        yield self.env.timeout(travel)
        actor.consume_soc(d * self.detour, pct_per_km)
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
        self.log(actor.actor_id, "swap_done", station.cell, station=station.node_id, wait_min=round(wait, 1))

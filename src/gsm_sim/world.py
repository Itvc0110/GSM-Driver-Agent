"""SimPy world — ghép mọi thứ chạy 1 ngày (1 arm B).

Nguồn: specs/simulation-pilot-world.md, advisor-optimization-layer-a.md §1/§4.
Kiến trúc: pure DES cho trip/swap lifecycle + dispatch tick 5s. Event log append vào list.

Slice v0: 1 arm (B, không advice). Twin-runner 3 arm ở vòng sau.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
    def __init__(self, grid: Grid, cfg: Config, policy: PolicyBundle, orders: list, actors: list[Actor], seed: int):
        self.grid = grid
        self.cfg = cfg
        self.policy = policy
        self.orders = orders
        self.actors = {a.actor_id: a for a in actors}
        self.seed = seed
        self.env = simpy.Environment()
        self.events: list[Event] = []
        self.speed_cfg = cfg.get("speed_kmh")
        self.disp_cfg = cfg.get("dispatcher")
        self.veh = cfg.get("vehicle")

        # RNG stream riêng cho hành vi actor (nền CRN: ngoại sinh đã ở orders)
        self.rng = np.random.default_rng(seed ^ 0xBEEF)

        # đơn mở theo thời điểm — dùng con trỏ
        self.orders_sorted = sorted(orders, key=lambda o: (o.t_min, o.order_id))
        self._order_ptr = 0
        self.open_orders: dict[int, object] = {}     # order_id -> Order
        self.order_open_since: dict[int, float] = {}

        # trạm
        self.stations: list[Station] = self._build_stations()
        self.station_by_id = {s.node_id: s for s in self.stations}

        self.metrics_start = float(cfg.get("time.start_min")) + float(cfg.get("time.warmup_min"))
        self.end_min = float(cfg.get("time.end_min"))

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

    # --- Processes ---

    def run(self):
        self.env.process(self._dispatcher_proc())
        self.env.process(self._order_expiry_proc())
        for a in self.actors.values():
            self.env.process(self._actor_proc(a))
        self.env.run(until=self.end_min)
        return self.events

    def _inject_orders(self):
        """Đưa các đơn tới thời điểm hiện tại vào open pool."""
        now = self.env.now
        while self._order_ptr < len(self.orders_sorted) and self.orders_sorted[self._order_ptr].t_min <= now:
            o = self.orders_sorted[self._order_ptr]
            self.open_orders[o.order_id] = o
            self.order_open_since[o.order_id] = now
            self._order_ptr += 1

    def _order_expiry_proc(self):
        expire_s = float(self.disp_cfg["order_expire_s"])
        while True:
            yield self.env.timeout(0.5)  # quét mỗi 30s-sim (đơn vị thời gian = phút)
            now = self.env.now
            expired = [oid for oid, t0 in self.order_open_since.items()
                       if oid in self.open_orders and (now - t0) * 60.0 > expire_s]
            for oid in expired:
                self.open_orders.pop(oid, None)
                self.order_open_since.pop(oid, None)
                self.log(-1, "order_expired", detail={"order_id": oid})

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
                                  self.speed_cfg, self.disp_cfg)
            for asg in assigns:
                order = self.open_orders.get(asg.order_id)
                actor = self.actors.get(asg.actor_id)
                if order is None or actor is None or actor.state != ActorState.IDLE:
                    continue
                actor.orders_offered += 1
                # SOC đủ hoàn thành? (pickup + trip)
                total_km = asg.pickup_dist_km + order.dist_km
                pct_per_km = (self.veh["swap_consume_pct_per_km"] if actor.fleet == FleetType.SWAP
                              else self.veh["charge_consume_pct_per_km"])
                enough = actor.soc_pct - total_km * float(pct_per_km) > 8.0
                forced = actor.acceptance_rate < 0.5 and actor.orders_offered > 5
                if not enough:
                    actor.orders_cancelled += 1
                    continue
                if not accept_order(actor, order.gross_vnd, asg.pickup_dist_km, forced, self.rng):
                    self.log(actor.actor_id, "order_declined", actor.cell, order_id=order.order_id)
                    continue
                # nhận đơn
                actor.orders_accepted += 1
                self.open_orders.pop(order.order_id, None)
                self.order_open_since.pop(order.order_id, None)
                actor.state = ActorState.ENROUTE
                self.env.process(self._serve_trip(actor, order, asg))

    def _serve_trip(self, actor: Actor, order, asg):
        hour = int(self.env.now // 60) % 24
        speed = _speed_kmh(hour, self.speed_cfg)
        pct_per_km = float(self.veh["swap_consume_pct_per_km"] if actor.fleet == FleetType.SWAP
                           else self.veh["charge_consume_pct_per_km"])
        # tới điểm đón
        pickup_min = asg.pickup_dist_km / speed * 60.0
        yield self.env.timeout(pickup_min)
        actor.consume_soc(asg.pickup_dist_km, pct_per_km)
        actor.cell = order.pickup_cell
        actor.empty_min += pickup_min
        actor.state = ActorState.ON_TRIP
        self.log(actor.actor_id, "pickup", order.pickup_cell, order_id=order.order_id)
        # chở khách
        trip_min = order.dist_km / speed * 60.0
        yield self.env.timeout(trip_min)
        actor.consume_soc(order.dist_km, pct_per_km)
        # kiểm tra stranded (variance): nếu SOC <= 0 giữa đường
        if actor.soc_pct <= 0.0:
            actor.stranded_count += 1
            self.log(actor.actor_id, "battery_stranded", order.drop_cell, order_id=order.order_id)
        actor.cell = order.drop_cell
        actor.trips_done += 1
        actor.orders_completed += 1
        actor.gross_vnd += order.gross_vnd
        actor.payout_vnd += self.policy.driver_payout_from_gross(order.gross_vnd)
        actor.points += self.policy.trip_points(int(order.t_min // 60) % 24)
        self.log(actor.actor_id, "dropoff", order.drop_cell,
                 order_id=order.order_id, gross=order.gross_vnd, dist_km=order.dist_km)
        # nếu trả khách ngoài lõi → deadhead quay về cell lõi gần nhất
        if not self.grid.is_core(actor.cell):
            yield from self._deadhead_to_core(actor, speed, pct_per_km)
        actor.state = ActorState.IDLE

    def _deadhead_to_core(self, actor: Actor, speed: float, pct_per_km: float):
        # tìm cell lõi gần nhất trong vành mở rộng
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
        t = d / speed * 60.0
        yield self.env.timeout(t)
        actor.consume_soc(d, pct_per_km)
        actor.empty_min += t
        actor.cell = target

    def _actor_proc(self, actor: Actor):
        # chờ tới giờ bắt đầu ca
        if actor.shift_start_min > self.env.now:
            yield self.env.timeout(actor.shift_start_min - self.env.now)
        actor.state = ActorState.IDLE
        self.log(actor.actor_id, "go_online", actor.cell)
        last = self.env.now

        while self.env.now < self.end_min:
            # nếu đang bận (enroute/on_trip/charging) → nhường, kiểm lại sau
            if actor.state in (ActorState.ENROUTE, ActorState.ON_TRIP, ActorState.CHARGING, ActorState.REST):
                yield self.env.timeout(1.0)
                continue
            if actor.state == ActorState.OFFLINE:
                break
            # actor IDLE: cập nhật online time
            now = self.env.now
            actor.online_min += (now - last)
            last = now
            hour = int(now // 60) % 24
            action, target = choose_idle_action(actor, now, self.grid, self.veh, hour, None, self.rng)

            if action == IdleAction.END_SHIFT:
                actor.state = ActorState.OFFLINE
                self.log(actor.actor_id, "end_shift", actor.cell,
                         trips=actor.trips_done, payout=actor.payout_vnd, points=actor.points)
                break
            elif action in (IdleAction.GO_SWAP, IdleAction.GO_CHARGE):
                yield from self._do_charge(actor, action)
                last = self.env.now
            elif action == IdleAction.REST:
                actor.state = ActorState.REST
                self.log(actor.actor_id, "rest", actor.cell)
                yield self.env.timeout(self.rng.uniform(20, 45))
                actor.state = ActorState.IDLE
                last = self.env.now
            elif action == IdleAction.RELOCATE and target:
                speed = _speed_kmh(hour, self.speed_cfg)
                d = cell_distance_km(self.grid, actor.cell, target)
                t = d / speed * 60.0
                yield self.env.timeout(t)
                actor.empty_min += t
                actor.cell = target
                last = self.env.now
            else:  # WAIT
                yield self.env.timeout(2.0)  # chờ đơn, kiểm lại sau 2 phút
                last = self.env.now

    def _do_charge(self, actor: Actor, action: IdleAction):
        if action == IdleAction.GO_CHARGE:
            # về nhà sạc cắm
            actor.state = ActorState.CHARGING
            self.log(actor.actor_id, "charge_home_start", actor.cell)
            yield self.env.timeout(float(self.veh["home_charge_min"]))
            actor.soc_pct = 100.0
            actor.state = ActorState.IDLE
            self.log(actor.actor_id, "charge_home_end", actor.cell)
            return
        # đổi pin tại trạm
        station = choose_station(actor, self.grid, self.stations, self.env.now, self.rng)
        if station is None:
            actor.soc_pct = 100.0
            actor.state = ActorState.IDLE
            return
        hour = int(self.env.now // 60) % 24
        speed = _speed_kmh(hour, self.speed_cfg)
        pct_per_km = float(self.veh["swap_consume_pct_per_km"])
        d = cell_distance_km(self.grid, actor.cell, station.cell)
        travel = d / speed * 60.0
        actor.state = ActorState.CHARGING
        self.log(actor.actor_id, "go_swap", actor.cell, station=station.node_id)
        yield self.env.timeout(travel)
        actor.consume_soc(d, pct_per_km)
        actor.cell = station.cell
        actor.empty_min += travel
        # xếp hàng
        station.queue_len += 1
        wait = 0.0
        while station.available_full(self.env.now) < 1:
            yield self.env.timeout(1.0)
            wait += 1.0
            if wait > 60.0:  # tránh kẹt vô hạn slice v0
                break
        swap_s = self.rng.uniform(float(self.cfg.get("station.swap_time_s_min")),
                                  float(self.cfg.get("station.swap_time_s_max")))
        yield self.env.timeout(swap_s / 60.0)
        station.queue_len = max(0, station.queue_len - 1)
        # lấy 1 pin đầy, trả pin cạn (bắt đầu sạc lại)
        full = [b for b in station.batteries if b.soc_pct >= station.ready_soc_pct and b.ready_at_min <= self.env.now]
        if full:
            station.batteries.remove(full[0])
        recharge = float(self.cfg.get("station.battery_recharge_min"))
        station.batteries.append(BatteryInStation(soc_pct=0.0, ready_at_min=self.env.now + recharge))
        actor.soc_pct = 100.0
        actor.state = ActorState.IDLE
        self.log(actor.actor_id, "swap_done", station.cell, station=station.node_id, wait_min=round(wait, 1))

"""Server-owned observer replay sessions for the unified Web demo."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable
import hashlib
import math

from gsm_sim.demo_trace import build_demo_trace


class DemoSessionError(RuntimeError):
    """Base class for explicit demo session boundary errors."""


class DemoSessionNotFound(DemoSessionError):
    pass


class DemoSessionConflict(DemoSessionError):
    pass


@dataclass
class _DemoSession:
    session_id: str
    seed: int
    result: Any
    traces: dict[int, dict]
    actors: list[dict]
    selected_actor_id: int | None = None
    cursor: int = -1
    step_version: int = 0
    status: str = "awaiting_actor"
    idempotent_responses: dict[str, dict] = field(default_factory=dict)
    route_cache: dict[tuple, dict] = field(default_factory=dict)
    lock: threading.RLock = field(default_factory=threading.RLock, repr=False)


def _default_run(seed: int):
    # Import lazily so importing the Web app does not eagerly construct the simulator.
    from app.routers.sim import _run
    return _run(seed)


class DemoSessionService:
    """Small in-process session store for one demo process.

    The completed ``RunResult`` is immutable from this service's perspective.  Only the
    selected actor/cursor/idempotency map changes, under the per-session lock.
    """

    def __init__(self, *, run_factory: Callable[[int], Any] | None = None,
                 session_id_factory: Callable[[], str] | None = None,
                 route_factory: Callable[[list[dict]], dict] | None = None):
        self.run_factory = run_factory or _default_run
        self.session_id_factory = session_id_factory or (lambda: str(uuid.uuid4()))
        self.route_factory = route_factory or _default_route
        self._sessions: dict[str, _DemoSession] = {}
        self._lock = threading.RLock()

    def create(self, seed: int = 1000) -> dict:
        result = self.run_factory(int(seed))
        actors = sorted(({
            "actor_id": int(actor.actor_id),
            "archetype": str(actor.archetype),
            "fleet": getattr(getattr(actor, "fleet", None), "value",
                              getattr(actor, "fleet", None)),
        } for actor in getattr(result, "actors", [])), key=lambda item: item["actor_id"])
        if not actors:
            raise DemoSessionError("run không có actor")
        traces = {item["actor_id"]: build_demo_trace(result, item["actor_id"])
                  for item in actors}
        session_id = self.session_id_factory()
        session = _DemoSession(session_id=session_id, seed=int(seed), result=result,
                               traces=traces, actors=actors)
        with self._lock:
            self._sessions[session_id] = session
        return self._summary(session)

    def _get(self, session_id: str) -> _DemoSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise DemoSessionNotFound(f"session {session_id!r} không tồn tại")
        return session

    def select_actor(self, session_id: str, actor_id: int) -> dict:
        session = self._get(session_id)
        with session.lock:
            if not any(item["actor_id"] == int(actor_id) for item in session.actors):
                raise ValueError(f"actor {actor_id} không tồn tại trong session")
            if session.cursor >= 0 and session.selected_actor_id != int(actor_id):
                raise DemoSessionConflict("không thể đổi actor sau khi session đã advance")
            session.selected_actor_id = int(actor_id)
            session.status = "active"
            return self._summary(session)

    def state(self, session_id: str) -> dict:
        session = self._get(session_id)
        with session.lock:
            return self._summary(session)

    def advance(self, session_id: str, *, client_step_id: str,
                expected_step_version: int) -> dict:
        if not client_step_id:
            raise ValueError("client_step_id không được rỗng")
        session = self._get(session_id)
        with session.lock:
            cached = session.idempotent_responses.get(client_step_id)
            if cached is not None:
                return cached
            if session.selected_actor_id is None:
                raise DemoSessionConflict("chưa chọn actor")
            if int(expected_step_version) != session.step_version:
                raise DemoSessionConflict(
                    f"step_version conflict: expected {expected_step_version}, "
                    f"current {session.step_version}")
            if session.status == "completed":
                raise DemoSessionNotFound("session đã completed")
            trace = session.traces[session.selected_actor_id]
            transitions = trace["transitions"]
            next_cursor = session.cursor + 1
            if next_cursor >= len(transitions):
                session.status = "completed"
                raise DemoSessionNotFound("session đã completed")
            session.cursor = next_cursor
            session.step_version += 1
            if session.cursor == len(transitions) - 1:
                session.status = "completed"
            response = self._step_response(session, transitions[session.cursor])
            session.idempotent_responses[client_step_id] = response
            return response

    @staticmethod
    def _summary(session: _DemoSession) -> dict:
        current = None
        if session.selected_actor_id is not None and session.cursor >= 0:
            current = session.traces[session.selected_actor_id]["transitions"][session.cursor]
        return {
            "session_id": session.session_id,
            "run_id": getattr(session.result, "run_id", None),
            "seed": session.seed,
            "status": session.status,
            "actor_id": session.selected_actor_id,
            "step_version": session.step_version,
            "cursor": session.cursor,
            "total_steps": len(session.traces[session.selected_actor_id]["transitions"])
            if session.selected_actor_id is not None else None,
            "actors": list(session.actors),
            "current_transition": current,
            "provenance": {"run_id": getattr(session.result, "run_id", None),
                            "seed": session.seed, "data_mode": "sim-engine", "is_mock": True},
        }

    def _step_response(self, session: _DemoSession, transition: dict) -> dict:
        trace = session.traces[session.selected_actor_id]
        driver = transition["driver"]
        trip = transition.get("trip")
        routes = self._routes(session, driver, trip)
        advice = DemoSessionService._advice(transition.get("checkpoint"))
        timeline = [
            {"sequence": item["sequence"], "transition_id": item["transition_id"],
             "t_min": item["t_min"], "kind": item["kind"]}
            for item in trace["transitions"][:transition["sequence"] + 1]
        ]
        return {
            "session_id": session.session_id,
            "run_id": trace["run_id"],
            "seed": trace["seed"],
            "actor_id": session.selected_actor_id,
            "step_version": session.step_version,
            "simulation_time_min": transition["t_min"],
            "transition": transition,
            "driver": driver,
            "state_delta": transition.get("state_delta") or {},
            "trip": trip,
            "map": DemoSessionService._map_payload(driver, trip),
            "routes": routes,
            "advice": advice,
            "timeline": timeline,
            "provenance": trace["provenance"],
        }

    @staticmethod
    def _map_payload(driver: dict, trip: dict | None) -> dict:
        markers = {"driver": dict(driver["position"])}
        if trip is not None:
            markers["pickup"] = dict(trip["pickup"])
            markers["destination"] = dict(trip["destination"])
        return {"driver": dict(driver["position"]), "markers": markers,
                "is_mock": True, "data_mode": "sim-engine"}

    @staticmethod
    def _advice(checkpoint: dict | None) -> dict:
        if checkpoint is None:
            return {"status": "silent", "reason_code": "no_checkpoint"}
        # Task 4 replaces this trace reference with the persisted AdviceEnvelopeV2 lease.
        # Keeping the raw checkpoint separate makes the current step truthful and avoids a
        # fake display ID before the lifecycle bridge has actually offered one.
        return {"status": "ready", "checkpoint": checkpoint,
                "presentation_source": "template"}

    def _routes(self, session: _DemoSession, driver: dict,
                trip: dict | None) -> list[dict]:
        if trip is None or trip.get("state") in {"DECLINED", "SKIPPED_SOC"}:
            return []
        state = str(trip.get("state"))
        if state in {"MATCHED", "CANCELLED_AFTER_ACCEPT"}:
            leg = "driver_to_pickup"
            start = driver["position"]
            end = trip["pickup"]
        elif state in {"PICKED_UP", "COMPLETED"}:
            leg = "pickup_to_destination"
            start = trip["pickup"]
            end = trip["destination"]
        else:
            return []
        start_lon = start.get("lng", start.get("lon"))
        end_lon = end.get("lng", end.get("lon"))
        key = (leg, round(float(start["lat"]), 6), round(float(start_lon), 6),
               round(float(end["lat"]), 6), round(float(end_lon), 6))
        route = session.route_cache.get(key)
        if route is None:
            waypoints = [{"lat": float(start["lat"]), "lng": float(start_lon),
                          "name": leg},
                         {"lat": float(end["lat"]), "lng": float(end_lon),
                          "name": leg}]
            try:
                raw = self.route_factory(waypoints)
                if hasattr(raw, "model_dump"):
                    raw = raw.model_dump()
                route = _normalize_route(raw, leg, key)
            except Exception:
                route = _fallback_route(waypoints, leg, key)
            session.route_cache[key] = route
        return [dict(route)]


def _default_route(waypoints: list[dict]) -> dict:
    from app.models import RouteCalculateRequest, WaypointItem
    from app.routers.routing import calculate_multi_stop_route
    request = RouteCalculateRequest(
        waypoints=[WaypointItem(**point) for point in waypoints])
    return calculate_multi_stop_route(request)


def _route_id(leg: str, key: tuple) -> str:
    return "route-" + hashlib.sha256(repr((leg, key)).encode("utf-8")).hexdigest()[:24]


def _normalize_route(raw: dict, leg: str, key: tuple) -> dict:
    return {
        "route_id": _route_id(leg, key), "leg": leg,
        "coords": raw.get("coords") or [],
        "distance_km": float(raw.get("total_dist_km", 0.0)),
        "duration_min": int(raw.get("total_duration_min", 0)),
        "source": raw.get("source", "unknown"),
        "route_is_real_road": bool(raw.get("route_is_real_road", False)),
        "is_mock": bool(raw.get("is_mock", True)),
        "data_mode": raw.get("data_mode", "synthetic"),
    }


def _fallback_route(waypoints: list[dict], leg: str, key: tuple) -> dict:
    start, end = waypoints[0], waypoints[-1]
    lat1, lon1 = float(start["lat"]), float(start["lng"])
    lat2, lon2 = float(end["lat"]), float(end["lng"])
    coords = [[lat1 + (lat2 - lat1) * i / 30,
               lon1 + (lon2 - lon1) * i / 30] for i in range(31)]
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    haversine = 2 * radius * math.asin(math.sqrt(
        math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2))
    return {
        "route_id": _route_id(leg, key), "leg": leg, "coords": coords,
        "distance_km": round(haversine, 1),
        "duration_min": max(1, round(haversine / 20.0 * 60.0)),
        "source": "fallback_straight_line", "route_is_real_road": False,
        "is_mock": True, "data_mode": "synthetic",
    }


DEMO_SESSIONS = DemoSessionService()

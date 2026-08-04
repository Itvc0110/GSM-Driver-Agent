"""Server-owned observer replay sessions for the unified Web demo."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
import copy
from functools import lru_cache
from pathlib import Path
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


@lru_cache(maxsize=6)
def _default_run(seed: int):
    """Build one cached, observer-only demo run.

    The production simulator config keeps advice tracing off.  The demo makes a deep copy
    and enables only existing S1/S2 trace callsites with zero adherence and no action
    override.  That gives the replay real checkpoint artifacts while keeping simulator
    dynamics and the shared config untouched; a click still only moves the cursor.
    """
    from app.routers.sim import _cfg
    from gsm_sim.config import Config
    from gsm_sim.runner import run_once

    base = _cfg()
    config = Config(copy.deepcopy(base.data), base.root_dir)
    advice = config.data.setdefault("advice", {})
    advice["enabled"] = True
    advice["coverage"] = "all"
    advice["single_actor_id"] = None
    advice["positioning_overrides"] = "off"
    advice["channels"] = {
        "shift_plan": True, "accept_lift": True,
        "shift_extend": False, "rest_window": False,
    }
    # Capture recommendations without forcing an actor to follow them.  The trace is
    # diagnostic, not a second treatment arm, and never owns simulator behaviour.
    advice["adherence_by_archetype"] = {
        archetype: 0.0 for archetype in ("P1", "P2", "P3", "P4", "P5", "P6", "P7")
    }
    config.data.setdefault("checkpoint_shadow", {})["enabled"] = True
    config.data["checkpoint_shadow"]["presentation_mode"] = "template"
    return run_once(config, int(seed))


class DemoSessionService:
    """Small in-process session store for one demo process.

    The completed ``RunResult`` is immutable from this service's perspective.  Only the
    selected actor/cursor/idempotency map changes, under the per-session lock.
    """

    def __init__(self, *, run_factory: Callable[[int], Any] | None = None,
                 session_id_factory: Callable[[], str] | None = None,
                 route_factory: Callable[[list[dict]], dict] | None = None,
                 checkpoint_store_path: str | Path | None = None):
        self.run_factory = run_factory or _default_run
        self.session_id_factory = session_id_factory or (lambda: str(uuid.uuid4()))
        self.route_factory = route_factory or _default_route
        if checkpoint_store_path is None:
            from app.adapters import mockdata
            checkpoint_store_path = mockdata.REPO_ROOT / "data" / "ui-telemetry" / "advice_checkpoint.db"
        self.checkpoint_store_path = Path(checkpoint_store_path)
        self.checkpoint_store_path.parent.mkdir(parents=True, exist_ok=True)
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

    def _checkpoint_for_actor(self, session: _DemoSession, checkpoint_id: str) -> dict:
        if session.selected_actor_id is None:
            raise DemoSessionConflict("chưa chọn actor")
        checkpoint = next((item for item in session.traces[session.selected_actor_id]["checkpoints"]
                           if item.get("checkpoint_id") == checkpoint_id), None)
        if checkpoint is None:
            raise DemoSessionNotFound("checkpoint không thuộc actor/session")
        return checkpoint

    def acknowledge_demo_display(self, session_id: str, checkpoint_id: str, *,
                                 display_id: str, client_event_id: str,
                                 mounted_at: str) -> dict:
        """Record mounted ACK for an explicitly internal demo replay.

        This endpoint is intentionally separate from the v2 feature flag: the demo bridge
        already served a trace-backed template envelope, while ``ADVICE_V2_ENABLED=0`` keeps
        the product polling API disabled.  Both paths write the same checkpoint stream.
        """
        session = self._get(session_id)
        with session.lock:
            self._checkpoint_for_actor(session, checkpoint_id)
            from app.services.advice_checkpoint import AdviceCheckpointService
            from gsm_core.lifecycle.checkpoint_store import CheckpointStore
            with CheckpointStore(self.checkpoint_store_path) as store:
                return AdviceCheckpointService(store).acknowledge_display(
                    checkpoint_id, display_id=display_id,
                    client_event_id=client_event_id, mounted_at=mounted_at)

    def record_demo_response(self, session_id: str, checkpoint_id: str, *,
                             display_id: str, client_event_id: str, response: str,
                             occurred_at: str) -> dict:
        session = self._get(session_id)
        with session.lock:
            self._checkpoint_for_actor(session, checkpoint_id)
            from app.services.advice_checkpoint import AdviceCheckpointService
            from gsm_core.lifecycle.checkpoint_store import CheckpointStore
            with CheckpointStore(self.checkpoint_store_path) as store:
                return AdviceCheckpointService(store).record_response(
                    checkpoint_id, display_id=display_id,
                    client_event_id=client_event_id, response=response,
                    occurred_at=occurred_at)

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
        advice = self._advice(session, transition.get("checkpoint"), transition["t_min"])
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

    def _advice(self, session: _DemoSession, checkpoint: dict | None,
                simulation_time_min: float) -> dict:
        if checkpoint is None:
            return {"status": "silent", "reason_code": "no_checkpoint"}
        # The simulator has already produced the exact snapshot/input/report.  Persist and
        # present that immutable record; never invoke ProductSolverOrchestrator on a click.
        from app.services.advice_checkpoint import AdviceCheckpointService, _iso_for_minute
        from gsm_core.lifecycle.checkpoint_store import CheckpointStore
        from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter
        import os

        generated_at = _iso_for_minute("2026-07-01", int(round(simulation_time_min)))
        try:
            artifact_by_id = {
                item["artifact_id"]: item
                for item in getattr(session.result, "advice_artifacts", [])
            }
            refs = [checkpoint.get("snapshot_ref"), checkpoint.get("solver_artifact_ref"),
                    *(checkpoint.get("solver_input_refs") or []),
                    *(checkpoint.get("solver_report_refs") or [])]
            artifacts = [artifact_by_id[ref] for ref in refs if ref in artifact_by_id]
            with CheckpointStore(self.checkpoint_store_path) as store:
                store.create_checkpoint_bundle(artifacts, checkpoint)
                # Replay the simulator's policy verdict exactly.  The bridge only creates
                # a READY event for hand-built traces that did not export lifecycle events;
                # it must not turn a queued/suppressed checkpoint into a card.
                for event in getattr(session.result, "advice_checkpoint_events", []):
                    if (event.get("checkpoint_id") == checkpoint.get("checkpoint_id")
                            and event.get("event_type") != "created"):
                        store.append_event(event)
                presenter = CheckpointPresenter(
                    mode=os.getenv("ADVICE_PRESENTATION_MODE", "template"))
                advice = AdviceCheckpointService(store, presenter=presenter).present_existing_checkpoint(
                    checkpoint["checkpoint_id"], surface=checkpoint["surface"],
                    generated_at=generated_at)
            return advice
        except Exception:
            # A failed bridge must not make replay unusable.  The canonical transition is
            # still returned, while this step remains an honest silent/fallback response.
            return {"status": "silent", "surface": checkpoint.get("surface", "nudge"),
                    "generated_at": generated_at,
                    "silent": {"reason_code": "presentation_fallback"}, "items": []}

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

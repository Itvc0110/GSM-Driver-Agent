"""Server-owned observer replay sessions for the unified Web demo."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

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
                 session_id_factory: Callable[[], str] | None = None):
        self.run_factory = run_factory or _default_run
        self.session_id_factory = session_id_factory or (lambda: str(uuid.uuid4()))
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

    @staticmethod
    def _step_response(session: _DemoSession, transition: dict) -> dict:
        trace = session.traces[session.selected_actor_id]
        return {
            "session_id": session.session_id,
            "run_id": trace["run_id"],
            "seed": trace["seed"],
            "actor_id": session.selected_actor_id,
            "step_version": session.step_version,
            "simulation_time_min": transition["t_min"],
            "transition": transition,
            "provenance": trace["provenance"],
        }


DEMO_SESSIONS = DemoSessionService()

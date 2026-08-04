"""HTTP boundary for the server-owned unified Web demo session."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.services.demo_session import (
    DEMO_SESSIONS,
    DemoSessionConflict,
    DemoSessionNotFound,
)
from app.services.advice_checkpoint import CheckpointConflictError, CheckpointNotFoundError


router = APIRouter()


class CreateSessionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seed: int = Field(default=1000, ge=0)


class SelectActorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_id: int = Field(ge=0)


class StepBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_step_id: str = Field(min_length=1, max_length=160)
    expected_step_version: int = Field(ge=0)


class DemoDisplayBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_id: str = Field(min_length=1)
    client_event_id: str = Field(min_length=1)
    mounted_at: datetime


class DemoResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_id: str = Field(min_length=1)
    client_event_id: str = Field(min_length=1)
    response: str = Field(pattern=r"^(accepted|dismissed|expanded)$")
    occurred_at: datetime


class DemoWhyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_id: str = Field(min_length=1)
    client_request_id: str = Field(min_length=1, max_length=160)
    expected_step_version: int | None = Field(default=None, ge=0)


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, DemoSessionNotFound):
        status = 410 if "completed" in str(exc) else 404
        return HTTPException(status_code=status, detail=str(exc))
    if isinstance(exc, DemoSessionConflict):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, CheckpointNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, CheckpointConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="demo_session_error")


@router.post("/sessions")
def create_session(body: CreateSessionBody):
    try:
        return DEMO_SESSIONS.create(seed=body.seed)
    except Exception as exc:  # keep simulation/provider errors explicit at the boundary
        raise _error(exc) from exc


@router.put("/sessions/{session_id}/driver")
def select_actor(session_id: str, body: SelectActorBody):
    try:
        return DEMO_SESSIONS.select_actor(session_id, body.actor_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/sessions/{session_id}/state")
def get_state(session_id: str):
    try:
        return DEMO_SESSIONS.state(session_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/sessions/{session_id}/steps")
def next_step(session_id: str, body: StepBody):
    try:
        return DEMO_SESSIONS.advance(
            session_id, client_step_id=body.client_step_id,
            expected_step_version=body.expected_step_version)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/sessions/{session_id}/advice/{checkpoint_id}/display")
def demo_display(session_id: str, checkpoint_id: str, body: DemoDisplayBody):
    try:
        return DEMO_SESSIONS.acknowledge_demo_display(
            session_id, checkpoint_id, display_id=body.display_id,
            client_event_id=body.client_event_id,
            mounted_at=body.mounted_at.isoformat())
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/sessions/{session_id}/advice/{checkpoint_id}/response")
def demo_response(session_id: str, checkpoint_id: str, body: DemoResponseBody):
    try:
        return DEMO_SESSIONS.record_demo_response(
            session_id, checkpoint_id, display_id=body.display_id,
            client_event_id=body.client_event_id, response=body.response,
            occurred_at=body.occurred_at.isoformat())
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/sessions/{session_id}/advice/{checkpoint_id}/why")
def demo_why(session_id: str, checkpoint_id: str, body: DemoWhyBody):
    try:
        return DEMO_SESSIONS.explain_demo_why(
            session_id, checkpoint_id, display_id=body.display_id,
            client_request_id=body.client_request_id,
            expected_step_version=body.expected_step_version)
    except Exception as exc:
        raise _error(exc) from exc

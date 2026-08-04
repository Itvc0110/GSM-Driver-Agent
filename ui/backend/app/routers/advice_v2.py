"""AdviceEnvelopeV2 HTTP boundary with presentation lease lifecycle."""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.adapters import mockdata
from app.services.advice_checkpoint import (
    AdviceCheckpointService,
    CheckpointConflictError,
    CheckpointNotFoundError,
    ProductSolverOrchestrator,
)
from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter
from gsm_core.lifecycle.checkpoint_store import CheckpointStore


router = APIRouter()
TELEMETRY_DIR = mockdata.REPO_ROOT / "data" / "ui-telemetry"
ORCHESTRATOR_FACTORY = ProductSolverOrchestrator
PRESENTER_FACTORY = lambda: CheckpointPresenter(
    mode=("template" if os.getenv("ADVICE_PRESENTATION_MODE", "template") == "internal_live"
          else os.getenv("ADVICE_PRESENTATION_MODE", "template")))


def _checkpoint_db() -> Path:
    return TELEMETRY_DIR / "advice_checkpoint.db"


def _enabled() -> bool:
    return os.getenv("ADVICE_V2_ENABLED", "0") == "1"


class AdviceV2Query(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surface: Literal["brief", "nudge", "recap"]
    driver_id: str = Field(min_length=1)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    now_min: int = Field(ge=0, le=1439)
    shift_start_min: int = Field(ge=0, le=1439)
    shift_end_min: int = Field(ge=0, le=2879)
    is_driving: bool

    @field_validator("date")
    @classmethod
    def valid_date(cls, value: str) -> str:
        date.fromisoformat(value)
        return value


class DisplayBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_id: str = Field(min_length=1)
    client_event_id: str = Field(min_length=1)
    mounted_at: datetime


class ResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_id: str = Field(min_length=1)
    client_event_id: str = Field(min_length=1)
    response: Literal["accepted", "dismissed", "expanded"]
    occurred_at: datetime


def _open_service() -> tuple[CheckpointStore, AdviceCheckpointService]:
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    store = CheckpointStore(_checkpoint_db())
    provider = None
    if (os.getenv("ADVICE_PRESENTATION_MODE", "template") == "internal_live"
            and os.getenv("ADVICE_AGENT_ALLOWLIST", "0") == "1"
            and os.getenv("ADVICE_AGENT_KILL_SWITCH", "0") != "1"):
        try:
            from gsm_core.advisor.advice_agent import OpenAIAdviceProvider
            provider = OpenAIAdviceProvider.from_env()
        except Exception:
            provider = None
    return store, AdviceCheckpointService(
        store, ORCHESTRATOR_FACTORY(), presenter=PRESENTER_FACTORY(),
        presentation_mode=os.getenv("ADVICE_PRESENTATION_MODE", "template"),
        agent_provider=provider)


@router.get("")
def get_advice(query: Annotated[AdviceV2Query, Query()]):
    if not _enabled():
        return JSONResponse(status_code=503,
                            content={"status": "disabled", "fallback": "v1"})
    store, service = _open_service()
    try:
        return service.get_advice(**query.model_dump())
    finally:
        store.close()


@router.post("/{checkpoint_id}/display")
def post_display(checkpoint_id: str, body: DisplayBody):
    if not _enabled():
        return JSONResponse(status_code=503,
                            content={"status": "disabled", "fallback": "v1"})
    store, service = _open_service()
    try:
        return service.acknowledge_display(
            checkpoint_id, display_id=body.display_id,
            client_event_id=body.client_event_id,
            mounted_at=body.mounted_at.isoformat())
    except CheckpointNotFoundError as exc:
        raise HTTPException(status_code=404, detail="checkpoint_not_found") from exc
    except CheckpointConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        store.close()


@router.post("/{checkpoint_id}/response")
def post_response(checkpoint_id: str, body: ResponseBody):
    if not _enabled():
        return JSONResponse(status_code=503,
                            content={"status": "disabled", "fallback": "v1"})
    store, service = _open_service()
    try:
        return service.record_response(
            checkpoint_id, display_id=body.display_id,
            client_event_id=body.client_event_id, response=body.response,
            occurred_at=body.occurred_at.isoformat())
    except CheckpointNotFoundError as exc:
        raise HTTPException(status_code=404, detail="checkpoint_not_found") from exc
    except CheckpointConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        store.close()

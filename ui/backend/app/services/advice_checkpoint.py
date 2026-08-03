"""Product orchestration for AdviceCheckpoint S1/S2 candidates.

S2 is capability-only until a trusted runtime provider supplies fresh SOC and
rest/shift state.  Analytics proxies (notably ``mockdata._soc_proxy``) are not
part of this module and cannot satisfy the gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as calendar_date
from datetime import datetime, timedelta
from typing import Callable, Literal, Protocol
import hashlib
import json
import time
import uuid

from app.adapters import advisor, mockdata
from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter, PresentationText
from gsm_core.features.from_l1r import derive_shift_plan_input_l1r
from gsm_core.lifecycle.checkpoint import normalize_solver_decision
from gsm_core.lifecycle.checkpoint import (
    PRESENTATION_TERMINAL_STATES,
    checkpoint_record,
    evaluate_checkpoint,
    select_primary_candidate,
)
from gsm_core.lifecycle.checkpoint_store import CheckpointStore, build_artifact_record
from gsm_core.schema_registry import L1R_ENTITIES, SchemaRegistry
from gsm_core.solvers import bonus_feasibility, shift_dp


@dataclass(frozen=True)
class ProductDriverRuntimeState:
    soc_pct: float
    rest_taken_min: float
    shift_elapsed_min: float
    observed_at: str
    freshness_deadline: str
    source: Literal["REAL", "LIVE"]


class RuntimeStateProvider(Protocol):
    def get_state(self, driver_id: str,
                  observed_at: str) -> ProductDriverRuntimeState | None: ...


class UnavailableRuntimeStateProvider:
    """Current product default: no trusted SOC/rest runtime feed is wired."""

    def get_state(self, driver_id: str,
                  observed_at: str) -> ProductDriverRuntimeState | None:
        return None


class StaticRuntimeStateProvider:
    """Trusted deterministic fixture/provider adapter used by integration tests."""

    def __init__(self, state: ProductDriverRuntimeState):
        self.state = state

    def get_state(self, driver_id: str,
                  observed_at: str) -> ProductDriverRuntimeState | None:
        return self.state


@dataclass
class ProductSolverResult:
    candidates: list[dict] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)
    solver_set: list[str] = field(default_factory=list)
    reasons: dict[str, str] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


def _default_l1r() -> dict[str, list[dict]]:
    return {entity: mockdata._table(entity).to_dicts() for entity in L1R_ENTITIES}


def _iso_for_minute(day: str, minute: int) -> str:
    base = calendar_date.fromisoformat(day) + timedelta(days=minute // 1440)
    minute_of_day = minute % 1440
    return (f"{base.isoformat()}T{minute_of_day // 60:02d}:"
            f"{minute_of_day % 60:02d}:00+07:00")


def _runtime_state_is_fresh(
        state: ProductDriverRuntimeState | None, now: datetime) -> bool:
    if state is None or state.source not in {"REAL", "LIVE"}:
        return False
    try:
        observed_at = datetime.fromisoformat(state.observed_at)
        freshness_deadline = datetime.fromisoformat(state.freshness_deadline)
    except (TypeError, ValueError):
        return False
    return observed_at <= now < freshness_deadline


def _snapshot(driver_id: str, t_now: str, shift_start_min: int,
              shift_end_min: int, *, freshness_deadline: str,
              data_mode: str, is_mock: bool,
              surface: str = "nudge",
              runtime_state: ProductDriverRuntimeState | None = None) -> dict:
    day = t_now[:10]
    snapshot = {
        "driver_id": driver_id,
        "surface": surface,
        "trigger_type": "poll",
        "observed_at": t_now,
        "freshness_deadline": freshness_deadline,
        "shift_start": _iso_for_minute(day, shift_start_min),
        "shift_end": _iso_for_minute(day, shift_end_min),
        "data_mode": data_mode,
        "is_mock": is_mock,
        "run_id": None,
    }
    if runtime_state is not None:
        snapshot["runtime_state"] = {
            "soc_pct": runtime_state.soc_pct,
            "rest_taken_min": runtime_state.rest_taken_min,
            "shift_elapsed_min": runtime_state.shift_elapsed_min,
            "observed_at": runtime_state.observed_at,
            "freshness_deadline": runtime_state.freshness_deadline,
            "source": runtime_state.source,
        }
    return snapshot


def _normalize_with_artifacts(solver_name: str, snapshot: dict, solver_input: dict,
                              solver_report: dict, source_decision_id: str
                              ) -> tuple[dict, list[dict]]:
    created_at = snapshot["observed_at"]
    data_mode = snapshot["data_mode"]
    is_mock = snapshot["is_mock"]
    artifacts = [
        build_artifact_record("state_snapshot", snapshot, data_mode, is_mock, created_at),
        build_artifact_record("solver_input", solver_input, data_mode, is_mock, created_at),
        build_artifact_record("solver_report", solver_report, data_mode, is_mock, created_at),
    ]
    combined = build_artifact_record("solver_artifact", {
        "solver_name": solver_name,
        "solver_input_ref": artifacts[1]["artifact_id"],
        "solver_report_ref": artifacts[2]["artifact_id"],
    }, data_mode, is_mock, created_at)
    artifacts.append(combined)
    candidate = normalize_solver_decision(
        solver_name, snapshot, solver_input, solver_report, source_decision_id)
    candidate["snapshot_ref"] = artifacts[0]["artifact_id"]
    candidate["solver_input_refs"] = [artifacts[1]["artifact_id"]]
    candidate["solver_report_refs"] = [artifacts[2]["artifact_id"]]
    candidate["solver_artifact_ref"] = combined["artifact_id"]
    return candidate, artifacts


class ProductSolverOrchestrator:
    def __init__(self, *, runtime_state_provider: RuntimeStateProvider | None = None,
                 l1r_provider: Callable[[], dict] | None = None):
        self.runtime_state_provider = (
            runtime_state_provider or UnavailableRuntimeStateProvider())
        self.l1r_provider = l1r_provider or _default_l1r
        self._registry = SchemaRegistry(mockdata.REPO_ROOT / "schemas")

    def solve(self, driver_id: str, t_now: str, shift_start_min: int,
              shift_end_min: int, surface: str = "nudge") -> ProductSolverResult:
        result = ProductSolverResult()
        policy = advisor.policy()
        now = datetime.fromisoformat(t_now)
        default_freshness = (now + timedelta(minutes=20)).isoformat()

        # S1 and S2 are isolated: either may fail without discarding the other.
        try:
            s1_input = advisor.build_gi(
                driver_id, t_now[:10], now.hour * 60 + now.minute, shift_end_min)
            s1_report = bonus_feasibility.solve(s1_input, policy)
            s1_snapshot = _snapshot(
                driver_id, t_now, shift_start_min, shift_end_min,
                freshness_deadline=default_freshness,
                data_mode="mock-realdata", is_mock=True, surface=surface)
            candidate, artifacts = _normalize_with_artifacts(
                "S1", s1_snapshot, s1_input, s1_report,
                f"s1-{driver_id}-{t_now[:10]}-{now.hour * 60 + now.minute}")
            result.candidates.append(candidate)
            result.artifacts.extend(artifacts)
            result.solver_set.append("S1")
        except Exception as exc:  # solver isolation boundary; surfaced in result
            result.reasons["S1"] = "solver_error"
            result.errors["S1"] = f"{type(exc).__name__}: {exc}"

        state = self.runtime_state_provider.get_state(driver_id, t_now)
        if not _runtime_state_is_fresh(state, now):
            result.reasons["S2"] = "missing_state"
            return result
        assert state is not None

        try:
            s2_input = derive_shift_plan_input_l1r(
                driver_id, t_now, self.l1r_provider(), policy)
            s2_input = {
                **s2_input,
                "schema_version": self._registry.schema_version("shift_plan_input"),
                "soc_pct": float(state.soc_pct),
                "rest_taken_min": float(state.rest_taken_min),
                "shift_elapsed_min": float(state.shift_elapsed_min),
            }
            errors = self._registry.validate("shift_plan_input", s2_input)
            if errors:
                raise ValueError(f"shift_plan_input latest không hợp lệ: {errors}")
            s2_report = shift_dp.solve(s2_input, policy)
            s2_snapshot = _snapshot(
                driver_id, t_now, shift_start_min, shift_end_min,
                freshness_deadline=state.freshness_deadline,
                data_mode="live", is_mock=False, surface=surface,
                runtime_state=state)
            candidate, artifacts = _normalize_with_artifacts(
                "S2", s2_snapshot, s2_input, s2_report,
                f"s2-{driver_id}-{t_now[:10]}-{now.hour * 60 + now.minute}")
            result.candidates.append(candidate)
            result.artifacts.extend(artifacts)
            result.solver_set.append("S2")
        except Exception as exc:  # independent from S1 by contract
            result.reasons["S2"] = "solver_error"
            result.errors["S2"] = f"{type(exc).__name__}: {exc}"
        return result


class CheckpointNotFoundError(LookupError):
    pass


class CheckpointConflictError(ValueError):
    pass


def _event(checkpoint: dict, event_type: str, occurred_at: str, *,
           event_id: str, display_id: str | None = None,
           actor: str = "advisor", origin: str = "product",
           reason_code: str | None = None, payload: dict | None = None) -> dict:
    return {
        "schema_version": "1.1.0",
        "event_id": event_id,
        "checkpoint_id": checkpoint["checkpoint_id"],
        "driver_id": checkpoint["driver_id"],
        "display_id": display_id,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "actor": actor,
        "origin": origin,
        "reason_code": reason_code,
        "relation_type": None,
        "confidence": None,
        "payload": payload or {},
    }


class AdviceCheckpointService:
    """Checkpoint orchestration, independent from the legacy v1 lifecycle store."""

    def __init__(self, store: CheckpointStore,
                 orchestrator: ProductSolverOrchestrator | None = None,
                 presenter: CheckpointPresenter | None = None):
        self.store = store
        self.orchestrator = orchestrator or ProductSolverOrchestrator()
        self.presenter = presenter or CheckpointPresenter(mode="template")

    def get_advice(self, *, surface: str, driver_id: str, date: str, now_min: int,
                   shift_start_min: int, shift_end_min: int,
                   is_driving: bool) -> dict:
        t_now = _iso_for_minute(date, now_min)
        solved = self.orchestrator.solve(
            driver_id, t_now, shift_start_min, shift_end_min, surface=surface)
        active = self.store.checkpoint_states(driver_id)
        cadence = self._cadence_memory(driver_id)
        ready: list[dict] = []
        silent_reasons: list[str] = []
        artifact_by_id = {a["artifact_id"]: a for a in solved.artifacts}

        for candidate in solved.candidates:
            existing = self.store.checkpoint(candidate["checkpoint_id"])
            if existing is not None:
                state = self.store.state(candidate["checkpoint_id"])["state"]
                valid_until = datetime.fromisoformat(existing["validity"]["valid_until"])
                if valid_until <= datetime.fromisoformat(t_now):
                    if state not in PRESENTATION_TERMINAL_STATES:
                        self.store.append_event(_event(
                            existing, "expired", t_now,
                            event_id=f"expired:{existing['checkpoint_id']}",
                            reason_code="expired"))
                    silent_reasons.append("expired")
                    continue
                if state == "queued" and not is_driving:
                    self.store.append_event(_event(
                        existing, "ready", t_now,
                        event_id=f"ready:{existing['checkpoint_id']}"))
                    ready.append({**candidate, **existing})
                elif state in {"ready", "generated", "generation_failed"}:
                    ready.append({**candidate, **existing})
                elif state in {"offered", "displayed"}:
                    lease = self.store.lease(existing["checkpoint_id"])
                    if lease is not None:
                        return self._envelope(existing, lease, surface, t_now)
                else:
                    silent_reasons.append("duplicate")
                continue

            policy = evaluate_checkpoint(
                candidate, active, cadence, t_now, is_driving=is_driving)
            for old_id in policy.superseded_checkpoint_ids:
                old = self.store.checkpoint(old_id)
                if old is not None and self.store.state(old_id)["state"] not in PRESENTATION_TERMINAL_STATES:
                    self.store.append_event(_event(
                        old, "superseded", t_now,
                        event_id=f"superseded:{old_id}:{candidate['checkpoint_id']}",
                        reason_code="material_change",
                        payload={"replacement_checkpoint_id": candidate["checkpoint_id"]}))
            checkpoint = checkpoint_record(candidate)
            refs = [checkpoint["snapshot_ref"], checkpoint["solver_artifact_ref"],
                    *checkpoint["solver_input_refs"], *checkpoint["solver_report_refs"]]
            bundle = [artifact_by_id[ref] for ref in refs if ref in artifact_by_id]
            self.store.create_checkpoint_bundle(bundle, checkpoint)
            self.store.append_event(_event(
                checkpoint, policy.verdict, t_now,
                event_id=f"{policy.verdict}:{checkpoint['checkpoint_id']}",
                reason_code=policy.reason))
            if policy.verdict == "ready":
                ready.append(candidate)
            else:
                silent_reasons.append(policy.reason or policy.verdict)
            active.append({**checkpoint, "state": policy.verdict,
                           "fingerprint": candidate.get("fingerprint")})

        if not ready:
            reason = ("unsafe_while_moving" if is_driving else
                      silent_reasons[0] if silent_reasons else
                      solved.reasons.get("S2") or solved.reasons.get("S1") or
                      "no_active_checkpoint")
            return self._silent(surface, t_now, reason)

        primary = select_primary_candidate(ready)
        assert primary is not None
        checkpoint = self.store.checkpoint(primary["checkpoint_id"])
        assert checkpoint is not None
        # Revalidate immediately before lease; solver/presenter work must not offer stale data.
        if datetime.fromisoformat(checkpoint["validity"]["valid_until"]) <= datetime.fromisoformat(t_now):
            self.store.append_event(_event(
                checkpoint, "expired", t_now,
                event_id=f"expired:{checkpoint['checkpoint_id']}", reason_code="expired"))
            return self._silent(surface, t_now, "expired")
        rendered = self._prepare_presentation(checkpoint, t_now, allow_shadow=True)
        if rendered is None:
            return self._silent(surface, t_now, "discarded_stale")
        lease_time = (datetime.fromisoformat(t_now) + timedelta(microseconds=1)).isoformat()
        lease = self.store.acquire_presentation_lease(
            checkpoint["checkpoint_id"], lease_time)
        return self._envelope(checkpoint, lease, surface, t_now, rendered=rendered)

    def acknowledge_display(self, checkpoint_id: str, *, display_id: str,
                            client_event_id: str, mounted_at: str) -> dict:
        return self._client_event(
            checkpoint_id, display_id=display_id, client_event_id=client_event_id,
            event_type="displayed", occurred_at=mounted_at, actor="client")

    def record_response(self, checkpoint_id: str, *, display_id: str,
                        client_event_id: str, response: str,
                        occurred_at: str) -> dict:
        return self._client_event(
            checkpoint_id, display_id=display_id, client_event_id=client_event_id,
            event_type=response, occurred_at=occurred_at, actor="driver")

    def _client_event(self, checkpoint_id: str, *, display_id: str,
                      client_event_id: str, event_type: str,
                      occurred_at: str, actor: str) -> dict:
        checkpoint = self.store.checkpoint(checkpoint_id)
        if checkpoint is None:
            raise CheckpointNotFoundError(checkpoint_id)
        lease = self.store.lease(checkpoint_id)
        if lease is None or lease["display_id"] != display_id:
            raise CheckpointConflictError("stale_or_unknown_lease")
        event = _event(
            checkpoint, event_type, occurred_at,
            event_id=f"client:{client_event_id}", display_id=display_id,
            actor=actor, origin="client")
        try:
            created = self.store.append_event(event)
        except ValueError as exc:
            # Transition and conflicting idempotency errors are both HTTP 409 at the router.
            raise CheckpointConflictError(str(exc)) from exc
        return {"ok": True, "idempotent_replay": not created,
                "checkpoint_id": checkpoint_id, "display_id": display_id,
                "event_type": event_type}

    def _cadence_memory(self, driver_id: str) -> dict:
        last: dict[str, str] = {}
        offered_ids: set[str] = set()
        dismissed: set[str] = set()
        for checkpoint in self.store.checkpoints(driver_id):
            for event in self.store.events(checkpoint["checkpoint_id"]):
                if event["event_type"] == "offered":
                    offered_ids.add(checkpoint["checkpoint_id"])
                    previous = last.get(checkpoint["topic"])
                    if previous is None or event["occurred_at"] > previous:
                        last[checkpoint["topic"]] = event["occurred_at"]
                elif event["event_type"] == "dismissed":
                    dismissed.add(checkpoint["topic"])
        return {"proactive_count": len(offered_ids),
                "last_offered_by_topic": last,
                "dismissed_topics": sorted(dismissed)}

    def _presentation_inputs(self, checkpoint: dict) -> tuple[list[dict], list[dict], list[dict]]:
        report_ref = (checkpoint.get("solver_report_refs") or [None])[0]
        report_artifact = self.store.artifact(report_ref) if report_ref else None
        report = (report_artifact or {}).get("payload") or {}
        numbers = [{
            "id": f"N{index + 1}",
            "value": number.get("value"),
            "unit": number.get("unit"),
            "source": number.get("source"),
            "artifact_ref": report_ref,
        } for index, number in enumerate(report.get("numbers") or [])]
        facts = [{"id": "F1", "value": str(checkpoint["reason_code"]).replace("_", " ")}]
        caveats = [{"id": f"C{index + 1}", "value": value}
                   for index, value in enumerate(report.get("caveats") or [])]
        return facts, numbers, caveats

    def _prepare_presentation(self, checkpoint: dict, generated_at: str, *,
                              allow_shadow: bool) -> tuple[PresentationText, list[dict], list[dict]] | None:
        facts, numbers, caveats = self._presentation_inputs(checkpoint)
        presenter = self.presenter if allow_shadow else CheckpointPresenter(mode="template")
        template = CheckpointPresenter(mode="template").present(
            checkpoint, facts=facts, numbers=numbers, caveats=caveats)
        if allow_shadow and presenter.mode == "shadow" and presenter.agent is not None:
            material = {
                "fingerprint": checkpoint.get("fingerprint") or checkpoint["checkpoint_id"],
                "facts_digest": hashlib.sha256(json.dumps(
                    {"facts": facts, "numbers": numbers, "caveats": caveats},
                    sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                "locale": "vi-VN",
                "prompt_version": "checkpoint-presenter-v1",
                "model_version": str(getattr(
                    presenter.agent, "model_version", type(presenter.agent).__name__)),
                "policy_version": advisor.policy().version,
            }
            cache_key = hashlib.sha256(json.dumps(
                material, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            cached = self.store.generation_cache_get(cache_key, generated_at)
            if cached is not None:
                self._record_shadow_metric(
                    checkpoint, generated_at, cache_hit=True, avoided_calls=1,
                    fallback=cached.get("shadow_output") is None)
                rendered = PresentationText(
                    title=template.title, summary=template.summary, why=template.why,
                    fallback_used=True,
                    verify_errors=tuple(cached.get("verify_errors") or ()),
                    agent_output=cached.get("agent_output"),
                    shadow_output=cached.get("shadow_output"))
                return rendered, numbers, caveats
            owner_id = str(uuid.uuid4())
            valid_until = checkpoint["validity"]["valid_until"]
            if not self.store.claim_generation(
                    cache_key, owner_id, generated_at, valid_until):
                self._record_shadow_metric(
                    checkpoint, generated_at, cache_hit=False, avoided_calls=1,
                    fallback=True)
                return template, numbers, caveats
            started = time.perf_counter()
            rendered = presenter.present(
                checkpoint, facts=facts, numbers=numbers, caveats=caveats)
            latency_ms = (time.perf_counter() - started) * 1000
            state = self.store.state(checkpoint["checkpoint_id"])["state"]
            stale = (state in PRESENTATION_TERMINAL_STATES
                     or datetime.fromisoformat(checkpoint["validity"]["valid_until"])
                     <= datetime.fromisoformat(generated_at))
            evaluation = build_artifact_record(
                "agent_shadow_output", {
                    "checkpoint_id": checkpoint["checkpoint_id"],
                    "status": "discarded_stale" if stale else
                              "verified" if rendered.shadow_output is not None else "fallback",
                    "agent_output": rendered.agent_output,
                    "shadow_output": rendered.shadow_output,
                    "verify_errors": list(rendered.verify_errors),
                }, checkpoint["data_mode"], checkpoint["is_mock"], generated_at)
            self.store.put_artifact_record(evaluation)
            usage = getattr(presenter.agent, "last_usage", None) or {}
            self._record_shadow_metric(
                checkpoint, generated_at, cache_hit=False, avoided_calls=0,
                stale_discard=stale, fallback=rendered.shadow_output is None,
                latency_ms=latency_ms,
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                cost_usd=usage.get("cost_usd"))
            if stale:
                self.store.release_generation_claim(cache_key, owner_id)
                return None
            self.store.put_generation_cache(cache_key, owner_id, {
                "agent_output": rendered.agent_output,
                "shadow_output": rendered.shadow_output,
                "verify_errors": list(rendered.verify_errors),
            }, valid_until)
        else:
            rendered = template
        return rendered, numbers, caveats

    def _record_shadow_metric(
            self, checkpoint: dict, occurred_at: str, *, cache_hit: bool,
            avoided_calls: int, stale_discard: bool = False,
            fallback: bool, latency_ms: float | None = None,
            input_tokens: int | None = None, output_tokens: int | None = None,
            cost_usd: float | None = None) -> None:
        self.store.append_presentation_metric({
            "occurred_at": occurred_at,
            "checkpoint_id": checkpoint["checkpoint_id"],
            "cache_hit": cache_hit,
            "avoided_calls": avoided_calls,
            "stale_discard": stale_discard,
            "fallback": fallback,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
        })

    def _envelope(self, checkpoint: dict, lease: dict, surface: str,
                  generated_at: str,
                  rendered: tuple[PresentationText, list[dict], list[dict]] | None = None
                  ) -> dict:
        action = checkpoint.get("current_action") or {"code": "NO_ACTION",
                                                       "label_id": "action.no_action"}
        rendered = rendered or self._prepare_presentation(
            checkpoint, generated_at, allow_shadow=False)
        assert rendered is not None
        presentation, numbers, caveats = rendered
        caveat_ids = [item["id"] for item in caveats]
        item = {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "display_id": lease["display_id"],
            "topic": checkpoint["topic"],
            "surface": surface,
            "canonical_action": action,
            "action_window": checkpoint.get("action_window"),
            "future_plan": checkpoint.get("future_plan") or [],
            "title": presentation.title,
            "summary": presentation.summary,
            "why": presentation.why,
            "validity": checkpoint["validity"],
            "confidence_band": checkpoint["confidence_band"],
            "caveat_ids": caveat_ids,
            "numbers": numbers,
            "provenance": {
                "snapshot_ref": checkpoint["snapshot_ref"],
                "solver_input_refs": checkpoint["solver_input_refs"],
                "solver_report_refs": checkpoint["solver_report_refs"],
                "policy_version": advisor.policy().version,
                "checkpoint_schema_version": checkpoint["schema_version"],
                "data_mode": checkpoint["data_mode"],
                "is_mock": checkpoint["is_mock"],
            },
            "solver_set": checkpoint["solver_set"],
            "response_options": ["accepted", "dismissed", "expanded"],
        }
        return {"status": "ready", "surface": surface,
                "generated_at": generated_at, "items": [item]}

    @staticmethod
    def _silent(surface: str, generated_at: str, reason: str) -> dict:
        return {"status": "silent", "surface": surface,
                "generated_at": generated_at,
                "silent": {"reason_code": reason}, "items": []}

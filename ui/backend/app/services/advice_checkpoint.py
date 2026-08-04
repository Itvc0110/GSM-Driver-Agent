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
from gsm_core.advisor.advice_agent import (
    AgentRequest, AdviceAgentProvider, ProviderResult, build_agent_request,
)
from gsm_core.advisor.checkpoint_presenter import (
    CheckpointPresenter, PresentationText, _render, build_agent_input,
    build_explanation_input, verify_agent_output, verify_explanation_output,
)
from gsm_core.advisor.presentation_strategy import decide_presentation
from gsm_core.features.from_l1r import derive_shift_plan_input_l1r
from gsm_core.lifecycle.checkpoint import normalize_solver_decision
from gsm_core.lifecycle.checkpoint import (
    PRESENTATION_TERMINAL_STATES,
    checkpoint_record,
    evaluate_checkpoint,
    select_primary_candidate,
)
from gsm_core.lifecycle.advice_topics import classify
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


@dataclass(frozen=True)
class PreparedPresentation:
    text: PresentationText
    numbers: list[dict]
    caveats: list[dict]
    metadata: dict


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


class CheckpointSoftAdviceError(ValueError):
    """Cố ghi một dấu vết ĐỒNG THUẬN cho lời khuyên KHUYÊN MỀM (QĐ-1/QĐ-4).

    Lớp RIÊNG chứ không dùng lại `CheckpointConflictError`: conflict là *"trạng thái không cho phép
    lúc này"* (409, thử lại có thể được); còn đây là *"việc này vĩnh viễn không được phép"* (422).
    Gộp hai cái sẽ dạy người đọc rằng cứ thử lại là qua — sai hẳn bản chất một ranh giới.
    """


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
                 presenter: CheckpointPresenter | None = None,
                 *, presentation_mode: str | None = None,
                 agent_provider: AdviceAgentProvider | None = None,
                 why_agent_enabled: bool | None = None):
        self.store = store
        self.orchestrator = orchestrator or ProductSolverOrchestrator()
        self.presenter = presenter or CheckpointPresenter(mode="template")
        self.presentation_mode = presentation_mode or __import__("os").getenv(
            "ADVICE_PRESENTATION_MODE", "template")
        if self.presentation_mode not in {"template", "shadow", "internal_live"}:
            raise ValueError("ADVICE_PRESENTATION_MODE chỉ nhận template|shadow|internal_live")
        self.agent_provider = agent_provider
        self.why_agent_enabled = (
            why_agent_enabled if why_agent_enabled is not None else
            __import__("os").getenv("ADVICE_WHY_AGENT_ENABLED", "0") == "1")
        # Preserve direct P5 shadow fixtures while the new strategy is opt-in via an
        # explicit mode/provider.  Production default remains template-only.
        self._legacy_shadow = (
            presentation_mode is None and agent_provider is None
            and self.presenter.mode == "shadow")

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
        rendered = self._prepare_presentation(
            checkpoint, t_now, allow_shadow=True, is_driving=is_driving)
        if rendered is None:
            return self._silent(surface, t_now,
                                "unsafe_while_moving" if is_driving else "discarded_stale")
        presentation_artifact = self._persist_presentation_artifact(
            checkpoint, surface, rendered, t_now)
        lease_time = (datetime.fromisoformat(t_now) + timedelta(microseconds=5)).isoformat()
        lease = self.store.acquire_presentation_lease(
            checkpoint["checkpoint_id"], lease_time,
            presentation=self._lease_presentation_metadata(presentation_artifact))
        return self._envelope(checkpoint, lease, surface, t_now, rendered=rendered)

    def present_existing_checkpoint(self, checkpoint_id: str, *, surface: str,
                                    generated_at: str, is_driving: bool = False) -> dict:
        """Present a checkpoint already produced by a simulator trace.

        This bridge deliberately skips ``ProductSolverOrchestrator.solve``.  The trace is
        the source of the exact snapshot/input/report; this method only replays lifecycle,
        presenter/verifier and immutable lease semantics in the existing checkpoint store.
        """
        checkpoint = self.store.checkpoint(checkpoint_id)
        if checkpoint is None:
            raise CheckpointNotFoundError(checkpoint_id)
        if checkpoint.get("driver_id") is None:
            raise CheckpointConflictError("checkpoint_missing_driver")
        if is_driving:
            return self._silent(surface, generated_at, "unsafe_while_moving")
        state = self.store.state(checkpoint_id)["state"]
        valid_until = checkpoint.get("validity", {}).get("valid_until")
        if valid_until is None:
            return self._silent(surface, generated_at, "missing_validity")
        if datetime.fromisoformat(valid_until) <= datetime.fromisoformat(generated_at):
            if state not in PRESENTATION_TERMINAL_STATES:
                self.store.append_event(_event(
                    checkpoint, "expired", generated_at,
                    event_id=f"expired:{checkpoint_id}", reason_code="expired"))
            return self._silent(surface, generated_at, "expired")
        if state in PRESENTATION_TERMINAL_STATES:
            return self._silent(surface, generated_at, state)
        if state in {"offered", "displayed"}:
            # A replay retry must return the immutable lease presentation.  Do not
            # regenerate text merely because the cursor revisited this transition.
            lease = self.store.lease(checkpoint_id)
            if lease is None:
                return self._silent(surface, generated_at, "missing_lease")
            return self._envelope(checkpoint, lease, surface, generated_at)
        if state == "created":
            self.store.append_event(_event(
                checkpoint, "ready", generated_at,
                event_id=f"ready:{checkpoint_id}"))
        elif state not in {"ready", "generated", "generation_failed"}:
            # A replay transition is only allowed to present a checkpoint that the
            # simulator/policy marked displayable.  In particular, queued advice must
            # not acquire a lease merely because a Web cursor reached its timestamp.
            return self._silent(surface, generated_at, state)
        rendered = self._prepare_presentation(
            checkpoint, generated_at, allow_shadow=True, is_driving=is_driving)
        if rendered is None:
            return self._silent(surface, generated_at,
                                "unsafe_while_moving" if is_driving else "discarded_stale")
        presentation_artifact = self._persist_presentation_artifact(
            checkpoint, surface, rendered, generated_at)
        lease_time = (datetime.fromisoformat(generated_at)
                      + timedelta(microseconds=5)).isoformat()
        try:
            lease = self.store.acquire_presentation_lease(
                checkpoint_id, lease_time,
                presentation=self._lease_presentation_metadata(presentation_artifact))
        except (KeyError, ValueError) as exc:
            raise CheckpointConflictError(str(exc)) from exc
        return self._envelope(checkpoint, lease, surface, generated_at, rendered=rendered)

    def acknowledge_display(self, checkpoint_id: str, *, display_id: str,
                            client_event_id: str, mounted_at: str) -> dict:
        return self._client_event(
            checkpoint_id, display_id=display_id, client_event_id=client_event_id,
            event_type="displayed", occurred_at=mounted_at, actor="client")

    def record_response(self, checkpoint_id: str, *, display_id: str,
                        client_event_id: str, response: str,
                        occurred_at: str) -> dict:
        # 🔴 QĐ-4 bước 2 (Cường chốt 2026-08-04) — RANH GIỚI KHUYÊN MỀM, không phải chi tiết kỹ thuật.
        #
        # Đây là đường ghi THỨ TƯ vào một store hành vi (UI v1 · sim · pipeline · **v2**). Ba đường
        # kia đã bị chặn từ UPDATE-135/129; đường này thì chưa, vì v2 có store riêng
        # (`CheckpointStore`) và từ vựng topic riêng — hai bên **giao nhau = RỖNG**, nên
        # `classify()` không chạm được một event nào của v2.
        #
        # Hậu quả đo được 2026-08-04: một checkpoint `rest` nhận được `response: accepted` ⇒ hệ
        # thống ĐANG GHI TRACE ĐỒNG Ý cho lời khuyên NGHỈ — đúng thứ QĐ-1 cấm. Chưa sinh số sai
        # (store v2 chưa vào `adherence_view`), nhưng dữ liệu **tích luỹ**: ngày ai đó tính
        # adherence trên store này, tỷ lệ hiện ra ngay với lịch sử đầy đủ.
        #
        # ⚠ ĐÍNH CHÍNH (soi độc lập 2026-08-04): bản đầu của comment này ghi *"`rest` sinh bởi S7"*.
        # SAI ở đường sản phẩm — `ProductSolverOrchestrator` chỉ chạy S1/S2 (xem `:176`, `:210`), và
        # contract cấm solver khác (`advice_v2.json` → `solver_set.enum=["S1","S2"]`). Ở đây `rest`
        # sinh từ **S2** qua nhánh `code == "REST"` (`checkpoint.py:134`). S7 chỉ sống ở sim.
        # Lỗ hổng có thật, nhưng qua một producer khác — và cổng đầu-cuối bản đầu vì thế đã canh
        # một kịch bản BẤT KHẢ. Đã sửa: `ui/backend/tests/test_v2_soft_advice_no_trace.py`.
        #
        # `dismissed`/`expanded` VẪN nhận: `dismissed` = *"đừng nhắc nữa"* (nhịp nói), không phải
        # *"tôi không đồng ý"*; chặn nó sẽ làm tài xế mất cách tắt thẻ phiền. Chỉ `accepted` bị cấm —
        # nó chỉ có MỘT nghĩa, và nghĩa đó là sự đồng thuận, tức thước nghe-lời.
        # Xem `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md` §6b.
        if response == "accepted":
            checkpoint = self.store.checkpoint(checkpoint_id)
            topic = (checkpoint or {}).get("topic")
            # `topic is None` ⇒ để `_client_event` trả `CheckpointNotFoundError` (404) — không nuốt
            # một checkpoint không tồn tại thành lỗi ranh giới, vì hai thứ đó cần hai thông điệp.
            lop = classify(topic) if topic is not None else "measured"
            if lop == "soft":
                raise CheckpointSoftAdviceError(
                    f"topic {topic!r} là KHUYÊN MỀM — không ghi được `accepted`. Khuyên mềm được "
                    f"nói vì đúng cho tài xế, KHÔNG kèm phép đo mức nghe lời: đo nó là biến sức "
                    f"khoẻ/an toàn thành chỉ tiêu để tối ưu (§1.2c). Dùng `dismissed` nếu ý là "
                    f"'đừng nhắc nữa' — đó là nhịp nói, không phải sự đồng thuận.")
            # FAIL-CLOSED cho topic CHƯA KHAI — cùng luật với `adherence_view` (Cường chốt
            # 2026-08-03: *"TREO kết quả, như D-M3-10"*). Nếu ở đây fail-OPEN thì ranh giới có hai
            # tiêu chuẩn cho cùng một tình huống: tầng ĐỌC loại topic lạ, tầng GHI lại nhận nó.
            #
            # Đánh đổi đã cân, không phải chọn cho gọn: chặn ở đây là lỗi **thấy được** (một cú bấm
            # nhận 422), còn cho qua là lỗi **im lặng** — và nếu topic lạ đó hoá ra là lời khuyên sức
            # khoẻ (`fatigue`, `hydration`…) thì cái im lặng ấy chính là trace đồng thuận mà QĐ-1
            # cấm. Không cùng hạng.
            #
            # Trong thực tế nhánh này **không tới được ở bản ship**: topic chỉ sinh từ
            # `_topic_for_action`, và ba cổng ở `tests/test_advice_topic_registry.py` ĐỎ ngay khi có
            # topic chưa khai. Nó là lan can cho khoảng thời gian giữa "vừa thêm topic" và "chạy
            # test" — đúng khoảng mà mọi lỗi họ này đã chui qua.
            if lop == "unknown":
                raise CheckpointSoftAdviceError(
                    f"topic {topic!r} CHƯA được phân loại trong `advice_topics.py` ⇒ chưa ai quyết "
                    f"nó là lời khuyên KINH TẾ (đo mức nghe lời được) hay KHUYÊN MỀM (không đo). "
                    f"Fail-closed: không ghi `accepted` cho tới khi có người quyết. Đọc "
                    f"`tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md` §6b.")
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
                              allow_shadow: bool,
                              is_driving: bool = False) -> PreparedPresentation | None:
        facts, numbers, caveats = self._presentation_inputs(checkpoint)
        template = CheckpointPresenter(mode="template").present(
            checkpoint, facts=facts, numbers=numbers, caveats=caveats)
        template_result = PreparedPresentation(
            template, numbers, caveats,
            {"presentation_source": "template", "template_version": "checkpoint-template-v1",
             "model_version": None, "prompt_version": None,
             "schema_version": "1.0.0", "verifier_version": "checkpoint-verifier-v1"})

        # A direct P5 shadow presenter remains available for old replay fixtures.  New
        # callers use the deterministic strategy/provider path below.
        if allow_shadow and self._legacy_shadow:
            return self._prepare_legacy_shadow(
                checkpoint, generated_at, template_result, facts, numbers, caveats)

        decision = decide_presentation(
            checkpoint, facts=facts, numbers=numbers, caveats=caveats,
            mode=self.presentation_mode,
            provider_enabled=self.agent_provider is not None,
            is_driving=is_driving)
        if decision.strategy != "LLM" or not allow_shadow or self.agent_provider is None:
            return template_result if decision.strategy != "SILENT" else None
        return self._prepare_agent_generation(
            checkpoint, generated_at, template_result, facts, numbers, caveats,
            reason_code=decision.reason_code)

    def _prepare_legacy_shadow(
            self, checkpoint: dict, generated_at: str,
            template_result: PreparedPresentation, facts: list[dict],
            numbers: list[dict], caveats: list[dict]) -> PreparedPresentation | None:
        presenter = self.presenter
        material = {
            "request_type": "proactive",
            "fingerprint": checkpoint.get("fingerprint") or checkpoint["checkpoint_id"],
            "facts_digest": hashlib.sha256(json.dumps(
                {"facts": facts, "numbers": numbers, "caveats": caveats},
                sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "locale": "vi-VN", "prompt_version": "checkpoint-presenter-v1",
            "model_version": str(getattr(
                presenter.agent, "model_version", type(presenter.agent).__name__)),
            "schema_version": "1.0.0", "verifier_version": "checkpoint-verifier-v1",
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
                title=template_result.text.title, summary=template_result.text.summary,
                why=template_result.text.why, fallback_used=True,
                verify_errors=tuple(cached.get("verify_errors") or ()),
                agent_output=cached.get("agent_output"),
                shadow_output=cached.get("shadow_output"))
            return PreparedPresentation(rendered, numbers, caveats,
                                        template_result.metadata)
        owner_id = str(uuid.uuid4())
        valid_until = checkpoint["validity"]["valid_until"]
        if not self.store.claim_generation(cache_key, owner_id, generated_at, valid_until):
            self._record_shadow_metric(
                checkpoint, generated_at, cache_hit=False, avoided_calls=1, fallback=True)
            return template_result
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
            latency_ms=latency_ms, input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"), cost_usd=usage.get("cost_usd"))
        if stale:
            self.store.release_generation_claim(cache_key, owner_id)
            return None
        self.store.put_generation_cache(cache_key, owner_id, {
            "agent_output": rendered.agent_output,
            "shadow_output": rendered.shadow_output,
            "verify_errors": list(rendered.verify_errors),
        }, valid_until)
        return PreparedPresentation(rendered, numbers, caveats, template_result.metadata)

    def _prepare_agent_generation(
            self, checkpoint: dict, generated_at: str,
            template_result: PreparedPresentation, facts: list[dict],
            numbers: list[dict], caveats: list[dict], *,
            reason_code: str) -> PreparedPresentation | None:
        provider = self.agent_provider
        assert provider is not None
        try:
            input_payload = build_agent_input(
                checkpoint, facts=facts, numbers=numbers, caveats=caveats)
        except Exception:
            return template_result
        model_version = str(getattr(provider, "model_version", "unknown"))
        material = {
            "request_type": "proactive",
            "fingerprint": checkpoint.get("fingerprint") or checkpoint["checkpoint_id"],
            "facts_digest": hashlib.sha256(json.dumps(
                {"facts": facts, "numbers": numbers, "caveats": caveats},
                sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "locale": "vi-VN", "surface": checkpoint.get("surface", "nudge"),
            "prompt_version": "advice-checkpoint-v1", "model_version": model_version,
            "schema_version": input_payload["schema_version"],
            "verifier_version": "checkpoint-verifier-v1",
            "policy_version": advisor.policy().version,
        }
        cache_key = hashlib.sha256(json.dumps(
            material, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        cached = self.store.generation_cache_get(cache_key, generated_at)
        if cached is not None:
            self._record_shadow_metric(
                checkpoint, generated_at, cache_hit=True, avoided_calls=1,
                fallback=cached.get("status") != "verified")
            return self._prepared_from_agent_cache(
                template_result, cached, numbers, caveats)
        owner_id = str(uuid.uuid4())
        valid_until = checkpoint["validity"]["valid_until"]
        if not self.store.claim_generation(cache_key, owner_id, generated_at, valid_until):
            self._record_shadow_metric(
                checkpoint, generated_at, cache_hit=False, avoided_calls=1, fallback=True)
            return template_result
        try:
            generation_started_at = (
                datetime.fromisoformat(generated_at) + timedelta(microseconds=1)).isoformat()
            self.store.append_event(_event(
                checkpoint, "generation_started", generation_started_at,
                event_id=f"generation_started:{checkpoint['checkpoint_id']}:{cache_key[:12]}",
                reason_code=reason_code))
        except ValueError:
            self.store.release_generation_claim(cache_key, owner_id)
            return template_result
        started = time.perf_counter()
        errors: list[str] = []
        accepted = None
        usage: dict = {}
        provider_result: ProviderResult | Any | None = None
        try:
            request = build_agent_request(
                input_payload, request_type="proactive",
                prompt_version=material["prompt_version"],
                policy_version=material["policy_version"], model_version=model_version)
            provider_result = provider.generate(request)
            raw = provider_result.output if isinstance(provider_result, ProviderResult) \
                else provider_result
            accepted, errors = verify_agent_output(
                raw, checkpoint, facts=facts, numbers=numbers, caveats=caveats)
            if accepted is None and hasattr(provider, "repair"):
                repaired = provider.repair(request, errors)
                accepted, errors = verify_agent_output(
                    repaired, checkpoint, facts=facts, numbers=numbers, caveats=caveats)
            if isinstance(provider_result, ProviderResult):
                usage = provider_result.usage or {}
        except Exception as exc:
            errors = [f"provider_error:{type(exc).__name__}"]
        latency_ms = (time.perf_counter() - started) * 1000
        state = self.store.state(checkpoint["checkpoint_id"])["state"]
        stale = (state in PRESENTATION_TERMINAL_STATES
                 or datetime.fromisoformat(checkpoint["validity"]["valid_until"])
                 <= datetime.fromisoformat(generated_at) or state == "superseded")
        if stale:
            self.store.release_generation_claim(cache_key, owner_id)
            evaluation = build_artifact_record(
                "agent_shadow_output", {
                    "checkpoint_id": checkpoint["checkpoint_id"],
                    "status": "discarded_stale", "reason_code": reason_code,
                    "agent_output": accepted, "verify_errors": errors,
                }, checkpoint["data_mode"], checkpoint["is_mock"], generated_at)
            self.store.put_artifact_record(evaluation)
            self._record_shadow_metric(
                checkpoint, generated_at, cache_hit=False, avoided_calls=0,
                stale_discard=True, fallback=True, latency_ms=latency_ms,
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                cost_usd=usage.get("cost_usd"))
            return None
        if accepted is None:
            try:
                generation_finished_at = (
                    datetime.fromisoformat(generated_at) + timedelta(microseconds=2)).isoformat()
                self.store.append_event(_event(
                    checkpoint, "generation_failed", generation_finished_at,
                    event_id=f"generation_failed:{checkpoint['checkpoint_id']}:{cache_key[:12]}",
                    reason_code=errors[0] if errors else "verifier_rejected"))
            except ValueError:
                pass
            status = "fallback"
            prepared = template_result
        else:
            try:
                generation_finished_at = (
                    datetime.fromisoformat(generated_at) + timedelta(microseconds=2)).isoformat()
                self.store.append_event(_event(
                    checkpoint, "generated", generation_finished_at,
                    event_id=f"generated:{checkpoint['checkpoint_id']}:{cache_key[:12]}",
                    reason_code=reason_code))
            except ValueError:
                self.store.release_generation_claim(cache_key, owner_id)
                return template_result
            rendered_text = _render(accepted, facts, numbers, caveats)
            status = "verified"
            prepared = PreparedPresentation(
                PresentationText(
                    title=template_result.text.title,
                    summary=rendered_text["summary"], why=rendered_text["why"],
                    fallback_used=False, verify_errors=(),
                    agent_output=accepted, shadow_output=None),
                numbers, caveats,
                {"presentation_source": "agent", "template_version": None,
                 "model_version": model_version,
                 "prompt_version": material["prompt_version"],
                 "schema_version": input_payload["schema_version"],
                 "verifier_version": material["verifier_version"]})
        evaluation = build_artifact_record(
            "agent_shadow_output", {
                "checkpoint_id": checkpoint["checkpoint_id"], "status": status,
                "reason_code": reason_code, "agent_output": accepted,
                "verify_errors": errors,
            }, checkpoint["data_mode"], checkpoint["is_mock"], generated_at)
        self.store.put_artifact_record(evaluation)
        self._record_shadow_metric(
            checkpoint, generated_at, cache_hit=False, avoided_calls=0,
            fallback=accepted is None, latency_ms=latency_ms,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"), cost_usd=usage.get("cost_usd"))
        self.store.put_generation_cache(cache_key, owner_id, {
            "status": status, "agent_output": accepted,
            "summary": prepared.text.summary, "why": prepared.text.why,
            "verify_errors": errors, "metadata": prepared.metadata,
        }, valid_until)
        # In shadow mode the driver still receives the deterministic template.  The
        # verified output is retained only in the evaluation artifact/cache.
        if self.presentation_mode == "shadow":
            return template_result
        return prepared

    @staticmethod
    def _prepared_from_agent_cache(template_result: PreparedPresentation,
                                   cached: dict, numbers: list[dict],
                                   caveats: list[dict]) -> PreparedPresentation:
        if cached.get("status") != "verified":
            return template_result
        metadata = dict(cached.get("metadata") or {})
        rendered = PresentationText(
            title=template_result.text.title,
            summary=cached.get("summary") or template_result.text.summary,
            why=cached.get("why") or template_result.text.why,
            fallback_used=False, verify_errors=(),
            agent_output=cached.get("agent_output"), shadow_output=None)
        return PreparedPresentation(rendered, numbers, caveats, metadata)

    def explain_why(self, checkpoint_id: str, *, display_id: str,
                    client_request_id: str, generated_at: str,
                    is_driving: bool = False) -> dict:
        """Lazily explain an already-offered card; never solve or create a checkpoint."""
        if not client_request_id:
            raise ValueError("client_request_id không được rỗng")
        checkpoint = self.store.checkpoint(checkpoint_id)
        if checkpoint is None:
            raise CheckpointNotFoundError(checkpoint_id)
        lease = self.store.lease(checkpoint_id)
        if lease is None or lease.get("display_id") != display_id:
            raise CheckpointConflictError("stale_or_unknown_lease")
        if is_driving:
            return {"status": "silent", "checkpoint_id": checkpoint_id,
                    "display_id": display_id, "client_request_id": client_request_id,
                    "silent": {"reason_code": "unsafe_while_moving"}}

        state = self.store.state(checkpoint_id)["state"]
        validity_until = checkpoint.get("validity", {}).get("valid_until")
        historical = state in {"expired", "superseded", "accepted", "dismissed"}
        if validity_until:
            try:
                historical = historical or datetime.fromisoformat(validity_until) \
                    <= datetime.fromisoformat(generated_at)
            except (TypeError, ValueError):
                historical = True
        artifact = (self.store.artifact(lease.get("presentation_artifact_id"))
                    if lease.get("presentation_artifact_id") else None)
        item = ((artifact or {}).get("payload") or {}).get("item") or {
            "title": "Lời khuyên", "summary": "Lời khuyên đã được tạo từ trạng thái có nguồn.",
        }
        facts, numbers, caveats = self._presentation_inputs(checkpoint)
        try:
            input_payload = build_explanation_input(
                checkpoint, display_id=display_id, facts=facts, numbers=numbers,
                caveats=caveats, presentation=item, checkpoint_status=state,
                is_historical=historical)
        except Exception:
            input_payload = None

        context_digest = hashlib.sha256(json.dumps({
            "checkpoint_id": checkpoint_id, "display_id": display_id,
            "content_digest": lease.get("content_digest"),
            "historical": historical, "schema_version": "1.0.0",
        }, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        previous = self.store.explanation_request(client_request_id)
        if previous is not None:
            if previous["context_digest"] != context_digest:
                raise CheckpointConflictError("client_request_id explanation context conflict")
            return previous["record"]

        response: dict
        if input_payload is None:
            response = self._why_fallback(
                checkpoint_id, display_id, client_request_id, historical,
                reason="invalid_context")
        elif not self.why_agent_enabled or self.agent_provider is None:
            response = self._why_fallback(
                checkpoint_id, display_id, client_request_id, historical,
                reason="llm_disabled")
        else:
            response = self._generate_why(
                checkpoint, lease, input_payload, facts, numbers, caveats,
                client_request_id=client_request_id, generated_at=generated_at,
                historical=historical)
        try:
            self.store.put_explanation_request(client_request_id, context_digest, response)
        except ValueError as exc:
            raise CheckpointConflictError(str(exc)) from exc
        try:
            self.store.append_event(_event(
                checkpoint, "expanded", generated_at,
                event_id=f"expanded:{client_request_id}", display_id=display_id,
                actor="driver", origin="client",
                payload={"client_request_id": client_request_id,
                         "is_historical": historical}))
        except ValueError:
            # Explanation is a side channel.  A terminal transition must not erase the
            # already-returnable response; duplicate/cross-state events are audited.
            pass
        return response

    @staticmethod
    def _why_fallback(checkpoint_id: str, display_id: str, client_request_id: str,
                      historical: bool, *, reason: str) -> dict:
        text = ("Lời giải thích này dựa trên trạng thái và kế hoạch tại thời điểm hiển thị. "
                "Hành động và thời gian phía trên do hệ thống tính toán.")
        if historical:
            text += " Đây là giải thích lịch sử, không phải lời khuyên hiện hành."
        return {
            "status": "ready", "checkpoint_id": checkpoint_id,
            "display_id": display_id, "client_request_id": client_request_id,
            "explanation": text, "used_fact_ids": [], "used_number_ids": [],
            "used_caveat_ids": [], "presentation_source": "template",
            "is_historical": historical, "no_reoffer": historical,
            "fallback": True, "reason_code": reason,
        }

    def _generate_why(self, checkpoint: dict, lease: dict, input_payload: dict,
                      facts: list[dict], numbers: list[dict], caveats: list[dict], *,
                      client_request_id: str, generated_at: str,
                      historical: bool) -> dict:
        provider = self.agent_provider
        assert provider is not None
        model_version = str(getattr(provider, "model_version", "unknown"))
        material = {
            "request_type": "why_explanation",
            "checkpoint_fingerprint": checkpoint.get("fingerprint") or checkpoint["checkpoint_id"],
            "display_id": lease["display_id"], "content_digest": lease.get("content_digest"),
            "facts_digest": hashlib.sha256(json.dumps(
                {"facts": facts, "numbers": numbers, "caveats": caveats},
                sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            "locale": input_payload["locale"], "prompt_version": "advice-why-v1",
            "model_version": model_version, "schema_version": input_payload["schema_version"],
            "verifier_version": "checkpoint-verifier-v1",
        }
        cache_key = "why_explanation:" + hashlib.sha256(json.dumps(
            material, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        cached = self.store.generation_cache_get(cache_key, generated_at)
        if cached is not None:
            cached_response = dict(cached.get("response") or {})
            cached_response["client_request_id"] = client_request_id
            return cached_response
        claim_owner = str(uuid.uuid4())
        now = datetime.fromisoformat(generated_at)
        valid_until = checkpoint.get("validity", {}).get("valid_until")
        expiry = max(
            datetime.fromisoformat(valid_until) if valid_until else now,
            now + timedelta(days=1))
        if not self.store.claim_generation(cache_key, claim_owner, generated_at,
                                           expiry.isoformat()):
            return self._why_fallback(
                checkpoint["checkpoint_id"], lease["display_id"], client_request_id,
                historical, reason="generation_claim_busy")
        accepted = None
        errors: list[str] = []
        try:
            request = build_agent_request(
                input_payload, request_type="explain_why",
                prompt_version=material["prompt_version"],
                policy_version=advisor.policy().version, model_version=model_version)
            provider_result = provider.generate(request)
            raw = provider_result.output if isinstance(provider_result, ProviderResult) \
                else provider_result
            accepted, errors = verify_explanation_output(
                raw, checkpoint, display_id=lease["display_id"],
                facts=facts, numbers=numbers, caveats=caveats)
        except Exception as exc:
            errors = [f"provider_error:{type(exc).__name__}"]
        if accepted is None:
            response = self._why_fallback(
                checkpoint["checkpoint_id"], lease["display_id"], client_request_id,
                historical, reason=errors[0] if errors else "verifier_rejected")
        else:
            explanation = _render({
                "reason_template": accepted["explanation_template"],
                "why_template": accepted["explanation_template"],
            }, facts, numbers, caveats)["why"]
            response = {
                "status": "ready", "checkpoint_id": checkpoint["checkpoint_id"],
                "display_id": lease["display_id"], "client_request_id": client_request_id,
                "explanation": explanation,
                "used_fact_ids": accepted["used_fact_ids"],
                "used_number_ids": accepted["used_number_ids"],
                "used_caveat_ids": accepted["used_caveat_ids"],
                "presentation_source": "agent", "is_historical": historical,
                "no_reoffer": historical, "fallback": False,
            }
        artifact = build_artifact_record(
            "agent_explanation", {
                "checkpoint_id": checkpoint["checkpoint_id"],
                "display_id": lease["display_id"],
                "request_type": "why_explanation",
                "status": "verified" if accepted is not None else "fallback",
                "output": accepted,
                "reason_code": response.get("reason_code"),
                "model_version": model_version,
                "prompt_version": material["prompt_version"],
                "verifier_version": material["verifier_version"],
            }, checkpoint["data_mode"], checkpoint["is_mock"], generated_at)
        self.store.put_artifact_record(artifact)
        self.store.put_generation_cache(cache_key, claim_owner,
                                        {"response": response}, expiry.isoformat())
        return response

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

    def _persist_presentation_artifact(
            self, checkpoint: dict, surface: str,
            rendered: PreparedPresentation,
            created_at: str) -> dict:
        presentation, numbers, caveats = rendered.text, rendered.numbers, rendered.caveats
        metadata = rendered.metadata
        item = self._presentation_item(
            checkpoint, surface, presentation, numbers, caveats, display_id=None)
        payload = {
            "schema_version": "1.0.0",
            "presentation_source": metadata.get("presentation_source", "template"),
            "template_version": metadata.get("template_version"),
            "model_version": metadata.get("model_version"),
            "prompt_version": metadata.get("prompt_version"),
            "verifier_version": metadata.get("verifier_version", "checkpoint-verifier-v1"),
            "policy_version": advisor.policy().version,
            "title": presentation.title,
            "summary": presentation.summary,
            "why": presentation.why,
            "item": item,
        }
        record = build_artifact_record(
            "presentation", payload, checkpoint["data_mode"],
            checkpoint["is_mock"], created_at)
        self.store.put_artifact_record(record)
        return record

    @staticmethod
    def _lease_presentation_metadata(record: dict) -> dict:
        payload = record["payload"]
        return {
            "presentation_artifact_id": record["artifact_id"],
            "content_digest": record["digest"],
            "presentation_source": payload["presentation_source"],
            "template_version": payload["template_version"],
            "model_version": payload["model_version"],
            "prompt_version": payload["prompt_version"],
            "schema_version": payload["schema_version"],
            "verifier_version": payload["verifier_version"],
            "policy_version": payload["policy_version"],
        }

    @staticmethod
    def _presentation_item(checkpoint: dict, surface: str,
                           presentation: PresentationText, numbers: list[dict],
                           caveats: list[dict], display_id: str | None) -> dict:
        action = checkpoint.get("current_action") or {"code": "NO_ACTION",
                                                       "label_id": "action.no_action"}
        caveat_ids = [item["id"] for item in caveats]
        return {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "display_id": display_id,
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

    def _envelope(self, checkpoint: dict, lease: dict, surface: str,
                  generated_at: str,
                  rendered: PreparedPresentation | None = None
                  ) -> dict:
        source = lease.get("presentation_source", "template")
        artifact_id = lease.get("presentation_artifact_id")
        if artifact_id:
            artifact = self.store.artifact(artifact_id)
            if artifact is not None and artifact.get("digest") == lease.get("content_digest"):
                payload = artifact.get("payload") or {}
                pinned_item = dict(payload.get("item") or {})
                if pinned_item.get("checkpoint_id") == checkpoint["checkpoint_id"]:
                    pinned_item["display_id"] = lease["display_id"]
                    return {"status": "ready", "surface": surface,
                            "generated_at": generated_at,
                            "presentation_source": source,
                            "items": [pinned_item]}
        rendered = rendered or self._prepare_presentation(
            checkpoint, generated_at, allow_shadow=False)
        assert rendered is not None
        presentation, numbers, caveats = rendered.text, rendered.numbers, rendered.caveats
        item = self._presentation_item(
            checkpoint, surface, presentation, numbers, caveats,
            display_id=lease["display_id"])
        return {"status": "ready", "surface": surface,
                "generated_at": generated_at, "presentation_source": source,
                "items": [item]}

    @staticmethod
    def _silent(surface: str, generated_at: str, reason: str) -> dict:
        return {"status": "silent", "surface": surface,
                "generated_at": generated_at,
                "silent": {"reason_code": reason}, "items": []}

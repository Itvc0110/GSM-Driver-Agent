"""P4 structured checkpoint presenter/verifier adversarial gate."""

from __future__ import annotations

import inspect

import pytest


def checkpoint(action="SWAP"):
    return {
        "checkpoint_id": "ckpt-1", "surface": "nudge", "topic": "energy",
        "current_action": {"code": action, "label_id": f"action.{action.lower()}"},
        "action_window": None, "urgency_band": "medium",
        "confidence_band": "high", "reason_code": "solver_recommendation",
    }


def registries():
    return (
        [{"id": "F1", "value": "trạng thái pin runtime đã đủ"}],
        [{"id": "N1", "value": 37.5, "unit": "percent", "source": "LIVE"}],
        [{"id": "C1", "value": "Ước tính có điều kiện"}],
    )


class Agent:
    def __init__(self, output, repair=None):
        self.output = output
        self.repair_output = repair
        self.generate_calls = 0
        self.repair_calls = 0

    def generate(self, payload):
        self.generate_calls += 1
        if isinstance(self.output, Exception):
            raise self.output
        return self.output

    def repair(self, payload, errors):
        self.repair_calls += 1
        return self.repair_output


def valid_output():
    return {
        "schema_version": "1.0.0", "checkpoint_id": "ckpt-1",
        "reason_template": "Dữ liệu {{F1}}.",
        "why_template": "Mức {{N1}} chỉ là ước tính; lưu ý {{C1}}.",
        "used_fact_ids": ["F1"], "used_number_ids": ["N1"],
        "used_caveat_ids": ["C1"],
    }


def test_presenter_is_side_effect_free_and_agent_only_enriches_text():
    from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter

    facts, numbers, caveats = registries()
    output = CheckpointPresenter(agent=Agent(valid_output()), mode="shadow").present(
        checkpoint(), facts=facts, numbers=numbers, caveats=caveats)

    assert output.fallback_used is True
    assert "37,5%" in output.shadow_output["why"]
    assert set(output.__dict__) == {
        "title", "summary", "why", "fallback_used", "verify_errors",
        "agent_output", "shadow_output",
    }
    source = inspect.getsource(__import__(
        "gsm_core.advisor.checkpoint_presenter", fromlist=["x"]))
    assert "CheckpointStore" not in source and "EpisodeStore" not in source


@pytest.mark.parametrize("bad", [
    "{not json",
    {**valid_output(), "unknown": True},
    {**valid_output(), "used_number_ids": ["N404"]},
    {**valid_output(), "why_template": "Pin còn 99 phần trăm."},
    {**valid_output(), "why_template": "Hãy nghỉ thay vì đổi pin."},
    {**valid_output(), "why_template":
        "Hãy đổi pin trước cuối ca; {{N1}} chỉ là ước tính; {{C1}}."},
    {**valid_output(), "why_template": "Cuốc này nên nhận ngay."},
    {**valid_output(), "why_template": "Chắc chắn anh/chị sẽ kiếm thêm tiền."},
    {**valid_output(), "why_template": "立即 đổi pin."},
    {**valid_output(), "why_template": "<script>{{N1}} {{C1}}</script>"},
    {**valid_output(), "why_template": "x\u0007 {{N1}} {{C1}}"},
    {**valid_output(), "why_template": "x" * 281},
])
def test_adversarial_outputs_fall_back_without_changing_canonical_fields(bad):
    from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter

    facts, numbers, caveats = registries()
    output = CheckpointPresenter(agent=Agent(bad), mode="shadow").present(
        checkpoint(), facts=facts, numbers=numbers, caveats=caveats)

    assert output.fallback_used is True
    assert output.title == "Chuẩn bị đổi pin"
    assert output.agent_output is None and output.shadow_output is None


def test_timeout_falls_back_and_one_repair_is_the_hard_limit():
    from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter

    facts, numbers, caveats = registries()
    timed_out = CheckpointPresenter(
        agent=Agent(TimeoutError("slow")), mode="shadow").present(
        checkpoint(), facts=facts, numbers=numbers, caveats=caveats)
    assert timed_out.fallback_used is True

    agent = Agent({**valid_output(), "checkpoint_id": "wrong"}, repair=valid_output())
    repaired = CheckpointPresenter(agent=agent, mode="shadow").present(
        checkpoint(), facts=facts, numbers=numbers, caveats=caveats)
    assert repaired.fallback_used is True
    assert repaired.shadow_output is not None
    assert agent.generate_calls == 1 and agent.repair_calls == 1


def test_template_mode_never_calls_agent():
    from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter

    agent = Agent(AssertionError("must not call"))
    facts, numbers, caveats = registries()
    output = CheckpointPresenter(agent=agent, mode="template").present(
        checkpoint(), facts=facts, numbers=numbers, caveats=caveats)
    assert output.fallback_used is True
    assert agent.generate_calls == 0


def test_agent_input_contains_typed_current_and_future_plan_context():
    from gsm_core.advisor.checkpoint_presenter import build_agent_input
    from gsm_core.schema_registry import SchemaRegistry
    from pathlib import Path

    value = checkpoint("ONLINE")
    value["future_plan"] = [{
        "code": "SWAP", "label_id": "action.swap",
        "window": {"start": "2026-08-04T10:00:00+07:00",
                    "end": "2026-08-04T11:00:00+07:00"},
    }]
    facts, numbers, caveats = registries()
    payload = build_agent_input(value, facts=facts, numbers=numbers, caveats=caveats)

    assert payload["current_action"] == payload["canonical_action"]
    assert payload["future_plan"][0]["code"] == "SWAP"
    errors = SchemaRegistry(Path(__file__).parents[1] / "schemas").validate(
        "agent_presentation_input", payload)
    assert errors == []


def test_verifier_rejects_future_action_as_current_and_fabricated_target():
    from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter

    value = checkpoint("ONLINE")
    value["future_plan"] = [{"code": "SWAP", "label_id": "action.swap"}]
    facts, numbers, caveats = registries()
    for text in ("Hãy đổi pin ngay.", "Đi tới trạm gần nhất.", "Khu vực này tốt hơn."):
        bad = {**valid_output(), "checkpoint_id": "ckpt-1", "why_template": text}
        output = CheckpointPresenter(agent=Agent(bad), mode="shadow").present(
            value, facts=facts, numbers=numbers, caveats=caveats)
        assert output.agent_output is None


def test_explanation_contract_is_closed_and_keeps_display_identity():
    from gsm_core.advisor.checkpoint_presenter import (
        build_explanation_input, verify_explanation_output,
    )
    from gsm_core.schema_registry import SchemaRegistry
    from pathlib import Path

    value = checkpoint("SWAP")
    facts, numbers, caveats = registries()
    payload = build_explanation_input(
        value, display_id="display-1", facts=facts, numbers=numbers, caveats=caveats,
        presentation={"title": "Pin", "summary": "Đổi pin"}, checkpoint_status="displayed",
        is_historical=False)
    assert SchemaRegistry(Path(__file__).parents[1] / "schemas").validate(
        "agent_explanation_input", payload) == []
    output, errors = verify_explanation_output({
        "schema_version": "1.0.0", "checkpoint_id": "ckpt-1",
        "display_id": "display-1", "explanation_template": "Vì {{F1}}.",
        "used_fact_ids": ["F1"], "used_number_ids": [], "used_caveat_ids": [],
    }, value, display_id="display-1", facts=facts, numbers=numbers, caveats=caveats)
    assert errors == [] and output["display_id"] == "display-1"

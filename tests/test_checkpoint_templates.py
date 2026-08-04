from __future__ import annotations


def _checkpoint(action="SWAP", *, future=None, topic="energy", reason="soc_low"):
    return {
        "checkpoint_id": "ckpt-template-1",
        "surface": "nudge",
        "topic": topic,
        "reason_code": reason,
        "current_action": {"code": action, "label_id": f"action.{action.lower()}"},
        "future_plan": future or [],
        "action_window": None,
    }


def test_registry_renders_s1_progress_from_typed_number_registry():
    from gsm_core.advisor.checkpoint_templates import CheckpointTemplateRegistry

    result = CheckpointTemplateRegistry().resolve(
        _checkpoint("PROTECT_ELIGIBILITY", topic="bonus_eligibility",
                    reason="bonus_gap"),
        facts=[{"id": "F1", "value": "còn thiếu mốc"}],
        numbers=[{"id": "N1", "value": 3, "unit": "trips", "source": "S1"}],
        caveats=[], locale="vi-VN", surface="nudge")

    assert result.template_key == "S1_BONUS_PROGRESS"
    assert "3" in result.summary
    assert result.required_number_ids == ("N1",)


def test_registry_keeps_online_now_and_swap_future_separate():
    from gsm_core.advisor.checkpoint_templates import CheckpointTemplateRegistry

    result = CheckpointTemplateRegistry().resolve(
        _checkpoint("ONLINE", future=[{
            "code": "SWAP", "label_id": "action.swap",
            "window": {"start": "2026-08-04T10:00:00+07:00",
                        "end": "2026-08-04T11:00:00+07:00"},
        }]), facts=[], numbers=[], caveats=[], locale="vi-VN", surface="nudge")

    assert result.template_key == "S2_ONLINE_NOW_SWAP_LATER"
    assert "Bây giờ: Tiếp tục online." in result.summary
    assert "Sắp tới: Đổi pin trong khung 10:00–11:00." in result.summary
    assert "Hãy đổi pin ngay" not in result.summary


def test_registry_unknown_action_uses_explicit_safe_fallback():
    from gsm_core.advisor.checkpoint_templates import CheckpointTemplateRegistry

    result = CheckpointTemplateRegistry().resolve(
        _checkpoint("NO_ACTION", topic="policy_info", reason="policy_info"),
        facts=[], numbers=[], caveats=[], locale="vi-VN", surface="brief")

    assert result.template_key == "FALLBACK_NO_ACTION"
    assert result.fallback_reason == "unknown_or_unsupported_template"

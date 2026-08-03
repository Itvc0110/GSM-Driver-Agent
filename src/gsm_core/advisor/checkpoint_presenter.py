"""Side-effect-free structured presenter for immutable AdviceCheckpoints."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gsm_core.advisor._text import normalize_vi
from gsm_core.schema_registry import SchemaRegistry
from gsm_core.vn_format import render_number_vn


_REGISTRY = SchemaRegistry(Path(__file__).resolve().parents[3] / "schemas")
_PLACEHOLDER = re.compile(r"\{\{([FNC]\d+)\}\}")
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

_TEMPLATE = {
    "PROTECT_ELIGIBILITY": (
        "Bảo vệ điều kiện thưởng", "Giữ tỷ lệ đủ điều kiện theo chính sách hiện hành.",
        "Điều kiện thưởng được đánh giá lại theo kết quả cuối ca."),
    "REST": ("Nghỉ trong khung này", "Ưu tiên nghỉ trong cửa sổ đang còn hiệu lực.",
             "Kế hoạch đã tính trạng thái nghỉ và thời gian trong ca."),
    "SWAP": ("Chuẩn bị đổi pin", "Đổi pin trong cửa sổ được đề xuất.",
             "Trạng thái runtime cho thấy cần bảo vệ phần ca còn lại."),
    "END": ("Kết ca", "Kết ca theo ranh giới kế hoạch hiện tại.",
            "Chạy thêm không cải thiện kế hoạch hiện tại."),
    "EXTEND": ("Cân nhắc kéo dài ca", "Kéo dài trong giới hạn đang hiển thị.",
               "Mốc kế tiếp còn nằm trong trần kéo dài đã khóa."),
    "ONLINE": ("Tiếp tục online", "Giữ trạng thái online trong khung hiện tại.",
               "Đây là trạng thái duy trì, không phải chỉ định vị trí."),
}

_ACTION_WORDS = {
    "PROTECT_ELIGIBILITY": ("bao ve dieu kien", "giu ty le"),
    "REST": ("nghi",),
    "SWAP": ("doi pin", "sac pin"),
    "END": ("ket ca", "dung ca"),
    "EXTEND": ("keo dai ca", "chay them"),
    "ONLINE": ("online", "tiep tuc chay"),
}


@dataclass(frozen=True)
class PresentationText:
    title: str
    summary: str
    why: str
    fallback_used: bool
    verify_errors: tuple[str, ...]
    agent_output: dict | None
    shadow_output: dict | None


def build_agent_input(checkpoint: dict, *, facts: list[dict], numbers: list[dict],
                      caveats: list[dict], locale: str = "vi-VN") -> dict:
    payload = {
        "schema_version": "1.0.0",
        "checkpoint_id": checkpoint["checkpoint_id"],
        "surface": checkpoint["surface"],
        "locale": locale,
        "topic": checkpoint["topic"],
        "canonical_action": checkpoint["current_action"],
        "action_window": checkpoint.get("action_window"),
        "facts": facts,
        "numbers": [{k: item[k] for k in ("id", "value", "unit", "source")}
                    for item in numbers],
        "confidence_band": checkpoint["confidence_band"],
        "caveats": caveats,
        "summary_max_chars": 120,
        "why_max_chars": 280,
    }
    errors = _REGISTRY.validate("agent_presentation_input", payload)
    if errors:
        raise ValueError(f"agent presentation input không hợp lệ: {errors}")
    return payload


def verify_agent_output(raw: Any, checkpoint: dict, *, facts: list[dict],
                        numbers: list[dict], caveats: list[dict]
                        ) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    if isinstance(raw, str):
        try:
            output = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            return None, [f"malformed_json:{exc}"]
    elif isinstance(raw, dict):
        output = dict(raw)
    else:
        return None, ["output_not_object"]

    errors.extend(_REGISTRY.validate("agent_presentation_output", output))
    if errors:
        return None, errors
    if output["checkpoint_id"] != checkpoint["checkpoint_id"]:
        errors.append("checkpoint_id_mismatch")

    registries = {
        "F": {item["id"] for item in facts},
        "N": {item["id"] for item in numbers},
        "C": {item["id"] for item in caveats},
    }
    used = {
        "F": set(output["used_fact_ids"]),
        "N": set(output["used_number_ids"]),
        "C": set(output["used_caveat_ids"]),
    }
    text = output["reason_template"] + " " + output["why_template"]
    placeholders = set(_PLACEHOLDER.findall(text))
    for prefix in ("F", "N", "C"):
        referenced = {value for value in placeholders if value.startswith(prefix)}
        if not used[prefix] <= registries[prefix]:
            errors.append(f"unknown_{prefix.lower()}_id")
        if referenced != used[prefix]:
            errors.append(f"used_{prefix.lower()}_ids_mismatch")

    without_placeholders = _PLACEHOLDER.sub("", text)
    if re.search(r"\d", without_placeholders):
        errors.append("fabricated_number")
    if _CJK.search(text):
        errors.append("cjk_not_allowed")

    normalized = normalize_vi(without_placeholders)
    if any(phrase in normalized for phrase in
           ("cuoc nay", "nhan cuoc", "tu choi cuoc", "huy cuoc")):
        errors.append("specific_trip_advice")
    if any(phrase in normalized for phrase in
           ("chac chan", "dam bao", "se kiem", "cam ket thu nhap")):
        errors.append("income_promise")
    if checkpoint.get("urgency_band") not in {"high", "critical"} and any(
            phrase in normalized for phrase in ("lap tuc", "khan cap", "ngay bay gio")):
        errors.append("urgency_conflict")
    if any(phrase in normalized for phrase in (
            "truoc cuoi ca", "sau cuoi ca", "trong khung", "trong vong",
            "hom nay", "ngay mai")):
        errors.append("window_conflict")

    canonical = (checkpoint.get("current_action") or {}).get("code")
    for action, phrases in _ACTION_WORDS.items():
        if action != canonical and any(phrase in normalized for phrase in phrases):
            errors.append("action_conflict")
            break
    return (None, errors) if errors else (output, [])


def _render(output: dict, facts: list[dict], numbers: list[dict],
            caveats: list[dict]) -> dict:
    values = {item["id"]: item["value"] for item in [*facts, *caveats]}
    values.update({item["id"]: render_number_vn(item["value"], item["unit"])
                   for item in numbers})

    def replace(template: str) -> str:
        return _PLACEHOLDER.sub(lambda match: str(values[match.group(1)]), template)

    return {"summary": replace(output["reason_template"]),
            "why": replace(output["why_template"])}


class CheckpointPresenter:
    def __init__(self, *, agent=None, mode: str = "template"):
        if mode not in {"template", "shadow"}:
            raise ValueError("presentation_mode chỉ nhận template|shadow")
        self.agent = agent
        self.mode = mode

    def present(self, checkpoint: dict, *, facts: list[dict], numbers: list[dict],
                caveats: list[dict], locale: str = "vi-VN") -> PresentationText:
        action = (checkpoint.get("current_action") or {}).get("code", "NO_ACTION")
        title, summary, why = _TEMPLATE.get(
            action, ("Gợi ý cho ca hiện tại", "Xem kế hoạch đang còn hiệu lực.",
                     "Gợi ý được tạo từ solver và dữ liệu có nguồn."))
        errors: list[str] = []
        accepted = None
        shadow = None
        if self.mode == "shadow" and self.agent is not None:
            payload = build_agent_input(
                checkpoint, facts=facts, numbers=numbers, caveats=caveats, locale=locale)
            try:
                raw = self.agent.generate(payload)
                accepted, errors = verify_agent_output(
                    raw, checkpoint, facts=facts, numbers=numbers, caveats=caveats)
                if accepted is None and hasattr(self.agent, "repair"):
                    repaired = self.agent.repair(payload, errors)
                    accepted, errors = verify_agent_output(
                        repaired, checkpoint, facts=facts, numbers=numbers, caveats=caveats)
                if accepted is not None:
                    shadow = _render(accepted, facts, numbers, caveats)
            except Exception as exc:  # provider boundary: model failure never escapes to card path
                errors = [f"agent_error:{type(exc).__name__}"]
                accepted = None
        return PresentationText(
            title=title, summary=summary, why=why, fallback_used=True,
            verify_errors=tuple(errors), agent_output=accepted,
            shadow_output=shadow)

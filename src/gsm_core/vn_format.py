"""Định dạng số theo locale VN — MỘT nguồn sự thật.

Trước đây `render_number_vn` chỉ nằm ở `advisor/context_pack.py`, nên digest của solver
tự format bằng `f"{x:,}"` → ra "100,000đ" (dấu phẩy) trong khi message hiển thị
"100.000đ" (dấu chấm). Cùng một con số, hai định dạng. Tách ra đây để solver (tầng dưới)
dùng chung mà KHÔNG phải import ngược từ tầng advisor.
"""

from __future__ import annotations


def format_vnd(value) -> str:
    """1234567 → '1.234.567đ' (chuẩn VN: dấu chấm phân nhóm nghìn)."""
    return f"{int(round(float(value))):,}".replace(",", ".") + "đ"


def render_number_vn(value: float, unit: str) -> str:
    """CODE render số theo locale VN — LLM không bao giờ tự format số."""
    if unit == "vnd":
        return format_vnd(value)
    if unit == "points":
        return f"{int(round(value))} điểm"
    if unit == "hours":
        return f"{value:.1f}".replace(".", ",") + " giờ"
    if unit == "trips":
        return f"{int(round(value))} cuốc"
    if unit == "ratio":
        return f"{value:.0%}"
    if unit == "minutes":
        return f"{int(round(value))} phút"
    if unit == "count":
        return f"{int(round(value))}"
    return f"{value:g} {unit}"

"""U4 — tokens và theme.css không được trôi nhau.

`ui/design-tokens.json` là MỘT nguồn style (web CSS vars + Flutter ThemeData).
theme.css hiện viết tay từ tokens — test này bắt mọi giá trị màu cốt lõi của
tokens phải xuất hiện trong CSS; ai đổi một phía mà quên phía kia thì đỏ.
"""

from __future__ import annotations

import json
from pathlib import Path

UI_DIR = Path(__file__).resolve().parents[2]
TOKENS = json.loads((UI_DIR / "design-tokens.json").read_text(encoding="utf-8"))
CSS = (UI_DIR / "web" / "theme.css").read_text(encoding="utf-8").lower()


def test_brand_colors_present_in_css():
    b = TOKENS["brand"]
    for key in ("accent", "accent_hover", "accent_soft", "ink", "page_bg", "surface"):
        assert b[key].lower() in CSS, f"brand.{key} ({b[key]}) không có trong theme.css"


def test_categorical_light_present_in_css():
    for name, tok in TOKENS["dataviz"]["categorical_light"].items():
        assert tok["hex"].lower() in CSS, \
            f"categorical_light.{name} ({tok['hex']}) không có trong theme.css"


def test_radius_tokens_present():
    r = TOKENS["radius"]
    for key in ("card", "sheet", "chip"):
        assert r[key] in CSS, f"radius.{key} ({r[key]}) không có trong theme.css"


def test_accent_never_used_as_series_in_tokens():
    """Ranh giới taste-skill: cyan brand là chrome accent, KHÔNG phải màu series."""
    accent = TOKENS["brand"]["accent"].lower()
    for name, tok in TOKENS["dataviz"]["categorical_light"].items():
        assert tok["hex"].lower() != accent, f"series {name} đang dùng accent brand"

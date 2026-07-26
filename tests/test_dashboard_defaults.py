"""AUDIT A1 BEHAV-2 — default slider dashboard phải BÁM CONFIG, không hardcode.

Bug gốc: dashboard hardcode default thời SIM-1 (accept_logit_center 6000, slider max
12000) trong khi config recalibrate 21200 ⇒ MỌI run từ dashboard dùng kinh tế học cũ,
reviewer nhìn dashboard thấy hành vi khác CLI. Test này đỏ nếu default lệch config
hoặc range slider không chứa giá trị hiệu chỉnh (module defaults không cần streamlit).
"""

from __future__ import annotations

import pytest

from gsm_sim.config import Config
from gsm_sim.dashboard_defaults import SLIDER_KEYS, slider_defaults

CFG = "configs/pilot_dongda.yaml"


@pytest.fixture(scope="module")
def cfg():
    return Config.load(CFG)


def test_every_slider_default_equals_config(cfg):
    d = slider_defaults(cfg)
    for key in SLIDER_KEYS:
        assert d[key] == cfg.get(key), f"slider {key} default lệch config"


def test_calibrated_center_inside_slider_range(cfg):
    """Chính bug BEHAV-2: 21200 phải nằm TRONG range slider (cũ max=12000 thì kẹt)."""
    lo, hi = SLIDER_KEYS["behavior.accept_logit_center_vnd"]
    assert lo <= cfg.get("behavior.accept_logit_center_vnd") <= hi


def test_out_of_range_config_raises(cfg):
    """Đổi config vượt range slider phải NỔ ngay khi mở dashboard, không âm thầm kẹp."""
    import copy
    c2 = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    c2.data["behavior"]["accept_logit_center_vnd"] = 999_999
    with pytest.raises(ValueError, match="ngoài range"):
        slider_defaults(c2)

"""D-M3-08 cơ chế 1 — POLICY_LOCKED_KEYS: khoá chính sách sức khoẻ khỏi sweep/override.

Spec: advisor-objective-model-v2 §1.2b (bảng "Có thật chưa?") + data-contract-counterfactual
§7.4 (pseudocode `test_rest_defer_max_min_is_policy_locked` — spec tự khai CHƯA TỒN TẠI,
grep POLICY_LOCKED toàn repo = 0 kết quả trước cycle này).

Bằng chứng đỏ của từng test ghi trong docstring — đã chạy mutation thật 2026-07-31.
"""
from __future__ import annotations

import copy

import pytest

from gsm_core.policy_locks import (POLICY_LOCKED_CONSTS, POLICY_LOCKED_KEYS,
                                   PolicyLockViolation, assert_policy_locks, is_locked)
from gsm_sim.config import Config
from gsm_sim.parallel import _cfg_with
from gsm_sim.runner import run_once


def _cfg(**advice_over) -> Config:
    c = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(c.data), c.root_dir)
    c.data.setdefault("advice", {}).update(advice_over)
    return c


def test_rest_defer_max_min_is_policy_locked():
    """T1 — tên do spec §7.4 đặt. Đỏ trước cycle này bằng ImportError (module không có)."""
    assert is_locked("rest_defer_max_min")           # tên lá — đúng chữ spec viết
    assert is_locked("advice.rest_defer_max_min")    # dotted path
    assert "advice.rest_defer_max_min" in POLICY_LOCKED_KEYS


def test_sweep_rest_defer_max_min_raises():
    """T2 — test chịu tải chính: sweep trần hoãn ⇒ NỔ ngay khi dựng world, không chạy tiếp.

    Đỏ trước cycle: run_once chạy trọn với cap 240 và trả kết quả như thường.
    Đỏ sau cycle nếu ai comment dòng assert_policy_locks trong bridge (mutation đã thử)."""
    cfg = _cfg_with(_cfg(rest_defer_max_min=240), enabled=True, actor_id=None, channels=None)
    with pytest.raises(PolicyLockViolation):
        run_once(cfg, 5100)


def test_lock_holds_on_multiday_path():
    """T3 — bằng chứng VỊ TRÍ cắm: multiday dựng World trực tiếp (không qua run_once).

    Guard đặt ở run_once thì test này đỏ — đó là lý do chokepoint là bridge."""
    from gsm_sim.multiday import run_multiday
    cfg = _cfg(shift_extend_max_min=999)
    with pytest.raises(PolicyLockViolation):
        run_multiday(cfg, seed=5100, days=1)


def test_absent_key_is_not_a_violation():
    """T4 — chống khoá quá tay: fixture tối giản không có block advice phải sống.

    Đỏ nếu assert_policy_locks đòi 'phải có mặt và bằng' (cfg_get không default ⇒ KeyError)."""
    class _Bare:
        @staticmethod
        def get(key, default=None):
            return default                            # config rỗng — mọi khoá vắng mặt
    assert_policy_locks(_Bare.get, where="test-bare") # không raise


def test_rest_min_per_4h_is_NOT_locked():
    """T5 — ghim chống khoá NHẦM: `rest_min_per_4h` là RÀNG BUỘC mà spec ĐÒI sweep được
    (`test_objective_DOES_change_under_feasible_set_perturbation`). Khoá nó là giết test
    hợp lệ của chính spec."""
    assert not is_locked("rest_min_per_4h")
    assert not is_locked("fatigue_threshold_min")     # hardcode ARCHETYPES — entry chết giả
    assert not is_locked("swap_soc_threshold_pct")    # calibration world, không phải lan can


def test_locked_keys_match_canonical_config():
    """T6 — ghim YAML: giá trị chuẩn trong bảng khoá phải khớp config sản phẩm.
    Đỏ khi ai sửa pilot_dongda.yaml mà không đi qua policy_locks.py (đường đổi hợp lệ)."""
    cfg = Config.load("configs/pilot_dongda.yaml")
    for key, canon in POLICY_LOCKED_KEYS.items():
        assert float(cfg.get(key, canon)) == canon, key


def test_locked_consts_match_source():
    """T7 — hằng module khớp bảng khoá (sweep bằng monkeypatch cũng bị T8+chokepoint bắt
    ở run kế vì import module là singleton)."""
    import importlib
    for dotted, canon in POLICY_LOCKED_CONSTS.items():
        mod, attr = dotted.rsplit(".", 1)
        assert float(getattr(importlib.import_module(mod), attr)) == canon, dotted


def test_monkeypatched_const_raises_at_bridge(monkeypatch):
    """T8 — đường sweep hằng module: monkeypatch IDLE_TOTAL_ALERT_MIN ⇒ world kế tiếp NỔ."""
    from gsm_core.solvers import idle_reduction
    monkeypatch.setattr(idle_reduction, "IDLE_TOTAL_ALERT_MIN", 5.0)
    cfg = _cfg_with(_cfg(), enabled=True, actor_id=None, channels=None)
    with pytest.raises(PolicyLockViolation):
        run_once(cfg, 5100)

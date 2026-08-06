"""E3 — UI nhắc "chỉ số sắp gây hại thu nhập" (UPDATE-151 r06; plan E3, Cường chốt backend+web).

E3.1 cliff phòng ngừa (S1 đã tính, adapter từng VỨT) · E3.3 ngưỡng chính sách vào payload.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(ROOT / "ui/backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "ui/backend"))

from app.adapters import advisor  # noqa: E402


def _report_with_cliff(note="tỷ lệ nhận 0.86 sát ngưỡng 0.85 — vài lần từ chối nữa "
                            "có thể mất TOÀN BỘ thưởng dù đủ điểm"):
    return {"confidence": 0.85,
            "sensitivity": [{"param": "rate_-20%", "note": "x"},
                            {"param": "acceptance_cliff", "note": note}]}


def test_cliff_item_sinh_tu_sensitivity_cua_S1():
    it = advisor._cliff_item(_report_with_cliff(), "d-1", "2026-09-28", 600)
    assert it is not None
    assert it["reason_code"] == "acceptance_near_threshold"
    assert it["advice_id"].startswith("s1-")          # namespace thật (L4-07) + hậu tố -cliff
    assert it["advice_id"].endswith("-cliff")
    assert it["numbers"] == []                         # không số tiền — không thành lời hứa
    assert "sát ngưỡng" in it["message"]               # note của solver, không tự đặt lời


def test_cliff_khong_co_thi_khong_bia():
    assert advisor._cliff_item({"sensitivity": []}, "d-1", "2026-09-28", 600) is None
    assert advisor._cliff_item({}, "d-1", "2026-09-28", 600) is None


def test_policy_thresholds_doc_tu_policy_khong_hardcode():
    thr = advisor._policy_thresholds()
    p = advisor.policy()
    assert thr["bonus_min_acceptance"] == float(p.bonus_min_acceptance)
    assert thr["bonus_min_completion"] == float(p.bonus_min_completion)
    assert thr["source"].startswith("policy_v:")


def test_advice_raw_noi_cliff_va_thresholds():
    """Nối thật vào `_advice_raw`: payload mang policy_thresholds; nhánh non-silent append cliff."""
    import inspect

    src = inspect.getsource(advisor._advice_raw)
    assert "_policy_thresholds()" in src, "payload thiếu ngưỡng — client sẽ lại hardcode (D-M3-17)"
    assert src.count("_cliff_item(") >= 2, "cliff phải nối ở CẢ nhánh feasible lẫn infeasible"

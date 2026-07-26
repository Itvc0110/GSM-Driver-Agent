"""AUDIT A3 fix batch 3 (UPDATE-070) — 4 lỗi CAO của hệ agent. Failing-first.

FAILCLOSED-1: pipeline FAIL-OPEN — verify lần 2 hỏng vẫn trả message cho tài xế.
LAYEROUT-1: `_vn` tolerance tuyệt đối 0.5 → ngưỡng policy 0.85 in nhầm thành tỷ lệ 74%.
LAYEROUT-2: template nói "còn thiếu X để đạt mốc" khi solver bảo INFEASIBLE.
LAYEROUT-4: view l1r gộp trọn ngày → 08:00 sáng đã "đạt mốc cao nhất" (rò tương lai trong ngày).
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gsm_core.advisor.templates import _vn, render_template
from gsm_core.features.from_l1r import derive_bonus_gap_input_l1r
from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.policy import PolicyBundle

ROOT = Path(__file__).resolve().parent.parent

POLICY_REC = {
    "schema_version": "1.0.0", "bundle_id": "b1", "version": "sim-policy-v0",
    "effective_from": "2026-07-01T00:00:00+07:00", "track": "platform", "service": "bike",
    "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300},
    "driver_share": 0.75,
    "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
               "window_hours": list(range(6, 22))},
    "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
    "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85},
    "source_url": None, "source": "MOCK",
}


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(POLICY_REC)


@pytest.fixture(scope="module")
def l1r():
    with TemporaryDirectory() as td:
        return generate_realdata(days=6, seed_base=880, out_dir=Path(td))["tables"]


# ---------- LAYEROUT-1 ----------

def test_vn_ratio_tolerance_does_not_confuse_threshold_with_rate():
    """Registry có CẢ tỷ lệ hiện tại (0.739) lẫn ngưỡng (0.85) — cùng unit 'ratio'.
    Tolerance 0.5 tuyệt đối làm 0.85 khớp nhầm 0.739 → in '74%' như 'mức tối thiểu'."""
    reg = {"N1": {"value": 0.739, "unit": "ratio", "source": "measured"},
           "N2": {"value": 0.85, "unit": "ratio", "source": "policy"}}
    assert _vn(reg, 0.85, "ratio") == "85%", "ngưỡng policy bị render thành tỷ lệ tài xế"
    assert _vn(reg, 0.739, "ratio") == "74%"
    assert _vn(reg, 0.61, "ratio") == "", "giá trị KHÔNG có trong registry phải trả rỗng"


# ---------- LAYEROUT-2 ----------

def _s1_report(feasible: bool):
    return {
        "schema_version": "1.0.0", "solver": "bonus_feasibility",
        "problem_digest": "digest", "inputs_used": [],
        "solution": {"feasible": feasible, "gap_points": 60, "tier_vnd": 115000,
                     "tier_points": 160, "hours_needed": None if not feasible else 2.0,
                     "trips_needed": 12,
                     "constraints": {"enough_hours": feasible, "ok_acceptance": True,
                                     "ok_completion": True}},
        "numbers": [{"value": 60, "unit": "points", "source": "policy_v:x"},
                    {"value": 115000, "unit": "vnd", "source": "policy_v:x"}],
        "sensitivity": [], "confidence": 0.8, "caveats": [],
        "infeasible_reason": None if feasible else
        "từ giờ đến hết khung điểm chỉ kiếm thêm được ~20đ < 60đ còn thiếu",
    }


def test_template_does_not_promise_gap_when_infeasible():
    reg = {"N1": {"value": 60, "unit": "points", "source": "s"},
           "N2": {"value": 115000, "unit": "vnd", "source": "s"}}
    ok = render_template("F2", [_s1_report(True)], [], reg)["message"]
    bad = render_template("F2", [_s1_report(False)], [], reg)["message"]
    assert "còn thiếu" in ok
    assert "còn thiếu 60 điểm để đạt mốc" not in bad, \
        "solver bảo KHÔNG khả thi mà template vẫn hứa mốc"
    assert "khó khả thi" in bad or "không đạt" in bad.lower()


# ---------- LAYEROUT-4 ----------

def test_bonus_gap_view_respects_t_now_within_day(l1r, policy):
    """08:00 sáng không được cộng điểm của cuốc chạy chiều CÙNG NGÀY."""
    drv = next(r["driver_id"] for r in l1r["driver_statistic_daily"]
               if r["driver_id"].startswith("d-") and r["completed_count"] > 5)
    date = sorted({r["local_date"] for r in l1r["driver_statistic_daily"]})[-1]
    early = derive_bonus_gap_input_l1r(drv, f"{date}T08:00:00+07:00", l1r, policy)
    late = derive_bonus_gap_input_l1r(drv, f"{date}T23:30:00+07:00", l1r, policy)
    assert early["points_now"] < late["points_now"], \
        "điểm lúc 8h sáng bằng cả ngày — view đọc TƯƠNG LAI trong ngày"


# ---------- FAILCLOSED-1 ----------

def test_pipeline_never_returns_unverified_message(policy, tmp_path):
    """Template render số không trace được (mission thiếu name → in mission_id 'M77')
    ⇒ V1 veto CẢ HAI lần. Pipeline PHẢI degrade an toàn, không trả message hỏng."""
    from gsm_core.advisor.pipeline import AdvisorPipeline
    mission_rep = {
        "schema_version": "1.0.0", "solver": "mission_knapsack",
        "problem_digest": "digest mission", "inputs_used": [],
        "solution": {"chosen_missions": [{"mission_id": "M77", "name": None}],
                     "expected_reward_vnd": 50000},
        "numbers": [{"value": 50000, "unit": "vnd", "source": "policy_v:x"}],
        "sensitivity": [], "confidence": 0.7, "caveats": [], "infeasible_reason": None,
    }
    reg = {"N1": {"value": 50000, "unit": "vnd", "source": "policy_v:x"}}
    out = render_template("F1", [mission_rep], [], reg)
    from gsm_core.advisor import verifier as V
    v = V.verify(out["message"], out.get("advice_spec"), out.get("citations", []),
                 "F1", used_kb=False, rendered_numbers=["50.000đ"], cited_texts=[])
    assert not v["passed"], "fixture phải làm verifier veto (nếu không, test vô nghĩa)"

    pipe = AdvisorPipeline(corpus_path=ROOT / "research" / "policy" / "t004-current-policy-text-corpus-2026-07-22.json",
                           store_path=tmp_path / "ep.jsonl", llm_mode="off")
    safe = pipe.safe_degrade(out, v)
    assert safe["residual_path"] == "R6_verify_fail"
    assert "M77" not in safe["message"] and "77" not in safe["message"]
    assert safe["verify_failed"] is True


# ---------- VBYPASS-3: negation defuse (test HAI CHIỀU) ----------

BYPASS_CASES = [
    "Khong sai dau, chac chan anh kiem duoc nam trieu dong.",
    "Ung dung nay chac chan giup anh kiem duoc nhieu hon.",
    "Su dung app deu, dam bao anh kiem duoc nhieu hon han.",
    "Ứng dụng này chắc chắn giúp anh kiếm được nhiều hơn.",
]
LEGIT_DISCLAIMERS = [
    "Con so nay khong chac chan, kiem duoc bao nhieu phu thuoc thi truong.",
    "Đây là ước tính, không đảm bảo anh/chị kiếm được mức này.",
    "Trợ lý không cam kết thu nhập; kết quả phụ thuộc nhu cầu thực tế.",
]


@pytest.mark.parametrize("msg", BYPASS_CASES)
def test_promise_not_defused_by_unrelated_negation(msg):
    from gsm_core.advisor import verifier as V
    assert V.check_blocklist(msg, None), f"lời hứa thu nhập LỌT V2: {msg}"


@pytest.mark.parametrize("msg", LEGIT_DISCLAIMERS)
def test_real_disclaimers_still_pass(msg):
    """Chiều ngược: câu disclaimer hợp lệ KHÔNG được bắt nhầm (precision)."""
    from gsm_core.advisor import verifier as V
    assert V.check_blocklist(msg, None) == [], f"disclaimer bị chặn nhầm: {msg}"


def test_control_promise_still_caught():
    from gsm_core.advisor import verifier as V
    assert V.check_blocklist(
        "Yen tam nhe, chac chan anh kiem duoc rat nhieu tien moi ngay.", None)

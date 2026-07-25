"""PI-5a — S5/S6 ĐẾN ĐƯỢC tài xế qua pipeline C6 (router → template → verifier).

Chain THẬT: generate_realdata → derive view → S5/S6 solve → AdvisorPipeline.handle
→ ComposedAdvice. Kiểm guardrail không bị nới: số phải trace registry, verifier pass,
cảnh báo truy thu dùng ngôn ngữ ĐIỀU KIỆN (không doạ/hứa).
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gsm_core.advisor.observability import compute_faithfulness
from gsm_core.advisor.pipeline import AdvisorPipeline
from gsm_core.advisor.router import route
from gsm_core.advisor.templates import render_template
from gsm_core.advisor.context_pack import build_context_pack
from gsm_core.features.from_l1r import (derive_weekly_khoan_input_l1r,
                                         derive_mission_select_input_l1r)
from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.policy import PolicyBundle
from gsm_core.schema_registry import SchemaRegistry
from gsm_core.solvers.weekly_khoan import solve as solve_s5
from gsm_core.solvers.mission_knapsack import solve as solve_s6
from test_weekly_khoan import BASE_POLICY, QUOTA  # pytest rootdir=tests trên sys.path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "research" / "policy" / "t004-current-policy-text-corpus-2026-07-22.json"


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record({**BASE_POLICY, "weekly_quota": QUOTA})


@pytest.fixture(scope="module")
def reports(policy):
    """SolverReport THẬT của S5+S6 từ data shape thật."""
    with TemporaryDirectory() as td:
        t = generate_realdata(days=8, seed_base=800, out_dir=Path(td))["tables"]
    row = sorted(t["driver_income_daily"], key=lambda r: -r["total_order"])[0]
    drv, d = row["driver_id"], row["order_date"]
    s5 = solve_s5(derive_weekly_khoan_input_l1r(drv, f"{d}T18:00:00+07:00", t, policy), policy)
    s6 = solve_s6(derive_mission_select_input_l1r("d-NEW", f"{d}T14:00:00+07:00", t,
                                                  hours_budget_remaining=8.0, trips_per_hour=2.5))
    return {"driver_id": drv, "date": d, "s5": s5, "s6": s6}


def _req(feature, drv="d-1", q=None):
    return {"schema_version": "1.0.0", "request_id": f"r-{feature}", "driver_id": drv,
            "feature": feature, "free_text_query": q, "l3_view_refs": [], "session_id": "s",
            "t_request": "2026-07-01T18:00:00+07:00", "trigger_source": "user_ask"}


# ---------- router ----------

def test_router_includes_new_solvers():
    assert "weekly_khoan" in route("F1", None)["solvers"]
    assert "mission_knapsack" in route("F1", None)["solvers"]
    assert "mission_knapsack" in route("F2", None)["solvers"]
    assert "weekly_khoan" in route("F3", None)["solvers"]
    assert "weekly_khoan" not in route("F0", None)["solvers"]  # F0 = policy Q&A


@pytest.mark.parametrize("q,intent", [
    ("hôm nay có nhiệm vụ nào nên làm không", "mission_task"),
    ("tuần này còn thiếu bao nhiêu khoán", "weekly_target"),
])
def test_router_new_intents(q, intent):
    assert route("F1", q)["intent"] == intent


def test_router_still_rejects_out_of_taxonomy():
    assert route("F1", "thời tiết sao Hỏa thế nào")["intent"] == "out_of_taxonomy"


# ---------- template render ----------

def test_f1_template_shows_khoan_and_mission(reports):
    pack = build_context_pack("F1", [reports["s5"], reports["s6"]], [], driver_id="d-1")
    out = render_template("F1", [reports["s5"], reports["s6"]], [], pack["numbers_registry"])
    msg = out["message"]
    assert "khoán" in msg.lower(), msg
    if (reports["s6"]["solution"] or {}).get("chosen_missions"):
        assert "Nhiệm vụ nên làm" in msg, msg


def test_clawback_uses_conditional_language(reports):
    """Cảnh báo truy thu phải là ĐIỀU KIỆN ('nếu không đạt...'), không doạ/khẳng định."""
    sol = reports["s5"]["solution"]
    if not sol.get("clawback_risk_vnd"):
        pytest.skip("driver này không có rủi ro truy thu")
    pack = build_context_pack("F1", [reports["s5"]], [], driver_id="d-1")
    msg = render_template("F1", [reports["s5"]], [], pack["numbers_registry"])["message"]
    assert "có thể bị truy thu" in msg and "Nếu không đạt" in msg, msg


def test_numbers_in_message_trace_to_registry(reports):
    """Số hiển thị PHẢI đến từ numbers_registry (không tự format từ solution)."""
    pack = build_context_pack("F1", [reports["s5"], reports["s6"]], [], driver_id="d-1")
    msg = render_template("F1", [reports["s5"], reports["s6"]], [], pack["numbers_registry"])["message"]
    from gsm_core.advisor.context_pack import render_number_vn
    rendered = {render_number_vn(n["value"], n["unit"]) for n in pack["numbers_registry"].values()}
    import re
    for tok in re.findall(r"\d[\d.,]*(?:đ| điểm| giờ)", msg):
        assert any(tok in r for r in rendered), f"số '{tok}' không trace được: {msg}"


def test_positional_number_bug_fixed(reports, policy):
    """BUG-PI5a-01: thêm S5/S6 làm đổi thứ tự registry → n1/n2 KHÔNG được lấy nhầm.

    S1 đứng SAU S5 trong danh sách → nếu vẫn dùng nids[0]/nids[1] thì 'mốc thưởng' sẽ
    hiển thị số khoán tuần (sai hoàn toàn).
    """
    s1 = {"schema_version": "1.0.0", "solver": "bonus_feasibility",
          "problem_digest": "x", "inputs_used": [{"view_id": "v", "version": "1",
                                                   "freshness": "2026-07-01T18:00:00+07:00"}],
          "solution": {"feasible": True, "gap_points": 20, "tier_vnd": 115000},
          "numbers": [{"value": 20, "unit": "points", "source": "policy_v:x"},
                       {"value": 115000, "unit": "vnd", "source": "policy_v:x"}],
          "sensitivity": [], "confidence": 0.8, "caveats": [], "infeasible_reason": None}
    reports_ordered = [reports["s5"], s1]          # S5 TRƯỚC S1 (đảo thứ tự)
    pack = build_context_pack("F1", reports_ordered, [], driver_id="d-1")
    msg = render_template("F1", reports_ordered, [], pack["numbers_registry"])["message"]
    assert "20 điểm" in msg and "115.000đ" in msg, msg


# ---------- NGỮ NGHĨA (test xanh ≠ câu đúng — 2 bug lộ khi ĐỌC output) ----------

def _khoan_report(gap, claw, quota_ok=True):
    nums = [{"value": 1_000_000, "unit": "vnd", "source": "ledger:income_daily|basis=gross"}]
    if gap:
        nums.append({"value": gap, "unit": "vnd", "source": "policy_v:x|basis=gross"})
    if claw:
        nums.append({"value": claw, "unit": "vnd", "source": "policy_v:x|basis=gross"})
    return {"schema_version": "1.0.0", "solver": "weekly_khoan", "problem_digest": "khoán",
            "inputs_used": [{"view_id": "v", "version": "1",
                             "freshness": "2026-07-01T18:00:00+07:00"}],
            "solution": {"quota_available": quota_ok, "feasible": True,
                          "gap_revenue_vnd": gap, "clawback_risk_vnd": claw},
            "numbers": nums, "sensitivity": [], "confidence": 0.8, "caveats": [],
            "infeasible_reason": None}


def test_bug02_quota_met_says_achieved_not_zero_shortfall():
    """BUG-PI5a-02: gap=0 phải nói 'đã đạt khoán', KHÔNG 'còn thiếu 0đ ... truy thu 0đ'."""
    r = _khoan_report(gap=0, claw=0)
    pack = build_context_pack("F1", [r], [], driver_id="d-1")
    msg = render_template("F1", [r], [], pack["numbers_registry"])["message"]
    assert "đã đạt khoán" in msg, msg
    assert "còn thiếu 0đ" not in msg and "truy thu" not in msg, msg


def test_bug01_no_bonus_solver_means_no_bonus_claim():
    """BUG-PI5a-01: thiếu bonus_feasibility ⇒ KHÔNG được bịa câu 'mốc thưởng' từ số khác
    (trước đây render 'mốc thưởng 35585.2 vnd_per_hour' — vô nghĩa)."""
    r = _khoan_report(gap=500_000, claw=100_000)
    pack = build_context_pack("F1", [r], [], driver_id="d-1")
    msg = render_template("F1", [r], [], pack["numbers_registry"])["message"]
    assert "mốc thưởng" not in msg, msg
    assert "vnd_per_hour" not in msg and "points_per_hour" not in msg, msg
    assert "còn thiếu 500.000đ doanh số" in msg, msg


def test_clawback_only_when_positive():
    r = _khoan_report(gap=500_000, claw=0)
    pack = build_context_pack("F1", [r], [], driver_id="d-1")
    msg = render_template("F1", [r], [], pack["numbers_registry"])["message"]
    assert "còn thiếu 500.000đ" in msg and "truy thu" not in msg, msg


# ---------- end-to-end pipeline ----------

@pytest.mark.parametrize("feature", ["F1", "F2", "F3"])
def test_pipeline_end_to_end_with_new_solvers(reg, reports, feature, tmp_path):
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=tmp_path / f"ep-{feature}.db",
                           llm_mode="off")
    rs = [reports["s5"], reports["s6"]]
    advice = pipe.handle(_req(feature), solver_reports=rs, kb_track="platform")
    assert reg.validate("composed_advice", advice) == [], advice
    assert pipe.last_verify_result["passed"] is True, pipe.last_verify_result
    assert compute_faithfulness(advice["numbers"], rs) == 1.0
    assert advice["message"]


def test_guardrail_no_promise_with_new_solvers(reg, reports, tmp_path):
    """Verifier không bị nới: message có cảnh báo truy thu vẫn PASS (không phải lời hứa)."""
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=tmp_path / "ep.db", llm_mode="off")
    advice = pipe.handle(_req("F1"), solver_reports=[reports["s5"], reports["s6"]],
                         kb_track="platform")
    assert pipe.last_verify_result["errors"] == []
    assert advice["fallback_used"] is True  # template mode

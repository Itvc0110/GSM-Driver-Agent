"""C6 tranche A — pipeline deterministic (TDD failing-first, KHÔNG LLM).

policy_kb (track guardrail), router (direct map + keyword), context_pack
(1 renderer, prefix cache, budget), templates (LLM-off), episode_store
(exact-key cache), pipeline end-to-end template-mode.
"""

import json
from pathlib import Path

import pytest

from gsm_core.advisor.policy_kb import PolicyKB
from gsm_core.advisor.router import route
from gsm_core.advisor.context_pack import build_context_pack, render_number_vn
from gsm_core.advisor.templates import render_template
from gsm_core.advisor.episode_store import EpisodeStore
from gsm_core.advisor.pipeline import AdvisorPipeline
from gsm_core.schema_registry import SchemaRegistry

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "research" / "policy" / "t004-current-policy-text-corpus-2026-07-22.json"


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def kb():
    return PolicyKB(CORPUS)


# ---------- policy_kb ----------

def test_kb_loads_seven_records(kb):
    assert kb.n_records == 7


def test_kb_track_filter_hard(kb):
    """Guardrail T-004: record rto-only KHÔNG hiện cho platform; unspecified (f0_tracks=[])
    KHÔNG BAO GIỜ match track cụ thể."""
    plat = kb.retrieve("platform", "đổi pin tài khoản")
    for r in plat:
        assert "platform" in r["f0_tracks"], f"record {r['source_id']} không thuộc platform"
    # record generic (f0_tracks rỗng) không được trả về
    all_plat_ids = {r["source_id"] for r in kb.retrieve("platform", "thu nhập")}
    generic_ids = {rec["source_id"] for rec in kb.records if not rec["f0_tracks"]}
    assert not (all_plat_ids & generic_ids), "generic bike KHÔNG được auto-match track"


def test_kb_missing_track_returns_need_track(kb):
    out = kb.retrieve(None, "thưởng thu nhập")
    assert out == "need_track"


def test_kb_citation_has_url(kb):
    rs = kb.retrieve("platform", "thu nhập")
    assert rs and all(r["source_url"].startswith("https://") for r in rs)


# ---------- router ----------

def test_router_feature_direct_map():
    # PI-5a: F1/F2/F3 nhận thêm S5 weekly_khoan / S6 mission_knapsack
    assert {"bonus_feasibility", "shift_dp"} <= set(route("F1", None)["solvers"])
    assert "f3_patterns" in route("F3", None)["solvers"]
    assert "policy_kb" in route("F0", None)["solvers"] or route("F0", None)["use_kb"]


def test_router_free_text_keyword():
    r = route("F0", "tuần này chạy bao nhiêu chuyến thì được thưởng")
    assert r["intent"] != "out_of_taxonomy"


def test_router_out_of_taxonomy():
    r = route("F0", "thời tiết sao Hỏa hôm nay thế nào")
    assert r["intent"] == "out_of_taxonomy"


# ---------- context_pack ----------

def _report_s1():
    return {"schema_version": "1.0.0", "solver": "bonus_feasibility",
            "problem_digest": "Thiếu 20đ tới mốc 160",
            "inputs_used": [{"view_id": "bg:d-1", "version": "1.0.0",
                             "freshness": "2026-07-01T18:00:00+07:00"}],
            # khớp solution THẬT của bonus_feasibility (có tier_points/tier_vnd) — template
            # neo số theo giá trị solution nên fixture phải trung thực (PI-5a)
            "solution": {"feasible": True, "gap_points": 20, "hours_needed": 1.33,
                          "tier_points": 160, "tier_vnd": 115000},
            "numbers": [{"value": 20, "unit": "points", "source": "policy_v:sim-policy-v0"},
                         {"value": 115000, "unit": "vnd", "source": "policy_v:sim-policy-v0"}],
            "sensitivity": [], "confidence": 0.85, "caveats": ["demand proxy"],
            "infeasible_reason": None}


def test_context_pack_canonical_numbers():
    pack = build_context_pack("F1", [_report_s1()], [], driver_id="d-1")
    assert "[N1]" in pack["prompt_data"] and "[N2]" in pack["prompt_data"]
    assert "policy_v:sim-policy-v0" in pack["prompt_data"]
    assert pack["numbers_registry"]["N1"]["value"] == 20
    assert pack["numbers_registry"]["N2"]["value"] == 115000


def test_context_pack_prefix_stable():
    p1 = build_context_pack("F1", [_report_s1()], [], driver_id="d-1")
    p2 = build_context_pack("F1", [_report_s1()], [], driver_id="d-2")
    assert p1["system_prompt"] == p2["system_prompt"], "system phải byte-identical (prefix cache)"


def test_render_number_vn():
    assert render_number_vn(115000, "vnd") == "115.000đ"
    assert render_number_vn(20, "points") == "20 điểm"
    assert render_number_vn(1.33, "hours") == "1,3 giờ"


# ---------- templates (LLM-off) ----------

def test_template_renders_each_feature(reg):
    for feature in ("F0", "F1", "F2", "F3"):
        out = render_template(feature, [_report_s1()], [],
                              numbers_registry={"N1": {"value": 20, "unit": "points",
                                                        "source": "policy_v:x"},
                                                 "N2": {"value": 115000, "unit": "vnd",
                                                        "source": "policy_v:x"}})
        assert out["message"] and "115.000đ" in out["message"] or "20 điểm" in out["message"]
        assert out["fallback_used"] is True


# ---------- episode_store ----------

def test_episode_store_append_and_cache(tmp_path):
    store = EpisodeStore(tmp_path / "ep.db")
    key_parts = dict(driver_id="d-1", state_digest="abc", policy_version="v0",
                     solver_version="1", prompt_version="1", model_id="template")
    assert store.cache_get(**key_parts) is None
    store.append_episode({"episode_id": "e1", "driver_id": "d-1", "feature": "F1",
                          "message": "test", "confidence": 0.8, "fallback_used": True})
    store.cache_put(advice={"advice_id": "e1"}, **key_parts)
    assert store.cache_get(**key_parts)["advice_id"] == "e1"
    # đổi policy_version → miss (versioned key)
    assert store.cache_get(**{**key_parts, "policy_version": "v1"}) is None
    assert store.count_episodes() == 1


# ---------- pipeline end-to-end (template mode) ----------

def test_pipeline_end_to_end_template(reg, tmp_path):
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=tmp_path / "ep.db",
                           llm_mode="off")
    req = {"schema_version": "1.0.0", "request_id": "r1", "driver_id": "d-1",
           "feature": "F1", "free_text_query": None, "l3_view_refs": [],
           "session_id": "s1", "t_request": "2026-07-01T18:00:00+07:00",
           "trigger_source": "user_ask"}
    advice = pipe.handle(req, solver_reports=[_report_s1()], kb_track="platform")
    assert reg.validate("composed_advice", advice) == []
    assert advice["fallback_used"] is True
    assert advice["numbers"], "numbers phải truyền từ SolverReport"
    # structural faithfulness: mọi số trong message trace về registry
    assert pipe.last_verify_result["passed"] is True


def test_pipeline_f0_needs_track(tmp_path):
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=tmp_path / "ep.db", llm_mode="off")
    req = {"schema_version": "1.0.0", "request_id": "r2", "driver_id": "d-9",
           "feature": "F0", "free_text_query": "thưởng tuần này thế nào",
           "l3_view_refs": [], "session_id": "s1",
           "t_request": "2026-07-01T18:00:00+07:00", "trigger_source": "user_ask"}
    advice = pipe.handle(req, solver_reports=[], kb_track=None)
    # thiếu track → clarify (message hỏi lại), không phải advice số
    assert advice.get("clarify_needed") or "hình thức" in advice["message"] or "track" in advice["message"].lower()

"""C6 tranche B — Composer placeholder-first + Verifier rules (mock LLM, TDD).

Suite KHÔNG gọi LLM thật. Mock composer trả ComposerOutput; test render + verify + repair.
"""

from pathlib import Path

import pytest

from gsm_core.advisor.composer import Composer, ComposerOutput, render_placeholders
from gsm_core.advisor import verifier as V
from gsm_core.advisor._text import normalize_vi
from gsm_core.advisor.context_pack import build_context_pack, render_number_vn
from gsm_core.advisor.pipeline import AdvisorPipeline
from gsm_core.schema_registry import SchemaRegistry

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "research" / "policy" / "t004-current-policy-text-corpus-2026-07-22.json"


def _report():
    return {"schema_version": "1.0.0", "solver": "bonus_feasibility",
            "problem_digest": "Thiếu 20đ tới mốc",
            "inputs_used": [{"view_id": "x", "version": "1", "freshness": "2026-07-01T18:00:00+07:00"}],
            "solution": {"feasible": True},
            "numbers": [{"value": 20, "unit": "points", "source": "policy_v:v0"},
                         {"value": 115000, "unit": "vnd", "source": "policy_v:v0"}],
            "sensitivity": [], "confidence": 0.85, "caveats": [], "infeasible_reason": None}


@pytest.fixture()
def pack():
    return build_context_pack("F1", [_report()], [], driver_id="d-1")


# ---------- placeholder render ----------

def test_render_placeholders_vn(pack):
    msg = render_placeholders("Còn thiếu {{N1}} để đạt mốc {{N2}}.",
                              pack["numbers_registry"])
    assert msg == "Còn thiếu 20 điểm để đạt mốc 115.000đ."


def test_render_unknown_placeholder_raises(pack):
    with pytest.raises(KeyError):
        render_placeholders("Số lạ {{N9}}.", pack["numbers_registry"])


# ---------- normalization (BUG-C6-01 regression) ----------

def test_normalize_strips_d_stroke():
    # đ/Đ là chữ cái riêng — NFD không tách; phải map tay → d
    assert normalize_vi("đơn") == "don"
    assert normalize_vi("Điểm") == "diem"
    assert normalize_vi("đổi pin") == "doi pin"
    assert normalize_vi("Đảm bảo") == "dam bao"


# ---------- verifier rules (từng rule đỏ→xanh) ----------

def test_verifier_catches_bare_number():
    errs = V.check_bare_numbers("Anh sẽ kiếm được 500.000đ hôm nay.", ["20 điểm"])
    assert errs and "V1" in errs[0]


def test_verifier_allows_rendered_numbers():
    assert V.check_bare_numbers("Còn thiếu 20 điểm để đạt 115.000đ.",
                                ["20 điểm", "115.000đ"]) == []


def test_verifier_allows_time_and_url():
    assert V.check_bare_numbers(
        "Chạy khung 17h nhé, xem https://greensm.com/abc123", []) == []


def test_verifier_blocklist_promise():
    errs = V.check_blocklist("Đảm bảo anh kiếm được 500 nghìn thu nhập.", None)
    assert any("V2a" in e for e in errs)


def test_verifier_blocklist_order_advice():
    errs = V.check_blocklist("Anh nên nhận đơn này ngay.", None)
    assert any("V2b" in e for e in errs)


def test_verifier_disclaimer_negation_ok():
    # câu phủ định = disclaimer hợp lệ, không phải lời hứa
    assert V.check_blocklist("Đây là ước tính, không phải cam kết thu nhập.", None) == []


def test_verifier_missing_disclaimer_with_spec():
    errs = V.check_blocklist("Anh nghỉ lúc 14h nhé.", {"action_type": "rest"})
    assert any("V2c" in e for e in errs)


def test_verifier_cited_title_not_flagged():
    """BUG-C6-02/03: tên chính sách official ('Đảm Bảo Thu Nhập', 'áp dụng 05/06/2026')
    được trích verbatim là DATA — không bị bắt là hứa hẹn / số trần."""
    title_promise = "Chính Sách Đảm Bảo Thu Nhập Cho Bác Tài Green Bike"
    msg = f"Anh/chị xem chính sách này nhé. Nguồn: {title_promise}."
    assert V.check_blocklist(msg, None, cited_texts=[title_promise]) == []
    title_date = "Bộ quy tắc ứng xử (Áp dụng từ 05/06/2026)"
    msg2 = f"Anh/chị lưu ý quy tắc mới. Nguồn: {title_date}."
    assert V.check_bare_numbers(msg2, [], cited_texts=[title_date]) == []
    # nhưng số TRẦN ngoài tiêu đề vẫn bị bắt
    msg3 = f"Anh chắc chắn kiếm 999đ. Nguồn: {title_date}."
    assert V.check_bare_numbers(msg3, [], cited_texts=[title_date])


def test_verifier_promise_still_caught_with_citation():
    """Fix không được nới lỏng: hứa earning THẬT vẫn bị bắt dù có cited_texts."""
    title = "Chính Sách Đảm Bảo Thu Nhập"
    msg = f"Đảm bảo anh kiếm được 500 nghìn. Nguồn: {title}."
    assert any("V2a" in e for e in V.check_blocklist(msg, None, cited_texts=[title]))


def test_verifier_cjk():
    errs = V.check_cjk("Chạy tốt 加油 nhé")
    assert errs and "V3" in errs[0]


def test_verifier_f0_citation():
    assert V.check_f0_citation("F0", True, []) != []
    assert V.check_f0_citation("F0", True, ["https://x"]) == []
    assert V.check_f0_citation("F1", False, []) == []


# ---------- composer với mock LLM ----------

class MockLLM:
    """Mock trả sẵn ComposerOutput theo kịch bản."""
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = 0

    def create(self, **kwargs):
        out = self.outputs[min(self.calls, len(self.outputs) - 1)]
        self.calls += 1
        return out


def test_composer_good_output(pack):
    good = ComposerOutput(
        advice_spec=None,
        message_template="Anh/chị còn thiếu {{N1}} để đạt mốc {{N2}}. Đây là ước tính, không đảm bảo.",
        citations=[], caveats=["ước tính"])
    c = Composer(llm=MockLLM([good]))
    out = c.compose(pack, "F1")
    assert "20 điểm" in out["message"] and "115.000đ" in out["message"]
    assert out["fallback_used"] is False


def test_composer_bad_number_veto_to_template(pack):
    """Mock trả số trần → verify fail trong pipeline → template fallback."""
    bad = ComposerOutput(advice_spec=None,
                         message_template="Anh chắc chắn kiếm 999.999đ hôm nay!",
                         citations=[], caveats=[])
    c = Composer(llm=MockLLM([bad, bad]))  # cả repair cũng bad
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=":memory:",
                           llm_mode="live", composer=c)
    req = {"schema_version": "1.0.0", "request_id": "r1", "driver_id": "d-1",
           "feature": "F1", "free_text_query": None, "l3_view_refs": [],
           "session_id": "s", "t_request": "2026-07-01T18:00:00+07:00",
           "trigger_source": "user_ask"}
    advice = pipe.handle(req, solver_reports=[_report()], kb_track=None)
    assert advice["fallback_used"] is True  # veto → template
    assert pipe.last_verify_result["passed"] is True  # template pass


def test_composer_unknown_placeholder_falls_back(pack):
    bad = ComposerOutput(advice_spec=None, message_template="Thiếu {{N9}} nữa.",
                         citations=[], caveats=[])
    c = Composer(llm=MockLLM([bad]))
    out = c.compose(pack, "F1")
    assert out["fallback_used"] is True  # render fail → fallback flag


def test_schema_composed_advice_live_mode(pack):
    reg = SchemaRegistry(ROOT / "schemas")
    good = ComposerOutput(
        advice_spec={"action_type": "rest_window", "target_window": "14:00"},
        message_template="Nghỉ 14h nhé — còn {{N1}} tới mốc {{N2}}. Ước tính, không chắc chắn.",
        citations=[], caveats=["ước tính"])
    c = Composer(llm=MockLLM([good]))
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=":memory:",
                           llm_mode="live", composer=c)
    req = {"schema_version": "1.0.0", "request_id": "r2", "driver_id": "d-1",
           "feature": "F2", "free_text_query": None, "l3_view_refs": [],
           "session_id": "s", "t_request": "2026-07-01T18:00:00+07:00",
           "trigger_source": "anchor"}
    advice = pipe.handle(req, solver_reports=[_report()], kb_track=None)
    assert reg.validate("composed_advice", advice) == []

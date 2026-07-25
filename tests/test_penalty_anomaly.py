"""PI-5c — S8 PenaltyExplain (UC6) + S9 AnomalyAlert (UC7).

TRỌNG TÂM = GUARDRAIL: không dạy lách (UC6), KHÔNG kết tội (UC7).
Đây là 2 tính năng dễ gây hại nhất → test chặn từ khoá + bắt buộc nhãn/khuyến nghị.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gsm_core.advisor.context_pack import build_context_pack
from gsm_core.advisor.pipeline import AdvisorPipeline
from gsm_core.advisor.router import route
from gsm_core.advisor.templates import render_template
from gsm_core.features.from_l1r import (derive_penalty_explain_input_l1r,
                                         derive_anomaly_alert_input_l1r)
from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.policy import PolicyBundle
from gsm_core.schema_registry import SchemaRegistry
from gsm_core.solvers.anomaly_alert import solve as solve_s9, NOT_CONCLUSION
from gsm_core.solvers.penalty_explain import solve as solve_s8
from test_weekly_khoan import BASE_POLICY

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "research" / "policy" / "t004-current-policy-text-corpus-2026-07-22.json"

# từ TUYỆT ĐỐI KHÔNG được xuất hiện
EVASION_WORDS = ["lách", "né phạt", "tránh bị phát hiện", "mẹo né", "không bị phát hiện",
                 "qua mặt", "đối phó"]
ACCUSATION_WORDS = ["gian lận", "vi phạm của anh", "anh/chị đã vi phạm", "bạn đã gian lận",
                    "hành vi gian lận", "đã trục lợi"]


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(BASE_POLICY)


@pytest.fixture(scope="module")
def tables():
    with TemporaryDirectory() as td:
        return generate_realdata(days=10, seed_base=1000, out_dir=Path(td))["tables"]


def _pen_view(pens, acc=0.90, ful=0.95, khoan_gap=None):
    return {"schema_version": "1.0.0", "driver_id": "d-1", "t_now": "2026-07-10T20:00:00+07:00",
            "period_start": "2026-06-10", "period_end": "2026-07-10", "penalties": pens,
            "rates": {"acceptance": acc, "fulfillment": ful, "cancellation": 0.05},
            "thresholds": {"min_acceptance": 0.85, "min_completion": 0.85},
            "khoan_gap_vnd": khoan_gap, "view_version": "1.0.0", "source": "MOCK"}


def _pen(pid, ptype, amt, status="applied"):
    return {"penalization_id": pid, "local_date": "2026-07-05", "penalty_type": ptype,
            "amount_vnd": amt, "reason": f"lý do {ptype}", "status": status,
            "week_key": "2026-W27"}


def _anom_view(flags):
    return {"schema_version": "1.0.0", "driver_id": "d-1", "t_now": "2026-07-10T20:00:00+07:00",
            "flags": flags, "view_version": "1.0.0", "source": "INFERRED"}


def _flag(fid, ftype="route_deviation", sev="low", conf=0.4, status="open"):
    return {"fraud_id": fid, "detected_at": "2026-07-05T18:00:00+07:00", "fraud_type": ftype,
            "severity": sev, "confidence": conf, "status": status}


# ================= S8 PenaltyExplain (UC6) =================

def test_s8_schema_and_totals(reg):
    v = _pen_view([_pen("p1", "clawback_khoan", 40000), _pen("p2", "conduct", 200000)])
    assert reg.validate("penalty_explain_input", v) == []
    r = solve_s8(v)
    assert reg.validate("solver_report", r) == []
    assert r["solution"]["total_deducted_vnd"] == 240000
    assert r["solution"]["breakdown"]["conduct"] == 200000


def test_s8_no_penalty_no_risk_does_not_invent(reg):
    """Không khoản trừ + chỉ số đạt → KHÔNG bịa rủi ro."""
    r = solve_s8(_pen_view([], acc=0.95, ful=0.97))
    assert r["solution"]["notable"] is False
    assert r["solution"]["risks"] == []
    assert "không ghi nhận khoản trừ" in r["problem_digest"]


def test_s8_flags_metric_below_threshold():
    r = solve_s8(_pen_view([], acc=0.80, ful=0.95))  # 0.80 < 0.85
    risks = r["solution"]["risks"]
    assert risks and risks[0]["state"] == "below"
    assert "dưới mức tối thiểu" in r["problem_digest"]


def test_s8_never_teaches_evasion():
    """GUARDRAIL: giải thích quy tắc + cách TUÂN THỦ, KHÔNG mẹo né."""
    r = solve_s8(_pen_view([_pen("p1", "acceptance", 100000)], acc=0.60))
    blob = (r["problem_digest"] + " " + " ".join(r["caveats"]) + " "
            + " ".join(r["solution"]["actions"])).lower()
    for w in EVASION_WORDS:
        assert w not in blob, f"lộ hướng dẫn lách: '{w}' — {blob}"
    # phải nêu hành động TUÂN THỦ
    assert any("nâng" in a or "tuân thủ" in a or "đạt" in a or "giữ" in a
               for a in r["solution"]["actions"])


def test_s8_numbers_traceable():
    r = solve_s8(_pen_view([_pen("p1", "conduct", 200000)], acc=0.80))
    assert r["numbers"]
    for n in r["numbers"]:
        assert n["source"].startswith(("penalization:", "statistic_daily:", "policy_v:"))


def test_s8_waived_penalty_excluded():
    r = solve_s8(_pen_view([_pen("p1", "conduct", 200000, status="waived")]))
    assert r["solution"]["total_deducted_vnd"] == 0


def test_s8_determinism():
    v = _pen_view([_pen("p1", "conduct", 200000)], acc=0.80)
    assert solve_s8(v) == solve_s8(v)


# ================= S9 AnomalyAlert (UC7) =================

def test_s9_schema(reg):
    v = _anom_view([_flag("f1")])
    assert reg.validate("anomaly_alert_input", v) == []
    assert reg.validate("solver_report", solve_s9(v)) == []


def test_s9_never_accuses():
    """GUARDRAIL CỐT LÕI: KHÔNG kết tội — chỉ 'ghi nhận dấu hiệu'."""
    r = solve_s9(_anom_view([_flag("f1", "off_app", "high", 0.8)]))
    blob = (r["problem_digest"] + " " + " ".join(r["caveats"])).lower()
    for w in ACCUSATION_WORDS:
        assert w not in blob, f"kết tội: '{w}' — {blob}"
    assert "ghi nhận" in r["problem_digest"]
    assert NOT_CONCLUSION in r["caveats"]


def test_s9_requires_confidence_and_recommendation():
    r = solve_s9(_anom_view([_flag("f1", conf=0.42)]))
    assert "độ tin cậy" in r["problem_digest"]
    assert any("liên hệ" in c or "kiểm tra" in c for c in r["caveats"])
    assert r["solution"]["items"][0]["confidence"] == 0.42


def test_s9_cleared_flags_silent():
    """Cờ đã khép (cleared/confirmed) → im lặng, không cằn nhằn."""
    r = solve_s9(_anom_view([_flag("f1", status="cleared")]))
    assert r["solution"]["notable"] is False
    assert r["solution"]["open_count"] == 0
    assert "không có dấu hiệu" in r["problem_digest"]


def test_s9_no_flags_silent():
    r = solve_s9(_anom_view([]))
    assert r["solution"]["notable"] is False
    pack = build_context_pack("F3", [r], [], driver_id="d-1")
    assert "dấu hiệu" not in render_template("F3", [r], [], pack["numbers_registry"])["message"]


def test_s9_does_not_leak_detection_details():
    """Chống dạy lách: KHÔNG lộ evidence_ref/ngưỡng phát hiện."""
    r = solve_s9(_anom_view([_flag("f1", "gps_anomaly", "high", 0.9)]))
    blob = str(r["solution"]) + r["problem_digest"]
    assert "evidence" not in blob.lower()
    for w in EVASION_WORDS:
        assert w not in blob.lower()


def test_s9_severity_ordering():
    r = solve_s9(_anom_view([_flag("f1", sev="low"), _flag("f2", sev="high")]))
    assert r["solution"]["items"][0]["fraud_id"] == "f2"  # high trước
    assert r["solution"]["top_severity"] == "high"


# ================= derivation + pipeline =================

def test_derivations_from_real_tables(reg, tables, policy):
    pens = tables["driver_penalization_ATA"]
    frauds = tables["public_frauds"]
    assert pens and frauds, "data phải có penalization + fraud"
    drv = pens[0]["driver_id"]
    d = pens[0]["local_date"]
    pv = derive_penalty_explain_input_l1r(drv, f"{d}T20:00:00+07:00", tables, policy)
    assert reg.validate("penalty_explain_input", pv) == [], pv
    assert reg.validate("solver_report", solve_s8(pv)) == []
    fdrv = frauds[0]["driver_id"]
    fd = frauds[0]["detected_at"][:10]
    av = derive_anomaly_alert_input_l1r(fdrv, f"{fd}T20:00:00+07:00", tables)
    assert reg.validate("anomaly_alert_input", av) == [], av
    assert av["source"] == "INFERRED"
    assert reg.validate("solver_report", solve_s9(av)) == []


def test_router_wires_uc6_uc7_to_f3_only():
    f3 = route("F3", None)["solvers"]
    assert "penalty_explain" in f3 and "anomaly_alert" in f3
    # quyết định sản phẩm: KHÔNG bắn cảnh báo giữa ca
    assert "anomaly_alert" not in route("F2", None)["solvers"]
    assert route("F3", "vì sao tôi bị trừ tiền")["intent"] == "penalty_why"
    assert route("F3", "có cảnh báo bất thường gì không")["intent"] == "anomaly_check"


# ---------- research đợt 4: thang chính thức + hạn giải trình 48h ----------

def test_s9_uses_official_4_level_scale():
    """F-2: dùng ĐÚNG thang app (Không/Thấp/Cao/Rất cao) — không phải low/medium/high."""
    from gsm_core.solvers.anomaly_alert import NO_ALERT_LEVEL, OFFICIAL_LEVEL
    assert set(OFFICIAL_LEVEL.values()) == {"Thấp", "Cao", "Rất cao"}
    r = solve_s9(_anom_view([_flag("f1", sev="high")]))
    assert r["solution"]["items"][0]["official_level"] == "Rất cao"
    assert r["solution"]["official_level_top"] == "Rất cao"
    assert "mức cảnh báo: Rất cao" in r["problem_digest"]
    # không cờ → mức "Không"
    assert solve_s9(_anom_view([]))["solution"]["official_level_top"] == NO_ALERT_LEVEL


def test_s9_explain_deadline_48h_countdown():
    """F-3: nhắc hạn giải trình 48h; số giờ còn lại phải TRACE được (có trong numbers)."""
    v = _anom_view([_flag("f1")])           # detected 2026-07-05T18:00
    v["t_now"] = "2026-07-06T18:00:00+07:00"  # +24h → còn 24h
    r = solve_s9(v)
    item = r["solution"]["items"][0]
    assert item["explain_hours_left"] == pytest.approx(24.0, abs=0.1)
    assert item["explain_overdue"] is False
    assert "giải trình" in r["problem_digest"]
    hrs = [n for n in r["numbers"] if n["unit"] == "hours"]
    assert hrs and "deadline=48h" in hrs[0]["source"], "số giờ phải trace được"


def test_s9_explain_deadline_overdue_no_fake_countdown():
    """Quá hạn → KHÔNG nêu số giờ dương; hướng sang liên hệ hỗ trợ."""
    v = _anom_view([_flag("f1")])
    v["t_now"] = "2026-07-09T18:00:00+07:00"  # +96h > 48h
    r = solve_s9(v)
    assert r["solution"]["items"][0]["explain_overdue"] is True
    assert "đã qua" in r["problem_digest"]
    assert not [n for n in r["numbers"] if n["unit"] == "hours"], "không bịa giờ còn lại"


def test_s9_missing_detected_at_does_not_invent_deadline():
    """Thiếu mốc thời gian → KHÔNG đoán hạn (thà thiếu còn hơn bịa)."""
    f = _flag("f1"); f["detected_at"] = None
    r = solve_s9(_anom_view([f]))
    assert r["solution"]["items"][0]["explain_hours_left"] is None
    assert "giờ để giải trình" not in r["problem_digest"]


def test_bug_pi5d_01_deadline_number_passes_verifier(reg, tmp_path):
    """BUG-PI5d-01: template tự format "24 giờ" ≠ chuỗi render từ registry ("24,0 giờ")
    ⇒ verifier V1 coi là SỐ TRẦN và VETO cả advice. Mọi số phải neo registry."""
    v = _anom_view([_flag("f1", sev="medium", conf=0.58)])
    v["t_now"] = "2026-07-06T18:00:00+07:00"  # còn 24h
    r = solve_s9(v)
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=tmp_path / "ep.db", llm_mode="off")
    req = {"schema_version": "1.0.0", "request_id": "r1", "driver_id": "d-1", "feature": "F3",
           "free_text_query": None, "l3_view_refs": [], "session_id": "s",
           "t_request": "2026-07-06T18:00:00+07:00", "trigger_source": "user_ask"}
    advice = pipe.handle(req, solver_reports=[r], kb_track="platform")
    assert pipe.last_verify_result["passed"] is True, pipe.last_verify_result
    assert "giải trình" in advice["message"]
    assert reg.validate("composed_advice", advice) == []


def test_s8_mentions_explain_right_48h():
    """F-3: S8 nhắc QUYỀN giải trình + hạn 48h (không xây quy trình khiếu nại — D-007)."""
    r = solve_s8(_pen_view([_pen("p1", "conduct", 200000)]))
    blob = " ".join(r["caveats"])
    assert "GIẢI TRÌNH TRỰC TUYẾN" in blob and "48 giờ" in blob


def test_s7_points_to_official_feature():
    """F-1: app ĐÃ CÓ bản đồ nhiệt → trỏ về tính năng chính thức, không tự chọn khu."""
    from gsm_core.solvers.idle_reduction import USE_OFFICIAL_FEATURE, solve as solve_s7
    v = {"schema_version": "1.0.0", "driver_id": "d-1", "t_now": "2026-07-01T18:00:00+07:00",
         "session_date": "2026-07-01",
         "idle_segments": [{"hex": "8amock01", "start": "2026-07-01T14:00:00+07:00",
                             "duration_seconds": 3600, "hour": 14}],
         "total_idle_min": 60.0, "longest_idle_min": 60.0, "online_hours": 8.0,
         "demand_by_hour": {"14": 0.2}, "active_reposition": None,
         "view_version": "1.0.0", "source": "MOCK"}
    r = solve_s7(v)
    assert USE_OFFICIAL_FEATURE in r["caveats"]
    assert "Nhiệm vụ tiếp theo" in USE_OFFICIAL_FEATURE
    # vẫn KHÔNG chỉ định ô H3 (D-004b/B1)
    assert "8amock01" not in str(r["solution"]) + r["problem_digest"]


@pytest.mark.parametrize("q,intent", [
    # BUG-PI5c-01: "bất thường"→"bat thuong" CHỨA "thuong" (=thưởng/bonus) sau khi bỏ dấu
    ("có cảnh báo bất thường gì không", "anomaly_check"),
    ("tôi bị trừ tiền vì sao", "penalty_why"),
    ("tuần này thưởng bao nhiêu", "policy_bonus"),   # thưởng THẬT vẫn về policy_bonus
    ("khoán tuần còn thiếu bao nhiêu", "weekly_target"),
])
def test_bug01_vietnamese_homograph_routing(q, intent):
    """Đồng âm sau bỏ dấu: keyword DÀI NHẤT thắng (cụm cụ thể > từ đơn)."""
    assert route("F3", q)["intent"] == intent


def test_pipeline_f3_end_to_end(reg, tmp_path):
    s8 = solve_s8(_pen_view([_pen("p1", "clawback_khoan", 40000)], acc=0.83))
    s9 = solve_s9(_anom_view([_flag("f1", "route_deviation", "medium", 0.5)]))
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=tmp_path / "ep.db", llm_mode="off")
    req = {"schema_version": "1.0.0", "request_id": "r1", "driver_id": "d-1", "feature": "F3",
           "free_text_query": None, "l3_view_refs": [], "session_id": "s",
           "t_request": "2026-07-10T20:00:00+07:00", "trigger_source": "user_ask"}
    advice = pipe.handle(req, solver_reports=[s8, s9], kb_track="platform")
    assert reg.validate("composed_advice", advice) == []
    assert pipe.last_verify_result["passed"] is True, pipe.last_verify_result
    msg = advice["message"].lower()
    for w in ACCUSATION_WORDS + EVASION_WORDS:
        assert w not in msg, f"message vi phạm guardrail: '{w}'"
    assert "chưa phải kết luận vi phạm" in advice["message"]

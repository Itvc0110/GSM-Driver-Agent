"""PI-5b — S7 IdleReduction (UC5) + guardrail D-004b.

Kiểm: view/report hợp schema; số idle khớp dữ liệu ĐO ĐƯỢC; KHÔNG bịa vấn đề khi
tài xế không chờ nhiều; **KHÔNG chỉ định ô/khu vực đứng** (B1); khu vực chỉ nhắc
nhiệm vụ CHÍNH THỨC; cảnh báo tỷ lệ nhận + nhãn ước lượng luôn có.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gsm_core.advisor.context_pack import build_context_pack
from gsm_core.advisor.pipeline import AdvisorPipeline
from gsm_core.advisor.router import route
from gsm_core.advisor.templates import render_template
from gsm_core.features.from_l1r import derive_idle_reduction_input_l1r
from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.schema_registry import SchemaRegistry
from gsm_core.solvers.idle_reduction import solve, WARN_ACCEPTANCE, WARN_PROXY

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "research" / "policy" / "t004-current-policy-text-corpus-2026-07-22.json"


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def tables():
    with TemporaryDirectory() as td:
        return generate_realdata(days=6, seed_base=900, out_dir=Path(td))["tables"]


def _view(segs, total=None, longest=None, online=8.0, demand=None, repo=None):
    total = total if total is not None else sum(s["duration_seconds"] for s in segs) / 60
    longest = longest if longest is not None else (
        max((s["duration_seconds"] for s in segs), default=0) / 60)
    return {"schema_version": "1.0.0", "driver_id": "d-1", "t_now": "2026-07-01T18:00:00+07:00",
            "session_date": "2026-07-01", "idle_segments": segs,
            "total_idle_min": round(total, 2), "longest_idle_min": round(longest, 2),
            "online_hours": online, "demand_by_hour": demand or {}, "active_reposition": repo,
            "view_version": "1.0.0", "source": "MOCK"}


def _seg(hour, minutes, hex_="8amock01"):
    return {"hex": hex_, "start": f"2026-07-01T{hour:02d}:00:00+07:00",
            "duration_seconds": int(minutes * 60), "hour": hour}


# ---------- schema ----------

def test_view_and_report_schema(reg):
    v = _view([_seg(14, 30), _seg(15, 25)], demand={"14": 0.2, "15": 0.3})
    assert reg.validate("idle_reduction_input", v) == []
    r = solve(v)
    assert reg.validate("solver_report", r) == []
    assert r["solver"] == "idle_reduction"


# ---------- số học + không bịa vấn đề ----------

def test_idle_totals_match_measured():
    v = _view([_seg(14, 30), _seg(15, 25)], demand={"14": 0.2})
    r = solve(v)
    assert r["solution"]["total_idle_min"] == 55.0
    assert r["solution"]["longest_idle_min"] == 30.0
    assert r["solution"]["idle_share"] == pytest.approx(55 / 60 / 8, abs=0.01)


def test_no_notable_idle_does_not_invent_problem():
    """Chờ ít → KHÔNG cảnh báo, KHÔNG gợi ý (bài học: không bịa vấn đề)."""
    r = solve(_view([_seg(10, 8)], demand={"10": 0.2}))
    assert r["solution"]["notable"] is False
    assert r["solution"]["worst_window"] is None
    assert r["infeasible_reason"] == "không có khoảng chờ đáng lưu ý"
    pack = build_context_pack("F3", [r], [], driver_id="d-1")
    assert "chờ tổng" not in render_template("F3", [r], [], pack["numbers_registry"])["message"]


def test_worst_window_only_when_demand_low():
    """Chờ nhiều nhưng ĐÚNG khung nhu cầu CAO → không đổ lỗi khung đó."""
    r_low = solve(_view([_seg(14, 60)], demand={"14": 0.2}))
    assert r_low["solution"]["worst_window"]["hour"] == 14
    r_high = solve(_view([_seg(17, 60)], demand={"17": 0.95}))
    assert r_high["solution"]["worst_window"] is None  # 17h là giờ cao điểm


# ---------- GUARDRAIL D-004b ----------

def test_never_directs_to_a_specific_cell():
    """B1: KHÔNG chọn điểm đứng hộ — không ô H3 nào trong solution/message."""
    v = _view([_seg(14, 60, hex_="8amock42")], demand={"14": 0.1})
    r = solve(v)
    assert "8amock42" not in str(r["solution"]), r["solution"]
    assert "8amock42" not in r["problem_digest"]
    pack = build_context_pack("F2", [r], [], driver_id="d-1")
    msg = render_template("F2", [r], [], pack["numbers_registry"])["message"]
    assert "8amock42" not in msg and "hex" not in msg.lower(), msg


def test_mandatory_warnings_always_present():
    """Điều kiện 3 & 4: cảnh báo tỷ lệ nhận + nhãn ước lượng luôn có trong caveats."""
    for v in (_view([_seg(14, 60)], demand={"14": 0.2}), _view([_seg(10, 5)])):
        r = solve(v)
        assert WARN_ACCEPTANCE in r["caveats"]
        assert WARN_PROXY in r["caveats"]


def test_reposition_only_from_official_mission():
    """Điều kiện 2: chỉ nhắc nhiệm vụ CHÍNH THỨC (có campaign_id); không có → im lặng."""
    no_repo = solve(_view([_seg(14, 60)], demand={"14": 0.2}))
    assert no_repo["solution"]["reposition_mission"] is None
    with_repo = solve(_view([_seg(14, 60)], demand={"14": 0.2},
                            repo={"campaign_id": "repo-01", "target_hex": "8ax", "reached": False}))
    assert "nhiệm vụ di chuyển của hãng" in with_repo["solution"]["reposition_mission"]
    assert "8ax" not in str(with_repo["solution"])  # không lộ ô đích như chỉ dẫn của ta


def test_no_income_promise_in_digest():
    r = solve(_view([_seg(14, 60)], demand={"14": 0.2}))
    low = r["problem_digest"].lower()
    for bad in ("đảm bảo", "chắc chắn kiếm", "cam kết"):
        assert bad not in low, r["problem_digest"]


def test_determinism():
    v = _view([_seg(14, 60), _seg(9, 30)], demand={"14": 0.2, "9": 0.3})
    assert solve(v) == solve(v)


# ---------- derivation từ data thật + pipeline ----------

def test_derivation_from_real_tables(reg, tables):
    hx = [h for h in tables["public_driver_hex_tracking"] if h.get("tracking_status") == "idle"]
    assert hx, "data phải có bản ghi idle"
    drv = hx[0]["driver_id"]
    d = (hx[0].get("last_seen_at") or "")[:10]
    v = derive_idle_reduction_input_l1r(drv, f"{d}T18:00:00+07:00", tables, session_date=d)
    assert reg.validate("idle_reduction_input", v) == [], v
    # tổng phút idle == tổng stay_duration đo được (chỉ segment ≥5 phút)
    expect = sum(h["stay_duration_seconds"] for h in tables["public_driver_hex_tracking"]
                 if h["driver_id"] == drv and (h.get("last_seen_at") or "")[:10] == d
                 and h.get("tracking_status") == "idle" and h["stay_duration_seconds"] >= 300)
    assert v["total_idle_min"] == pytest.approx(expect / 60, abs=0.02)
    assert reg.validate("solver_report", solve(v)) == []


def test_bug01_idle_never_exceeds_online_time(tables):
    """BUG-PI5b-01 (conservation): Σ thời gian CHỜ không được vượt giờ ONLINE.

    Trước fix: dwell offline dài (vd 20 giờ đứng yên qua đêm) bị gán `tracking_status=idle`
    ⇒ "chờ tổng 1300 phút" trong khi online 4.8h — bất khả, lại bị `min(1.0, …)` che.
    """
    onl = {(r["driver_id"], r["local_date"]): r["online_time"]
           for r in tables["driver_online_hours_sap_id"]}
    seen = 0
    for (drv, d), online_h in onl.items():
        if online_h <= 0:
            continue
        v = derive_idle_reduction_input_l1r(drv, f"{d}T23:00:00+07:00", tables, session_date=d)
        if not v["idle_segments"]:
            continue
        seen += 1
        assert v["total_idle_min"] <= online_h * 60 + 1, (
            f"{drv} {d}: chờ {v['total_idle_min']:.0f}ph > online {online_h * 60:.0f}ph")
        assert solve(v)["solution"]["data_warning"] is None
    assert seen > 0, "phải kiểm được ít nhất 1 driver-day có idle"


def test_data_warning_surfaces_impossible_input():
    """Nếu data VẪN mâu thuẫn (idle > online) → phải NÊU cờ, không im lặng kẹp 100%."""
    r = solve(_view([_seg(14, 600)], online=1.0, demand={"14": 0.2}))
    assert r["solution"]["data_warning"], "phải cảnh báo dữ liệu bất khả"
    assert any("vượt giờ online" in c for c in r["caveats"])


def test_router_wires_idle_to_f2_f3():
    assert "idle_reduction" in route("F2", None)["solvers"]
    assert "idle_reduction" in route("F3", None)["solvers"]
    assert route("F2", "hôm nay chờ lâu quá ế khách")["intent"] == "idle_wait"


def test_pipeline_end_to_end(reg, tmp_path):
    r = solve(_view([_seg(14, 60)], demand={"14": 0.15}))
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=tmp_path / "ep.db", llm_mode="off")
    req = {"schema_version": "1.0.0", "request_id": "r1", "driver_id": "d-1", "feature": "F2",
           "free_text_query": None, "l3_view_refs": [], "session_id": "s",
           "t_request": "2026-07-01T18:00:00+07:00", "trigger_source": "user_ask"}
    advice = pipe.handle(req, solver_reports=[r], kb_track="platform")
    assert reg.validate("composed_advice", advice) == []
    assert pipe.last_verify_result["passed"] is True, pipe.last_verify_result
    assert "chờ tổng" in advice["message"], advice["message"]

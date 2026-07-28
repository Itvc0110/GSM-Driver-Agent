"""Contract tests — response của backend PHẢI khớp JSON Schema trong ui/contracts/.

Đây là điểm đồng bộ web ↔ Flutter (contract-first): schema đỏ = một trong hai UI
sẽ vỡ ở runtime. Chạy: uv run pytest ui/backend/tests -q (cần extra `ui`).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import validate

from app.main import app

CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"
client = TestClient(app)


def _schema(name: str) -> dict:
    return json.loads((CONTRACTS / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def dv() -> dict:
    r = client.get("/api/v1/driver/default-view")
    assert r.status_code == 200
    return r.json()


def test_driver_state_matches_contract(dv):
    r = client.get(f"/api/v1/driver/state?driver_id={dv['driver_id']}&date={dv['date']}")
    assert r.status_code == 200
    body = r.json()
    validate(body, _schema("driver_state"))
    # ranh giới tiền (CLAUDE §5): payout PHẢI bằng tổng breakdown — không rò tiền
    m = body["money"]
    assert m["payout_vnd"] == sum(m["payout_breakdown"].values())
    assert m["gross_vnd"] >= m["payout_breakdown"]["trip_payout_vnd"]
    assert m["est_net_vnd"] is None, "est_net chỉ được có số khi đủ known costs"


def test_map_context_matches_contract(dv):
    r = client.get(f"/api/v1/map-context?date={dv['date']}&hour=18")
    assert r.status_code == 200
    validate(r.json(), _schema("map_context"))


def test_advice_matches_contract_all_hours(dv):
    for now_min in (9 * 60, 14 * 60, 21 * 60 + 30):
        r = client.get(f"/api/v1/advice?driver_id={dv['driver_id']}&date={dv['date']}&now_min={now_min}")
        assert r.status_code == 200
        body = r.json()
        validate(body, _schema("advice"))
        # im lặng và có-items phải loại trừ nhau
        assert body["silent"]["is_silent"] == (len(body["items"]) == 0)


def test_advice_car_fleet_is_silent_not_wrong(dv):
    """Đội car không có policy bike — advisor phải IM LẶNG chứ không áp bừa số."""
    r = client.get(f"/api/v1/advice?driver_id=cp-0&date={dv['date']}&now_min=840")
    body = r.json()
    validate(body, _schema("advice"))
    assert body["silent"]["is_silent"] and body["silent"]["reason_code"] == "no_active_channel"


def test_state_deterministic(dv):
    """Cùng driver/ngày → byte-identical (không random trong adapter)."""
    url = f"/api/v1/driver/state?driver_id={dv['driver_id']}&date={dv['date']}"
    assert client.get(url).content == client.get(url).content


def test_history_days_bounded(dv):
    r = client.get(f"/api/v1/driver/history?driver_id={dv['driver_id']}&date={dv['date']}&days=14")
    body = r.json()
    assert 1 <= len(body["days"]) <= 14
    assert body["days"][-1]["date"] == dv["date"]
    assert all(d["payout_vnd"] <= d["gross_vnd"] for d in body["days"])


# ---------- U3: khu Mô phỏng (sim-engine endpoints) ----------


def test_sim_journey_matches_contract():
    run = client.get("/api/v1/sim/run?seed=1000").json()
    aid = run["actors"][0]["actor_id"]
    r = client.get(f"/api/v1/sim/journey?seed=1000&actor_id={aid}")
    assert r.status_code == 200
    body = r.json()
    validate(body, _schema("journey"))
    # bảo toàn 4 nguồn (kế thừa BUG-SIM2-01): tổng breakdown == payout == cuối income_curve
    m = body["metrics"]
    parts = (m["trip_payout_vnd"] + m["day_bonus_vnd"]
             + m["mission_reward_vnd"] + m["newbie_vnd"])
    assert parts == m["payout_vnd"]
    if body["income_curve"]:
        assert body["income_curve"][-1][1] == m["payout_vnd"]


def test_sim_replay_matches_contract():
    r = client.get("/api/v1/sim/replay?seed=1000")
    assert r.status_code == 200
    body = r.json()
    validate(body, _schema("replay"))
    assert body["stations"], "mất trạm pin"
    # legs phải có thứ tự thời gian trong từng actor
    for a in body["actors"][:5]:
        ts = [g["t0_min"] for g in a["legs"]]
        assert ts == sorted(ts)


def test_sim_ab_matches_contract_and_guardrail_fields():
    r = client.get("/api/v1/sim/ab?seed=1000")
    assert r.status_code == 200
    body = r.json()
    validate(body, _schema("ab_result"))
    assert "1 seed" in body["warning_text"], "warning đọc-số bắt buộc bị mất"
    t = body["target_actors"][0]
    assert t["delta_vnd"] == t["payout_b_vnd"] - t["payout_a_vnd"]


def test_sim_ab_guardrail_is_real_per_cell_and_never_verdicts_on_one_seed():
    """AUDIT STATS-2 + STATS-1: guardrail là số per-cell THẬT, và 1 seed thì KHÔNG
    được phán 'ổn/xấu' — ok phải là null (verdict thật ở sweep ≥30 seed)."""
    body = client.get("/api/v1/sim/ab?seed=1000").json()
    g = body["guardrail"]
    assert isinstance(g["flagged_cells"], list)
    assert g["ok"] is None, "endpoint 1-seed không được ra phán quyết ổn/xấu"
    assert isinstance(g["others_payout_delta_vnd"], int)
    if g["flagged_cells"]:
        assert g["worst_cell_delta_served"] <= -3
    else:
        assert g["worst_cell_delta_served"] > -3


# ---------- UX-CARDS (UPDATE-067): adherence action round-trip ----------


def test_advice_action_roundtrip_and_contract(dv, tmp_path, monkeypatch):
    """POST action → GET actions thấy lại đúng bản ghi, khớp schema advice_action;
    log vào file tạm (không bẩn data/ui-telemetry thật của phiên review)."""
    from app.routers import advice as advice_router
    monkeypatch.setattr(advice_router, "TELEMETRY_DIR", tmp_path)
    monkeypatch.setattr(advice_router, "ACTIONS_FILE", tmp_path / "a.jsonl")
    body = {"advice_id": "s1-test-1", "driver_id": dv["driver_id"], "date": dv["date"],
            "action": "followed", "card_kind": "nudge", "at_min": 840}
    r = client.post("/api/v1/advice/action", json=body)
    assert r.status_code == 200 and r.json()["ok"]
    validate(r.json()["logged"], _schema("advice_action"))
    got = client.get(f"/api/v1/advice/actions?driver_id={dv['driver_id']}").json()
    assert got["is_mock"] and got["actions"][0]["advice_id"] == "s1-test-1"


def test_advice_action_rejects_bad_action(dv):
    r = client.post("/api/v1/advice/action", json={
        "advice_id": "x", "driver_id": dv["driver_id"], "date": dv["date"],
        "action": "maybe_later", "card_kind": "nudge"})
    assert r.status_code == 422, "action ngoài enum phải bị chặn ở validation"


# ---------- R5-A (UPDATE-071): đường UI cards PHẢI có guardrail như pipeline ----------

_UNIT_KEY = {"điểm": "points", "vnd": "vnd", "giờ": "hours", "cuốc": "trips"}


def test_advice_items_pass_verifier(dv):
    """Mọi card trả cho tài xế phải qua verifier tầng 1. Trước R5, đường này KHÔNG có
    guardrail nào — mọi fix ở batch 3 chỉ bảo vệ pipeline C6, không bảo vệ cards."""
    from gsm_core.advisor import verifier as V
    from gsm_core.vn_format import render_number_vn
    for now_min in (9 * 60, 14 * 60, 19 * 60):
        body = client.get(f"/api/v1/advice?driver_id={dv['driver_id']}&date={dv['date']}"
                          f"&now_min={now_min}").json()
        for it in body["items"]:
            rendered = [render_number_vn(n["value"], _UNIT_KEY.get(n["unit"], "count"))
                        for n in it.get("numbers", [])]
            text = f"{it['title']} {it['message']}"
            assert V.check_bare_numbers(text, rendered) == [], \
                f"card {it['advice_id']} có số trần không trace được"
            assert V.check_blocklist(text, None) == [], \
                "card vi phạm blocklist (hứa thu nhập / khuyên đơn cụ thể)"


def test_rates_do_not_leak_same_day_data(dv):
    """ĐA-01: `build_gi` KHÔNG được đọc tỷ lệ của **chính ngày đó**.

    Bản cũ lấy `driver_statistic_daily` của `date` — aggregate CẢ NGÀY — nên ở 9h sáng S1 đã
    biết tỷ lệ cuối ngày. Test này tái tính độc lập từ ≤7 ngày TRƯỚC và bắt buộc khớp; đồng thời
    ràng buộc kết quả **không** bằng tỷ lệ cùng ngày (nếu bằng thì leak vẫn còn).
    """
    import polars as pl
    from app.adapters import advisor as A
    from app.adapters.mockdata import _table, _stat_row
    from gsm_core.rates import shrunk_rate

    stat = _table("driver_statistic_daily")
    drv, date = dv["driver_id"], dv["date"]

    # (1) tái tính độc lập
    prev = (stat.filter((pl.col("driver_id") == drv) & (pl.col("local_date") < date))
            .sort("local_date").tail(A.RATE_WINDOW_DAYS))
    k = float(prev["accepted_count"].sum() or 0)
    n = float(prev["total_request_calculate_accept"].sum() or 0)
    pool = stat.filter(pl.col("local_date") < date)
    p0 = float(pool["accepted_count"].sum()) / float(pool["total_request_calculate_accept"].sum())
    expect = round(shrunk_rate(k, n, p0, A.SHRINK_PSEUDO_COUNTS), 4)
    got = A.build_gi(drv, date, 9 * 60)["acceptance_rate"]
    assert got == pytest.approx(expect, abs=1e-9)

    # (2) không được là con số CỦA NGÀY HÔM ĐÓ
    same_day = float((_stat_row(drv, date) or {}).get("acceptance_rate", -1))
    assert got != pytest.approx(same_day, abs=1e-6), "vẫn đang đọc tỷ lệ của chính ngày đó"

    # (3) không phụ thuộc giờ trong ngày — as-of đầu ngày, không rò về sau
    assert A.build_gi(drv, date, 21 * 60)["acceptance_rate"] == got


def test_no_perfect_rate_fallback_on_first_day():
    """Không có lịch sử ⇒ trả **prior**, KHÔNG trả 1.0.

    Fallback `or 1.0` cũ nghĩa là "hoàn hảo" ⇒ gate thưởng (≥0,85) đi qua nhầm cho đúng nhóm
    chưa có dữ liệu nào để tin. ĐA-01 cấm tường minh."""
    from app.adapters import advisor as A
    from app.adapters.mockdata import _table
    first = _table("driver_statistic_daily")["local_date"].min()
    drv = _table("driver_statistic_daily")["driver_id"][0]
    gi = A.build_gi(drv, first, 9 * 60)
    assert gi["acceptance_rate"] != 1.0 and gi["completion_rate"] != 1.0
    assert 0.0 < gi["acceptance_rate"] < 1.0


def test_advice_seed_matches_dataset_seed(dv):
    """C2 §5.2: `/advice` khai `seed: 0` trong khi data thật sinh bằng `seed_base` của manifest
    (7000). Hai endpoint của CÙNG một dataset trả hai định danh khác nhau ⇒ không ai truy được
    advice này đọc từ đâu. `seed` phải cùng một nguồn với `/driver/state`."""
    from app.adapters.mockdata import manifest
    adv = client.get(f"/api/v1/advice?driver_id={dv['driver_id']}&date={dv['date']}").json()
    st = client.get(f"/api/v1/driver/state?driver_id={dv['driver_id']}&date={dv['date']}").json()
    assert adv["seed"] == st["payout_summary"]["seed"], \
        "advice và driver/state khai seed khác nhau cho cùng dataset"
    assert adv["seed"] == int(manifest()["seed_base"])
    # kể cả đường im lặng (đội car/premium) cũng không được khai seed giả
    silent = client.get(f"/api/v1/advice?driver_id=cp-0&date={dv['date']}").json()
    assert silent["seed"] == int(manifest()["seed_base"])


def test_maxed_but_rates_at_risk_is_not_silenced(dv, monkeypatch):
    """C2 §1b: kịch mốc điểm NHƯNG tỷ lệ dưới ngưỡng ⇒ chính sách trả **0đ**.

    Adapter cũ chỉ nhìn `already_maxed` rồi trả silent *"không có gì cần chỉnh. Giữ nhịp hiện
    tại."* — trấn an một người đang mất sạch thưởng và VẪN CÒN CỨU ĐƯỢC. Card cảnh báo phải
    ra, và phải qua verifier như mọi card khác.
    """
    from gsm_core.advisor import verifier as V
    from gsm_core.vn_format import render_number_vn
    from app.adapters import advisor as adv

    at_risk_report = {
        "solution": {"already_maxed": True, "feasible": False, "gap_points": 0,
                     "constraints": {"ok_acceptance": False, "ok_completion": True,
                                     "enough_hours": True}},
        "confidence": 0.85,
        "caveats": ["thưởng chỉ được trả khi tỷ lệ nhận/hoàn thành giữ trên ngưỡng đến cuối ngày"],
        "infeasible_reason": "tỷ lệ nhận dưới ngưỡng",
        "numbers": [{"value": 170000, "unit": "vnd", "source": "policy_v:x"}],
    }
    monkeypatch.setattr(adv.bonus_feasibility, "solve", lambda *a, **kw: at_risk_report)

    body = client.get(f"/api/v1/advice?driver_id={dv['driver_id']}&date={dv['date']}").json()
    validate(body, _schema("advice"))
    assert body["silent"]["is_silent"] is False, "im lặng trong lúc tài xế sắp mất toàn bộ thưởng"
    assert body["items"], "phải có card cảnh báo"
    it = body["items"][0]
    assert it["reason_code"] in ("acceptance_below_threshold", "completion_below_threshold")
    assert "tỷ lệ" in it["message"], "phải nói rõ nghẽn ở tỷ lệ — đó là thứ còn cứu được"
    rendered = [render_number_vn(n["value"], _UNIT_KEY.get(n["unit"], "count"))
                for n in it.get("numbers", [])]
    text = f"{it['title']} {it['message']}"
    assert V.check_bare_numbers(text, rendered) == []
    assert V.check_blocklist(text, None) == []


def test_maxed_and_safe_stays_silent(dv, monkeypatch):
    """Đối chứng: kịch mốc VÀ tỷ lệ đủ ⇒ im lặng vẫn là hành vi ĐÚNG (không cảnh báo thừa)."""
    from app.adapters import advisor as adv
    safe = {"solution": {"already_maxed": True, "feasible": True, "gap_points": 0,
                         "constraints": {"ok_acceptance": True, "ok_completion": True,
                                         "enough_hours": True}},
            "confidence": 0.95, "caveats": [], "infeasible_reason": None,
            "numbers": [{"value": 170000, "unit": "vnd", "source": "policy_v:x"}]}
    monkeypatch.setattr(adv.bonus_feasibility, "solve", lambda *a, **kw: safe)
    body = client.get(f"/api/v1/advice?driver_id={dv['driver_id']}&date={dv['date']}").json()
    validate(body, _schema("advice"))
    assert body["silent"]["is_silent"] is True
    assert body["silent"]["reason_code"] == "already_on_track"


def test_poisoned_advice_never_reaches_response(dv, monkeypatch):
    """Inject item độc (số trần + hứa thu nhập) → response phải IM LẶNG với
    reason_code verify_failed, KHÔNG lọt ra ngoài (fail-closed như FAILCLOSED-1)."""
    from app.adapters import advisor as adv

    def poisoned(*a, **kw):
        return {"scenario_id": "x", "seed": 0, "data_mode": "mock-realdata", "is_mock": True,
                "generated_at_min": 840, "silent": {"is_silent": False},
                "items": [{"advice_id": "poison-1", "solver": "S1", "kind": "bonus_gap",
                           "title": "Chắc chắn anh kiếm được 5.000.000đ hôm nay",
                           "message": "Cứ chạy đi, chắc chắn anh kiếm được 999.999đ.",
                           "confidence": 0.9, "reason_code": "feasible_gap",
                           "numbers": [], "caveat": ""}]}

    monkeypatch.setattr(adv, "_advice_raw", poisoned)
    body = client.get(f"/api/v1/advice?driver_id={dv['driver_id']}&date={dv['date']}").json()
    validate(body, _schema("advice"))
    assert body["items"] == [], "advice độc LỌT ra response"
    assert body["silent"]["is_silent"] and body["silent"]["reason_code"] == "verify_failed"


# ---------- R5-B F-01 (UPDATE-072): nhãn fleet phải khớp generator ----------


def test_fleet_labels_match_generator_prefixes():
    """Prefix trong `mockgen/profiles.py`: r=bike_rto · cp=car_platform · ce=car_employee
    · px=car_premium. Adapter từng map lệch một bậc (cp→car-premium, px→premium) ⇒ 15 tài
    xế VF5 hiện nhãn 'premium' trên picker."""
    from app.adapters.mockdata import FLEET_BY_PREFIX
    assert FLEET_BY_PREFIX["cp"] == "car-platform"
    assert FLEET_BY_PREFIX["px"] == "car-premium"
    assert FLEET_BY_PREFIX["ce"] == "car-employee"
    assert FLEET_BY_PREFIX["r"] == "bike-rto"
    cat = client.get("/api/v1/driver/catalog").json()
    by_fleet = {}
    for d in cat["drivers"]:
        by_fleet.setdefault(d["fleet"], []).append(d["driver_id"])
    assert all(x.startswith("cp-") for x in by_fleet["car-platform"])
    assert all(x.startswith("px-") for x in by_fleet["car-premium"])
    assert "premium" not in by_fleet, "nhãn 'premium' trơn là dấu hiệu map cũ còn sót"


# ---------- C2 parity (UPDATE-075): UI KHÔNG được tự tính giá ----------


def test_ui_fare_equals_sim_policy():
    """Cước UI phải bằng ĐÚNG `PolicyBundle.gross_fare` của sim. Trước C2, routing dùng
    `km × 24000` hard-code — lệch ~4,6× (5km: 120.000đ vs 25.900đ) và số 24000 không tồn
    tại ở bất kỳ config/spec nào. Đây là số tài xế nhìn trực tiếp.

    Test này soi `sim_pricing.quote_distance` — bản `origin/main`. (Nhánh này từng có
    `routing._gross_fare` làm cùng việc; merge 2026-07-28 giữ bản kia vì nó **đọc**
    `PolicyBundle` thay vì chép lại công thức, nên bất biến dưới đây mới có ý nghĩa: nếu ai
    hard-code lại thì hai vế lệch nhau.)
    """
    from pathlib import Path

    from app.adapters.sim_pricing import quote_distance
    from gsm_sim.config import Config
    from gsm_sim.policy import PolicyBundle
    # đường dẫn TUYỆT ĐỐI theo vị trí file test — bản đầu dùng relative path nên chỉ xanh khi
    # chạy từ repo root, đỏ khi chạy từ `ui/backend` (lỗi của test, không phải của code)
    repo = Path(__file__).resolve().parents[3]
    sim_policy = PolicyBundle.from_config(Config.load(repo / "configs" / "pilot_dongda.yaml"))
    for km in (0.5, 2.0, 5.0, 8.7, 15.0):
        assert quote_distance(km)["fare_vnd"] == sim_policy.gross_fare(km), f"cước lệch tại {km}km"
    # và KHÔNG được là công thức tuyến tính 24000/km nữa
    assert quote_distance(5.0)["fare_vnd"] != 5.0 * 24000


def test_no_hardcoded_fare_constant_in_routing():
    """Chặn hồi quy: hằng số cước không được xuất hiện lại trong routing."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "app" / "routers" / "routing.py").read_text(encoding="utf-8")
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    assert "24000" not in code, "hằng số cước hard-code quay lại trong routing.py"


def test_soc_is_labelled_mock_in_payload(dv):
    """Q-06 (Cường chốt phương án **b**): SOC **không tồn tại** trong 13 bảng GSM —
    `_soc_proxy` sinh nó bằng `sha256(driver|date)`. Số đó đang hiện `⚡{soc}%` trên app và
    tô đỏ khi <25%, **không nhãn**, nên tài xế đọc như telemetry thật.

    Nhãn phải đi **CÙNG DỮ LIỆU**, không hard-code trong JS: nếu chỉ sửa `app.js` thì màn hình
    kế tiếp (hoặc Flutter của Khánh) lại quên. Đây đúng bài học "sửa một tầng, tầng khác không
    biết" (hồ sơ `13-*` Phần 1)."""
    st = client.get(f"/api/v1/driver/state?driver_id={dv['driver_id']}&date={dv['date']}").json()
    validate(st, _schema("driver_state"))
    assert st.get("soc_source") == "MOCK", \
        "soc_percent phải mang nhãn nguồn để UI không thể hiển thị nó như số thật"
    assert st.get("vehicle_range_km_source") == "MOCK", \
        "tầm đi còn lại suy TỪ soc bịa ⇒ cũng phải mang nhãn"


def test_soc_label_reaches_the_screen():
    """Nhãn phải thực sự được RENDER, không chỉ nằm trong payload."""
    from pathlib import Path
    web = Path(__file__).resolve().parents[2] / "web"
    js = (web / "js" / "app.js").read_text(encoding="utf-8")
    html = (web / "index.html").read_text(encoding="utf-8")
    assert "soc_source" in js, "app.js không đọc nhãn nguồn của SOC"
    assert "pill-soc-tag" in html and "pill-soc-tag" in js, \
        "thiếu phần tử hiển thị nhãn MOCK cạnh chỉ báo pin"

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

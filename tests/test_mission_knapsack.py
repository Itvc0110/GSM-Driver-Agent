"""PI-4b — S6 MissionKnapsack (TDD).

Kiểm: view hợp schema; **DP == brute-force** (chứng minh tối ưu) trên 30 case ngẫu
nhiên có seed; không vượt quỹ giờ; loại mission hết hạn/đã claim; reward chỉ từ catalog;
determinism; chain từ data thật.
"""

import itertools
import random
from pathlib import Path

import pytest

from gsm_core.features.from_l1r import derive_mission_select_input_l1r
from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.schema_registry import SchemaRegistry
from gsm_core.solvers.mission_knapsack import solve, SLOT_MIN, _slots

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


def _view(missions, hours=8.0, tph=2.0):
    return {"schema_version": "1.0.0", "driver_id": "d-1",
            "t_now": "2026-07-01T14:00:00+07:00",
            "hours_budget_remaining": hours, "trips_per_hour": tph,
            "missions": missions, "view_version": "1.0.0", "source": "MOCK"}


def _m(mid, reward, remaining, **kw):
    return {"mission_id": mid, "name": kw.get("name", mid), "mission_type": "trip_count",
            "reward_vnd": reward, "remaining_count": remaining,
            "window_start": kw.get("ws"), "window_end": kw.get("we"),
            "state": kw.get("state")}


# ---------- schema ----------

def test_view_schema_valid(reg):
    assert reg.validate("mission_select_input", _view([_m("m1", 30000, 8)])) == []


def test_report_schema_valid(reg):
    r = solve(_view([_m("m1", 30000, 8)]))
    assert reg.validate("solver_report", r) == []
    assert r["solver"] == "mission_knapsack"


# ---------- TỐI ƯU: DP == brute-force ----------

def _brute_force(missions, hours, tph):
    cap = _slots(hours)
    best = 0
    items = [(int(m["reward_vnd"]), _slots(int(m["remaining_count"]) / tph))
             for m in missions if m["remaining_count"] > 0 and m["reward_vnd"] > 0]
    for r in range(len(items) + 1):
        for combo in itertools.combinations(items, r):
            if sum(c for _, c in combo) <= cap:
                best = max(best, sum(v for v, _ in combo))
    return best


@pytest.mark.parametrize("seed", range(30))
def test_dp_equals_brute_force(seed):
    """CHỨNG MINH tối ưu: DP phải bằng brute-force mọi tập con."""
    rng = random.Random(seed)
    n = rng.randint(1, 9)
    missions = [_m(f"m{i}", rng.choice([10000, 30000, 50000, 100000]), rng.randint(1, 25))
                for i in range(n)]
    hours, tph = rng.choice([2.0, 5.0, 8.0]), rng.choice([1.5, 2.0, 3.0])
    r = solve(_view(missions, hours=hours, tph=tph))
    assert r["solution"]["expected_reward_vnd"] == _brute_force(missions, hours, tph)


def test_never_exceeds_budget():
    rng = random.Random(7)
    for _ in range(20):
        missions = [_m(f"m{i}", rng.randint(1, 5) * 10000, rng.randint(1, 20)) for i in range(6)]
        hours = rng.choice([1.0, 4.0, 9.0])
        r = solve(_view(missions, hours=hours))
        assert r["solution"]["hours_used"] <= hours + SLOT_MIN / 60 + 1e-9


# ---------- lọc / guardrail ----------

def test_skips_completed_and_too_expensive():
    r = solve(_view([_m("m-done", 50000, 0), _m("m-huge", 90000, 200), _m("m-ok", 30000, 4)],
                    hours=3.0, tph=2.0))
    ids = [c["mission_id"] for c in r["solution"]["chosen_missions"]]
    assert ids == ["m-ok"]
    reasons = {s["mission_id"]: s["reason"] for s in r["solution"]["skipped"]}
    assert "m-done" in reasons and "m-huge" in reasons


def test_reward_only_from_catalog():
    """Mọi số VND phải trace về public_mission (không bịa)."""
    r = solve(_view([_m("m1", 30000, 4), _m("m2", 20000, 4)]))
    for n in r["numbers"]:
        assert n["source"].startswith("public_mission") or n["source"].startswith("historical:")
    total = r["solution"]["expected_reward_vnd"]
    assert total == sum(c["reward_vnd"] for c in r["solution"]["chosen_missions"])


def test_no_feasible_mission():
    r = solve(_view([_m("m-huge", 90000, 500)], hours=1.0))
    assert r["solution"]["chosen_missions"] == []
    assert r["solution"]["feasible"] is False
    assert r["infeasible_reason"]


def test_determinism():
    v = _view([_m("m1", 30000, 4), _m("m2", 30000, 4), _m("m3", 10000, 2)])
    assert solve(v) == solve(v)


# ---------- derivation + chain thật ----------

def test_derivation_filters_and_chains(reg):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tables = generate_realdata(days=8, seed_base=500, out_dir=Path(td))["tables"]
    drv = tables["driver_income_daily"][0]["driver_id"]
    v = derive_mission_select_input_l1r(drv, "2026-07-01T14:00:00+07:00", tables,
                                        hours_budget_remaining=6.0)
    assert reg.validate("mission_select_input", v) == [], v
    assert v["trips_per_hour"] > 0
    # mission đã claim/completed không được đề xuất
    prog = {p["mission_id"]: p["state"] for p in tables["public_user_mission_progress"]
            if p["driver_id"] == drv}
    for m in v["missions"]:
        assert prog.get(m["mission_id"]) not in ("completed", "claimed", "expired")
    r = solve(v)
    assert reg.validate("solver_report", r) == []


def test_mock_missions_are_actionable(reg):
    """Regression: `public_mission.rewards` PHẢI có `target_count`.

    Thiếu → remaining=0 → S6 loại hết ("đã đủ tiến độ") → solver vô nghĩa dù chạy xanh.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tables = generate_realdata(days=8, seed_base=501, out_dir=Path(td))["tables"]
    for m in tables["public_mission"]:
        assert (m["rewards"] or {}).get("target_count", 0) > 0, f"{m['id']} thiếu target_count"
    # driver mới (không có progress row) phải thấy mission còn việc để làm
    v = derive_mission_select_input_l1r("d-CHUA-CO", "2026-07-02T14:00:00+07:00", tables,
                                        hours_budget_remaining=8.0, trips_per_hour=2.0)
    assert any(m["remaining_count"] > 0 for m in v["missions"]), "không mission nào actionable"
    r = solve(v)
    assert r["solution"]["chosen_missions"], "S6 phải chọn được ít nhất 1 nhiệm vụ"


def test_window_filter_excludes_expired():
    """Mission ngoài khung giờ hiệu lực bị loại ở derivation (không vào view)."""
    tables = {"public_mission": [
        {"id": "m-old", "name": "cũ", "mission_type": "trip_count",
         "rewards": {"vnd": 30000, "target_count": 10},
         "start_time": "2026-06-01T00:00:00+07:00", "end_time": "2026-06-30T23:59:00+07:00",
         "source": "MOCK"},
        {"id": "m-now", "name": "hiện hành", "mission_type": "trip_count",
         "rewards": {"vnd": 30000, "target_count": 10},
         "start_time": "2026-07-01T00:00:00+07:00", "end_time": "2026-07-31T23:59:00+07:00",
         "source": "MOCK"}],
        "public_user_mission_progress": [], "driver_income_daily": [], "driver_online_hours_sap_id": []}
    v = derive_mission_select_input_l1r("d-1", "2026-07-15T10:00:00+07:00", tables, 5.0)
    assert [m["mission_id"] for m in v["missions"]] == ["m-now"]

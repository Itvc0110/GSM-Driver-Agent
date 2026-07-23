"""C5 — Solver S4 CapacityAlloc (TDD failing-first).

Platform-level: gán advice nhiều driver vào slot có capacity → chống herding.
swap_window (station capacity) + standby_zone (zone, kèm 5 safety_flags F2-04).
scipy.linear_sum_assignment. Mọi số có source; không chỉ đơn cụ thể (§5).
"""

from pathlib import Path

import pytest

from gsm_core.solvers.capacity_alloc import solve, STANDBY_SAFETY_FLAGS
from gsm_core.features.allocation import derive_allocation_input
from gsm_core.schema_registry import SchemaRegistry

ROOT = Path(__file__).resolve().parent.parent
T_NOW = "2026-07-01T17:00:00+07:00"
BUCKET = "2026-07-01T17:00:00+07:00"


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


def _cand(did, kind="swap_window", target="s-1", soc=50.0):
    return {"driver_id": did, "advice_kind": kind, "target": target, "priority_soc": soc}


def _ai(candidates, station_cap=None, zone_cap=None):
    return {
        "schema_version": "1.0.0", "t_now": T_NOW, "candidates": candidates,
        "station_capacity": station_cap if station_cap is not None else
            [{"station_id": "s-1", "bucket": BUCKET, "capacity": 2}],
        "zone_supply": zone_cap if zone_cap is not None else
            [{"zone": "z-1", "bucket": BUCKET, "capacity": 2}],
        "view_version": "1.0.0", "source": "MOCK",
    }


def test_alloc_respects_capacity():
    # 4 driver muốn swap s-1, capacity 2 → tối đa 2 assigned tại s-1
    ai = _ai([_cand(f"d-{i}", target="s-1") for i in range(4)],
             station_cap=[{"station_id": "s-1", "bucket": BUCKET, "capacity": 2}])
    r = solve(ai)
    sol = r["solution"]
    assigned_s1 = [a for a in sol["allocations"] if a["assigned_target"] == "s-1"
                   and a["assigned_bucket"] == BUCKET]
    assert len(assigned_s1) <= 2, "không được vượt capacity"


def test_excess_candidate_unassigned():
    ai = _ai([_cand(f"d-{i}", target="s-1") for i in range(4)],
             station_cap=[{"station_id": "s-1", "bucket": BUCKET, "capacity": 2}])
    r = solve(ai)
    sol = r["solution"]
    # 4 candidate, cap 2, không có bucket kế trong input → 2 unassigned (chống dồn)
    assert len(sol["unassigned"]) >= 2
    assert all(u["reason"] for u in sol["unassigned"])


def test_low_soc_swap_priority():
    # 2 driver tranh 1 slot; SOC thấp (10) phải thắng SOC cao (80)
    ai = _ai([_cand("d-hi", soc=80.0), _cand("d-lo", soc=10.0)],
             station_cap=[{"station_id": "s-1", "bucket": BUCKET, "capacity": 1}])
    r = solve(ai)
    assigned = [a["driver_id"] for a in r["solution"]["allocations"]]
    assert "d-lo" in assigned and "d-hi" not in assigned


def test_standby_has_safety_flags():
    ai = _ai([_cand("d-1", kind="standby_zone", target="z-1")])
    r = solve(ai)
    st = [a for a in r["solution"]["allocations"] if a["advice_kind"] == "standby_zone"]
    assert st
    assert set(STANDBY_SAFETY_FLAGS) <= set(st[0]["safety_flags"])
    assert len(st[0]["safety_flags"]) == 5


def test_swap_no_safety_flags():
    ai = _ai([_cand("d-1", kind="swap_window", target="s-1")])
    r = solve(ai)
    sw = [a for a in r["solution"]["allocations"] if a["advice_kind"] == "swap_window"]
    assert sw and not sw[0].get("safety_flags")


def test_herding_avoided_count():
    ai = _ai([_cand(f"d-{i}", target="s-1") for i in range(5)],
             station_cap=[{"station_id": "s-1", "bucket": BUCKET, "capacity": 2}])
    r = solve(ai)
    sol = r["solution"]
    n_stag = sum(1 for a in sol["allocations"] if a.get("staggered"))
    assert sol["herding_avoided"] == n_stag + len(sol["unassigned"])
    assert sol["herding_avoided"] >= 3  # 5 - 2 capacity


def test_no_specific_order_advice():
    """§5: không allocation nào chỉ định order/đơn cụ thể — chỉ trạm/zone."""
    ai = _ai([_cand("d-1", kind="standby_zone", target="z-1"),
              _cand("d-2", kind="swap_window", target="s-1")])
    r = solve(ai)
    import json
    blob = json.dumps(r["solution"])
    assert "order_id" not in blob and "\"order\"" not in blob


def test_number_traceability():
    r = solve(_ai([_cand("d-1")]))
    assert r["numbers"]
    for n in r["numbers"]:
        assert n["source"] and any(n["source"].startswith(p) for p in
                                    ("station_registry", "zone_supply", "computed", "observed")), n


def test_solver_report_schema(reg):
    r = solve(_ai([_cand("d-1"), _cand("d-2", kind="standby_zone", target="z-1")]))
    assert reg.validate("solver_report", r) == []
    assert r["solver"] == "capacity_alloc"


def test_determinism():
    ai = _ai([_cand(f"d-{i}", soc=float(i * 10)) for i in range(4)])
    assert solve(ai) == solve(ai)


def test_sensitivity_capacity():
    ai = _ai([_cand(f"d-{i}", target="s-1") for i in range(4)],
             station_cap=[{"station_id": "s-1", "bucket": BUCKET, "capacity": 3}])
    r = solve(ai)
    cs = [s for s in r["sensitivity"] if "capacity" in s.get("param", "")]
    assert cs, "phải có sensitivity capacity"
    assert all("unassigned" in s or "n_unassigned" in s for s in cs)


def test_derive_allocation_schema(reg):
    driver_reports = [
        {"driver_id": "d-1", "advice_kind": "swap_window", "target": "s-1", "priority_soc": 15.0},
        {"driver_id": "d-2", "advice_kind": "standby_zone", "target": "z-1", "priority_soc": None},
    ]
    stations = [{"station_id": "s-1", "throughput_nominal_per_hour": 4.0}]
    zones = [{"zone": "z-1"}]
    ai = derive_allocation_input(T_NOW, driver_reports, stations, zones)
    assert reg.validate("allocation_input", ai) == []
    assert ai["candidates"]
    assert ai["source"] == "MOCK"

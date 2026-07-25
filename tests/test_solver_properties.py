"""Property test XUYÊN SOLVER — bất biến chung cho MỌI solver (audit 2026-07-24).

Thay vì chỉ test từng solver riêng, file này kiểm các bất biến mà **mọi** SolverReport
phải thoả, chạy trên data thật (`generate_realdata`). Bắt được lỗi hồi quy khi thêm
solver mới mà quên guardrail.

Bất biến:
  P1 SolverReport hợp schema (enum `solver` phải được khai báo)
  P2 number_traceability = 1.0 — MỌI số có `source` không rỗng (§5)
  P3 deterministic — gọi 2 lần cho kết quả y hệt
  P4 không NaN/Inf lọt vào `numbers`
  P5 confidence ∈ [0,1]; digest không rỗng
  P6 `caveats` luôn là list (nêu bất định), `infeasible_reason` là str|None
"""

import math
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gsm_core.features.from_l1r import (derive_anomaly_alert_input_l1r,
                                         derive_bonus_gap_input_l1r,
                                         derive_idle_reduction_input_l1r,
                                         derive_mission_select_input_l1r,
                                         derive_penalty_explain_input_l1r,
                                         derive_weekly_khoan_input_l1r)
from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.policy import PolicyBundle
from gsm_core.schema_registry import SchemaRegistry
from gsm_core.solvers import (anomaly_alert, bonus_feasibility, idle_reduction,
                               mission_knapsack, penalty_explain, weekly_khoan)
from test_weekly_khoan import BASE_POLICY, QUOTA

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record({**BASE_POLICY, "weekly_quota": QUOTA})


@pytest.fixture(scope="module")
def ctx(policy):
    with TemporaryDirectory() as td:
        t = generate_realdata(days=8, seed_base=1200, out_dir=Path(td))["tables"]
    row = sorted(t["driver_income_daily"], key=lambda r: -r["total_order"])[0]
    return {"tables": t, "driver": row["driver_id"], "date": row["order_date"]}


def _all_reports(ctx, policy):
    """Chạy mọi solver có thể derive từ data thật → {tên: (report, report_lần_2)}."""
    t, drv, d = ctx["tables"], ctx["driver"], ctx["date"]
    tn = f"{d}T18:00:00+07:00"
    specs = {
        "bonus_feasibility": (bonus_feasibility.solve,
                              (derive_bonus_gap_input_l1r(drv, tn, t, policy, [360, 1320]), policy)),
        "weekly_khoan": (weekly_khoan.solve,
                         (derive_weekly_khoan_input_l1r(drv, tn, t, policy), policy)),
        "mission_knapsack": (mission_knapsack.solve,
                             (derive_mission_select_input_l1r(drv, tn, t, 6.0),)),
        "idle_reduction": (idle_reduction.solve,
                           (derive_idle_reduction_input_l1r(drv, tn, t, session_date=d),)),
        "penalty_explain": (penalty_explain.solve,
                            (derive_penalty_explain_input_l1r(drv, tn, t, policy),)),
        "anomaly_alert": (anomaly_alert.solve, (derive_anomaly_alert_input_l1r(drv, tn, t),)),
    }
    return {name: (fn(*args), fn(*args)) for name, (fn, args) in specs.items()}


@pytest.fixture(scope="module")
def reports(ctx, policy):
    return _all_reports(ctx, policy)


SOLVERS = ["bonus_feasibility", "weekly_khoan", "mission_knapsack",
           "idle_reduction", "penalty_explain", "anomaly_alert"]


@pytest.mark.parametrize("name", SOLVERS)
def test_p1_report_schema_valid(reg, reports, name):
    r, _ = reports[name]
    assert reg.validate("solver_report", r) == [], f"{name}: {reg.validate('solver_report', r)}"
    assert r["solver"] == name


@pytest.mark.parametrize("name", SOLVERS)
def test_p2_number_traceability_is_one(reports, name):
    """§5 HARD invariant: mọi số phải trace được về nguồn."""
    r, _ = reports[name]
    for n in r["numbers"]:
        assert n.get("source"), f"{name}: số {n} thiếu source (traceability != 1.0)"
        assert n.get("unit"), f"{name}: số {n} thiếu unit"


@pytest.mark.parametrize("name", SOLVERS)
def test_p3_deterministic(reports, name):
    r1, r2 = reports[name]
    assert r1 == r2, f"{name} KHÔNG deterministic"


@pytest.mark.parametrize("name", SOLVERS)
def test_p4_no_nan_or_inf(reports, name):
    r, _ = reports[name]
    for n in r["numbers"]:
        v = float(n["value"])
        assert math.isfinite(v), f"{name}: số không hữu hạn {n}"


@pytest.mark.parametrize("name", SOLVERS)
def test_p5_confidence_and_digest(reports, name):
    r, _ = reports[name]
    assert 0.0 <= float(r["confidence"]) <= 1.0
    assert r["problem_digest"].strip(), f"{name}: digest rỗng"


@pytest.mark.parametrize("name", SOLVERS)
def test_p6_caveats_and_infeasible_shape(reports, name):
    r, _ = reports[name]
    assert isinstance(r["caveats"], list)
    assert r.get("infeasible_reason") is None or isinstance(r["infeasible_reason"], str)
    assert isinstance(r.get("sensitivity", []), list)


def test_p7_solver_enum_covers_all_implemented(reg):
    """Mọi solver đã cài PHẢI có trong enum schema (enum đóng — dễ quên khi thêm mới)."""
    import importlib
    enum = set(reg.schema("solver_report")["properties"]["solver"]["enum"])
    implemented = {"bonus_feasibility", "shift_dp", "f3_patterns", "capacity_alloc",
                   "weekly_khoan", "mission_knapsack", "idle_reduction",
                   "penalty_explain", "anomaly_alert"}
    assert implemented <= enum, f"solver thiếu trong enum: {implemented - enum}"
    for name in implemented:  # module phải tồn tại
        importlib.import_module(f"gsm_core.solvers.{name}")

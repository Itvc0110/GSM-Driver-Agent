"""C4 — Solver S3 F3Patterns + L2i inference (TDD failing-first).

Phát hiện pattern chưa tối ưu sau ca từ observable+inferred. Loss = observed +
HEURISTIC (KHÔNG số tuyệt đối, §5). L2i inference tầng riêng, nhãn INFERRED.
"""

import json
from pathlib import Path

import pytest

from gsm_core.policy import PolicyBundle
from gsm_core.features.infer_activity import infer_activities
from gsm_core.features.session_summary import derive_session_summary_input
from gsm_core.solvers.f3_patterns import solve
from gsm_core.schema_registry import SchemaRegistry

ROOT = Path(__file__).resolve().parent.parent

POLICY_REC = {
    "schema_version": "1.0.0", "bundle_id": "b1", "version": "sim-policy-v0",
    "effective_from": "2026-07-01T00:00:00+07:00", "track": "platform", "service": "bike",
    "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300},
    "driver_share": 0.75,
    "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
               "window_hours": list(range(6, 22))},
    "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
    "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85,
                    "forced_accept_below": 0.5},
    "source_url": None, "source": "MOCK",
}
DATE = "2026-07-01"


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(POLICY_REC)


def _t(h, m=0):
    return f"{DATE}T{h:02d}:{m:02d}:00+07:00"


def _trip(oid, h, m=0, dur=15):
    end_m = m + dur
    eh = h + end_m // 60
    em = end_m % 60
    return {"schema_version": "1.0.0", "order_id": oid, "driver_id": "d-1",
            "service_type": "bike", "t_request": _t(h, m), "t_assign": _t(h, m),
            "t_pickup": _t(h, m), "t_complete": _t(eh, em),
            "pickup": {"lat": 21.0, "lon": 105.8, "h3": "x"},
            "drop": {"lat": 21.0, "lon": 105.8, "h3": "y"},
            "dist_km": 3.0, "gross_vnd": 17000, "source": "MOCK"}


def _swap(txid, h, m=0):
    return {"schema_version": "1.0.0", "tx_id": txid, "driver_id": "d-1",
            "station_id": "s-1", "t": _t(h, m), "wait_min": 5.0, "source": "MOCK"}


# ---------- L2i inference ----------

def test_infer_charging_around_swap(reg):
    l1 = {"trip_record": [], "app_event": [], "swap_transaction": [_swap("sw1", 17, 0)]}
    acts = infer_activities("d-1", DATE, l1)
    charging = [a for a in acts if a["label"] == "charging_likely"]
    assert charging, "swap phải sinh charging_likely"
    a = charging[0]
    assert a["source"] == "INFERRED"
    assert a["inference_rule_version"]
    assert reg.validate("inferred_activity", a) == []


def test_infer_rest_vs_idle_from_gap(reg):
    # trip 7:00-7:15, trip 8:00-8:15 → gap 45ph = rest_likely
    # trip 8:00-8:15, trip 8:30-8:45 → gap 15ph = idle_wait
    l1 = {"trip_record": [_trip("o1", 7, 0), _trip("o2", 8, 0), _trip("o3", 8, 30)],
          "app_event": [{"schema_version": "1.0.0", "event_id": "on", "driver_id": "d-1",
                         "t": _t(6), "kind": "go_online", "source": "MOCK"}],
          "swap_transaction": []}
    acts = infer_activities("d-1", DATE, l1)
    labels = [a["label"] for a in acts]
    assert "rest_likely" in labels, "gap 45ph phải là rest_likely"
    assert "idle_wait" in labels, "gap 15ph phải là idle_wait"


# ---------- L3 session_summary ----------

def test_session_summary_schema(reg, policy):
    l1 = {"trip_record": [_trip("o1", 7), _trip("o2", 17)],
          "app_event": [{"schema_version": "1.0.0", "event_id": "on", "driver_id": "d-1",
                         "t": _t(6), "kind": "go_online", "source": "MOCK"}],
          "swap_transaction": [_swap("sw1", 17, 30)],
          "payout_ledger": [
              {"schema_version": "1.0.0", "entry_id": "p1", "driver_id": "d-1",
               "t": _t(7, 20), "kind": "trip_payout", "amount_vnd": 12750,
               "basis": {"trip_id": "o1", "policy_bundle_version": "sim-policy-v0"},
               "gross_vnd": 17000, "source": "MOCK"}]}
    ss = derive_session_summary_input("d-1", DATE, l1, policy)
    assert reg.validate("session_summary_input", ss) == []
    pb = ss["payout_breakdown"]
    assert pb["gross_vnd"] >= pb["driver_payout_vnd"]  # gross ≥ payout
    assert pb["estimated_net_vnd"] is None  # chưa known costs


# ---------- solver patterns ----------

def _ss(points_end=140, acceptance=0.9, completion=0.9, inferred=None,
        gross=100000, payout=75000):
    return {
        "schema_version": "1.0.0", "driver_id": "d-1", "session_date": DATE,
        "trips": [_trip("o1", 7), _trip("o2", 17)],
        "inferred_activities": inferred or [],
        "payout_breakdown": {"gross_vnd": gross, "driver_payout_vnd": payout,
                              "estimated_net_vnd": None, "net_definition_version": None},
        "day_state_end": {"points": points_end, "acceptance_rate": acceptance,
                          "completion_rate": completion},
        "view_version": "1.0.0", "source": "MOCK",
    }


def _infer(label, h, dur=40):
    return {"schema_version": "1.0.0", "driver_id": "d-1", "t_start": _t(h, 0),
            "t_end": _t(h, dur), "label": label, "confidence": 0.7,
            "inference_rule_version": "infer-v1", "source": "INFERRED"}


def test_pattern_charge_peak(policy):
    # charging_likely lúc 17h (peak) → charge_rest_peak pattern
    r = solve(_ss(inferred=[_infer("charging_likely", 17)]), policy)
    pats = [p for p in r["solution"]["patterns"] if p["type"] == "charge_rest_peak"]
    assert pats
    p = pats[0]
    assert "observed" in p and p["observed"]["hour"] == 17
    assert p["severity"] in ("LOW", "MED", "HIGH")
    assert "heuristic_note" in p


def test_pattern_acceptance_cliff(policy):
    r = solve(_ss(acceptance=0.86), policy)
    assert any(p["type"] == "acceptance_cliff" for p in r["solution"]["patterns"])


def test_pattern_bonus_gap(policy):
    # 150 điểm, mốc 160 thiếu 10 → bonus_progress_gap; số 115000 (mốc) có source policy_v
    r = solve(_ss(points_end=150), policy)
    pats = [p for p in r["solution"]["patterns"] if p["type"] == "bonus_progress_gap"]
    assert pats
    # số mốc phải trong numbers với source policy_v
    assert any(n["source"].startswith("policy_v") for n in r["numbers"])


def test_pattern_idle_peak(policy):
    r = solve(_ss(inferred=[_infer("idle_wait", 17, dur=30)]), policy)
    assert any(p["type"] == "idle_peak" for p in r["solution"]["patterns"])


def test_no_absolute_loss_number(policy):
    """§5: KHÔNG số loss tuyệt đối trong numbers[]. Loss chỉ ở heuristic_note có nhãn."""
    r = solve(_ss(inferred=[_infer("charging_likely", 17)]), policy)
    for n in r["numbers"]:
        assert n["unit"] != "vnd_loss", "không được có số loss tuyệt đối"
        # mọi số phải có source hợp lệ (không phải loss bịa)
        assert n["source"], n
    # loss xuất hiện dưới dạng note có nhãn HEURISTIC
    for p in r["solution"]["patterns"]:
        note = p.get("heuristic_note", "")
        if "mất" in note.lower() or "loss" in note.lower():
            assert "HEURISTIC" in p.get("label", "") or p.get("severity"), \
                "loss phải gắn nhãn HEURISTIC/severity, không phải số chắc chắn"


def test_number_traceability(policy):
    r = solve(_ss(points_end=150), policy)
    for n in r["numbers"]:
        assert n["source"] and any(n["source"].startswith(pf) for pf in
                                    ("policy_v", "observed", "session")), n["source"]


def test_top_pattern_single(policy):
    r = solve(_ss(points_end=150, acceptance=0.86,
                  inferred=[_infer("charging_likely", 17)]), policy)
    assert "top_pattern" in r["solution"]
    tp = r["solution"]["top_pattern"]
    assert tp is None or isinstance(tp, dict)  # 1 pattern hoặc None


def test_solver_report_schema(reg, policy):
    r = solve(_ss(), policy)
    assert reg.validate("solver_report", r) == []
    assert r["solver"] == "f3_patterns"


def test_determinism(policy):
    ss = _ss(points_end=150, inferred=[_infer("charging_likely", 17)])
    assert solve(ss, policy) == solve(ss, policy)


def test_no_patterns_clean_session(policy):
    # ca tốt: đủ điểm mốc cao, acceptance cao, không sạc peak → ít/không pattern
    r = solve(_ss(points_end=210, acceptance=0.98, inferred=[]), policy)
    assert r["solution"]["n_patterns"] == 0
    assert r["solution"]["top_pattern"] is None

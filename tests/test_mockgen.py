"""T-038 C1 — mock generator tests (TDD).

Adapter sim→schema phải: map đúng event kinds, ledger tái tính được từ policy,
GPS bám segment, determinism theo seed. Mọi record pass schema registry.
"""

from pathlib import Path

import pytest

from gsm_core.mockgen.adapter_sim import generate_day
from gsm_core.schema_registry import SchemaRegistry

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def reg():
    return SchemaRegistry(ROOT / "schemas")


@pytest.fixture(scope="module")
def day():
    # 1 ngày mock từ sim seed 101, date cố định
    return generate_day(ROOT / "configs" / "pilot_dongda.yaml", seed=101, date="2026-07-01")


def test_all_entities_present(day):
    for name in ("policy_bundle", "driver_profile", "app_event", "trip_record",
                 "swap_transaction", "payout_ledger", "gps_ping"):
        assert name in day and day[name], f"thiếu entity {name}"


def test_every_record_passes_schema(reg, day):
    for entity, records in day.items():
        bad = reg.validate_many(entity, records)
        assert not bad, f"{entity}: {len(bad)} record fail — ví dụ {list(bad.items())[:1]}"


def test_all_records_labeled_mock(day):
    for entity, records in day.items():
        for r in records:
            assert r.get("source") == "MOCK", f"{entity} thiếu nhãn MOCK"


def test_ledger_recomputable_from_policy(day):
    """Cross-entity contract: trip_payout amount = driver_share × gross (policy bundle)."""
    pb = day["policy_bundle"][0]
    share = pb["driver_share"]
    trips = {t["order_id"]: t for t in day["trip_record"]}
    checked = 0
    for e in day["payout_ledger"]:
        if e["kind"] != "trip_payout":
            continue
        t = trips[e["basis"]["trip_id"]]
        assert e["amount_vnd"] == int(round(t["gross_vnd"] * share)), \
            f"ledger {e['entry_id']} không tái tính được"
        assert e["gross_vnd"] == t["gross_vnd"]
        checked += 1
    assert checked > 100, "phải có nhiều trip_payout để kiểm"


def test_app_events_ordered_per_driver(day):
    from collections import defaultdict
    by_driver = defaultdict(list)
    for e in day["app_event"]:
        by_driver[e["driver_id"]].append(e["t"])
    for d, ts in by_driver.items():
        assert ts == sorted(ts), f"driver {d}: event nghịch thời gian"


def test_gps_near_trip_endpoints(day):
    """GPS ping đầu/cuối của trip phải gần pickup/drop (<100m)."""
    from gsm_sim.geo import haversine_km
    from collections import defaultdict
    pings = defaultdict(list)
    for p in day["gps_ping"]:
        pings[p["driver_id"]].append(p)
    checked = 0
    for t in day["trip_record"][:50]:
        dp = [p for p in pings[t["driver_id"]]
              if t["t_pickup"] <= p["t"] <= t["t_complete"]]
        if len(dp) < 2:
            continue
        d0 = haversine_km(dp[0]["location"]["lat"], dp[0]["location"]["lon"],
                          t["pickup"]["lat"], t["pickup"]["lon"])
        d1 = haversine_km(dp[-1]["location"]["lat"], dp[-1]["location"]["lon"],
                          t["drop"]["lat"], t["drop"]["lon"])
        assert d0 < 0.5 and d1 < 0.5, f"GPS lệch endpoint trip {t['order_id']}: {d0:.2f}/{d1:.2f}km"
        checked += 1
    assert checked > 10


def test_determinism_same_seed(day):
    day2 = generate_day(ROOT / "configs" / "pilot_dongda.yaml", seed=101, date="2026-07-01")
    assert len(day["app_event"]) == len(day2["app_event"])
    assert day["payout_ledger"] == day2["payout_ledger"]


def test_no_latent_fields_in_output(day):
    import json
    blob = json.dumps({k: v[:5] for k, v in day.items()})
    for latent in ("meals_taken", "fatigue", "demand_prior", "patience"):
        assert latent not in blob, f"latent '{latent}' leak vào mock data"

"""PI-2b — profile universe phủ MỌI loại tài xế GreenSM (car/bike/premium/…).

Sim CHỈ simulate subset BIKE (driver_id `d-*` khớp sim actors); các loại khác
(bike-rto, car-platform, car-employee, car-premium) sinh KPI RULE-BASED grounded
`research/economics/income-structure.md`. Acceptance theo archetype target + noise
(sửa caveat R2 acceptance≈1.00). Zone enlargement DEFER (Cường) — giữ pilot 1 vùng.
"""

from __future__ import annotations

import random

# archetype → (target_acceptance, trips/ngày range, online giờ range). Grounded personas + realism-benchmarks.
ARCHETYPES = {
    "newbie":    {"acc": 0.74, "trips": (8, 15), "online": (6.0, 8.0), "fulfil": 0.90},
    "part_time": {"acc": 0.82, "trips": (8, 16), "online": (3.0, 5.0), "fulfil": 0.94},
    "full_time": {"acc": 0.91, "trips": (15, 25), "online": (8.0, 10.5), "fulfil": 0.95},
    "veteran":   {"acc": 0.96, "trips": (15, 22), "online": (8.0, 9.5), "fulfil": 0.98},
    "top":       {"acc": 0.96, "trips": (22, 30), "online": (10.0, 11.5), "fulfil": 0.98},
}

# loại GSM → (service_type, driver_type, track, driver_share, fare/cuốc VND range, vehicle_model)
KINDS = {
    "bike_platform": ("bike", "bike-electric", "platform", 0.75, (16000, 24000), "Feliz S"),
    "bike_rto":      ("bike", "bike-electric-rto", "rto", 0.90, (16000, 24000), "Evo200"),
    "car_platform":  ("car", "car", "platform", 0.75, (45000, 70000), "VF5"),
    "car_employee":  ("car", "car", "employee", 0.25, (50000, 80000), "VF e34"),
    "car_premium":   ("car", "car-premium", "platform", 0.75, (90000, 140000), "VF8 Luxury"),
}


def _pick_archetype(rng: random.Random) -> str:
    # phân phối thực: đa số full_time/part_time, ít top/newbie
    return rng.choices(list(ARCHETYPES),
                       weights=[0.15, 0.30, 0.30, 0.15, 0.10])[0]


def _profile(driver_id: str, kind: str, archetype: str, simulated: bool,
             rng: random.Random) -> dict:
    service, dtype, track, share, fare_rng, vehicle = KINDS[kind]
    a = ARCHETYPES[archetype]
    return {
        "driver_id": driver_id, "kind": kind, "service_type": service,
        "driver_type": dtype, "track": track, "tier": "premium" if kind == "car_premium" else "standard",
        "archetype": archetype, "tenure_months": rng.randint(1, 30),
        "driver_share": share, "vehicle_model": vehicle,
        "fare_lo": fare_rng[0], "fare_hi": fare_rng[1],
        "target_acceptance": a["acc"], "target_fulfil": a["fulfil"],
        "trips_lo": a["trips"][0], "trips_hi": a["trips"][1],
        "online_lo": a["online"][0], "online_hi": a["online"][1],
        "simulated": simulated,
    }


def build_profile_universe(sim_bike_ids: list[str], seed: int,
                           n_bike_rto: int = 20, n_car_platform: int = 15,
                           n_car_employee: int = 15, n_car_premium: int = 10) -> dict[str, dict]:
    """Roster đa dạng: bike sim (khớp id sim) + các loại rule-based. Trả {driver_id: profile}."""
    rng = random.Random(seed ^ 0x9E3779B1)
    uni: dict[str, dict] = {}
    # bike-sim (subset simulate) — gán archetype trải đều
    for did in sim_bike_ids:
        uni[did] = _profile(did, "bike_platform", _pick_archetype(rng), True, rng)
    # rule-based (không simulate — sinh KPI trực tiếp)
    for kind, n, prefix in (("bike_rto", n_bike_rto, "r"), ("car_platform", n_car_platform, "cp"),
                            ("car_employee", n_car_employee, "ce"), ("car_premium", n_car_premium, "px")):
        for i in range(n):
            did = f"{prefix}-{i}"
            uni[did] = _profile(did, kind, _pick_archetype(rng), False, rng)
    return uni


def kind_distribution(universe: dict[str, dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for p in universe.values():
        out[p["kind"]] = out.get(p["kind"], 0) + 1
    return out

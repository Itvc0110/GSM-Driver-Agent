"""5 archetype templates → sample N actors có jitter, deterministic theo seed.

Nguồn: planning/PERSONAS.md, advisor-optimization-layer-a.md §1 (σ_arch, ngưỡng mệt,
acceptance), sim-policy-bundle-v0.md §6 (đội xe).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Config
from .entities import Actor, FleetType
from .geo import Grid


@dataclass(frozen=True)
class Archetype:
    name: str
    demand_prior_sigma: float   # sai số kinh nghiệm cá nhân (P4 cao, P3 thấp)
    accept_base: float
    fatigue_threshold_min: float
    shift_len_min: tuple[float, float]  # dải giờ chạy (min,max) theo phút
    shift_start_min: tuple[float, float]
    meal_hour: int
    fleet: str  # "swap" | "charge" | "mixed"


# Từ specs: σ P4 0.6 · P1 0.4 · P2 0.3 · P5 0.15 · P3 0.1; accept P3 .98/P5 .97/P2 .95/P1 .85/P4 .80
ARCHETYPES: dict[str, Archetype] = {
    "P1": Archetype("P1", 0.40, 0.85, 5 * 60, (3 * 60, 5 * 60), (16 * 60, 18 * 60), 12, "charge"),
    "P2": Archetype("P2", 0.30, 0.95, 10 * 60, (9 * 60, 11 * 60), (6 * 60, 8 * 60), 12, "swap"),
    "P3": Archetype("P3", 0.10, 0.98, 12 * 60, (10 * 60, 12 * 60), (5 * 60, 7 * 60), 12, "mixed"),
    "P4": Archetype("P4", 0.60, 0.80, 8 * 60, (8 * 60, 9 * 60), (7 * 60, 10 * 60), 12, "swap"),
    "P5": Archetype("P5", 0.15, 0.97, 9 * 60, (8 * 60, 9 * 60), (6 * 60, 8 * 60), 12, "mixed"),
}


def _pick_fleet(spec: str, ratio_mixed_charge: float, rng) -> FleetType:
    if spec == "swap":
        return FleetType.SWAP
    if spec == "charge":
        return FleetType.CHARGE
    # mixed
    return FleetType.CHARGE if rng.random() < ratio_mixed_charge else FleetType.SWAP


def sample_actors(grid: Grid, cfg: Config, seed: int) -> list[Actor]:
    """Sample N actors theo archetype_mix, jitter deterministic theo seed."""
    rng = np.random.default_rng(seed ^ 0xA11CE)  # stream riêng cho actor sampling
    n = int(cfg.get("actors.n"))
    mix = cfg.get("actors.archetype_mix")
    ratio = float(cfg.get("actors.charge_fleet_ratio_p3p5"))
    start_min = int(cfg.get("time.start_min"))

    # phân bổ số actor theo tỷ trọng (làm tròn ổn định)
    names = sorted(mix.keys())
    counts = {name: int(round(n * float(mix[name]))) for name in names}
    # điều chỉnh cho đủ tổng n
    diff = n - sum(counts.values())
    for name in names:
        if diff == 0:
            break
        counts[name] += 1 if diff > 0 else -1
        diff += -1 if diff > 0 else 1

    core = grid.core_cells
    actors: list[Actor] = []
    aid = 0
    for name in names:
        arc = ARCHETYPES[name]
        for _ in range(counts[name]):
            shift_len = rng.uniform(*arc.shift_len_min)
            shift_start = max(start_min, rng.uniform(*arc.shift_start_min))
            shift_end = min(24 * 60, shift_start + shift_len)
            home = core[rng.integers(len(core))]
            actors.append(
                Actor(
                    actor_id=aid,
                    archetype=name,
                    fleet=_pick_fleet(arc.fleet, ratio, rng),
                    home_cell=home,
                    shift_start_min=float(shift_start),
                    shift_end_min=float(shift_end),
                    demand_prior_sigma=arc.demand_prior_sigma,
                    accept_base=arc.accept_base,
                    fatigue_threshold_min=arc.fatigue_threshold_min,
                    meal_hour=arc.meal_hour,
                    cell=home,
                    soc_pct=float(rng.uniform(70, 100)),
                )
            )
            aid += 1
    return actors

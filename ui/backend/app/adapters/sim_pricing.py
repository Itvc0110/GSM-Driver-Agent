"""Bridge giá cuốc demo Web sang policy MOCK canonical của Simulator.

Module này không sở hữu công thức hay tham số tài chính. Mọi số được đọc từ
`configs/pilot_dongda.yaml` qua `gsm_sim.policy.PolicyBundle`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from gsm_sim.config import Config
from gsm_sim.policy import PolicyBundle

REPO_ROOT = Path(__file__).resolve().parents[4]


@lru_cache(maxsize=1)
def policy() -> PolicyBundle:
    """Policy MOCK dùng chung với Simulator, cache vì config bất biến trong process."""
    cfg = Config.load(REPO_ROOT / "configs" / "pilot_dongda.yaml")
    return PolicyBundle.from_config(cfg)


def quote_distance(distance_km: float) -> dict[str, int | float | str | bool]:
    """Quote gross và payout cuốc cho distance đã được route provider trả về."""
    if distance_km < 0:
        raise ValueError("distance_km must be non-negative")
    active = policy()
    gross = active.gross_fare(distance_km)
    return {
        "fare_vnd": gross,
        "driver_payout_vnd": active.driver_payout_from_gross(gross),
        "driver_share": active.driver_share,
        "fare_policy_version": active.version,
        "data_mode": "synthetic",
        "is_mock": True,
    }

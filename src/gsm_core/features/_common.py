"""Shared helpers cho L3 derivation (bonus_gap, shift_plan)."""

from __future__ import annotations

from gsm_core.policy import PolicyBundle


def hour(iso: str) -> int:
    return int(iso[11:13])


def minute(iso: str) -> int:
    return int(iso[14:16])


def date(iso: str) -> str:
    return iso[:10]


def min_of_day(iso: str) -> int:
    return hour(iso) * 60 + minute(iso)


def points_on_date(trips: list[dict], driver: str, d: str, policy: PolicyBundle) -> int:
    """Σ trip_points các cuốc của driver trong ngày d (điểm suy từ trip + policy)."""
    return sum(policy.trip_points(hour(t["t_request"]))
               for t in trips if t["driver_id"] == driver and date(t["t_request"]) == d)


def online_minutes_on_date(events: list[dict], driver: str, d: str) -> float:
    """Phút online ≈ từ event sớm nhất tới muộn nhất trong ngày (xấp xỉ observable)."""
    ts = sorted(e["t"] for e in events
                if e["driver_id"] == driver and date(e["t"]) == d)
    if len(ts) < 2:
        return 0.0
    return float(min_of_day(ts[-1]) - min_of_day(ts[0]))

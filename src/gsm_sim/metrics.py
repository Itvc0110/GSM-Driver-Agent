"""Tổng hợp event log + actor state → bảng metrics cơ bản (slice v0).

Metrics đầy đủ 3 tầng ở T-020. Ở đây: sanity đối chiếu spec.
"""

from __future__ import annotations

from statistics import median, mean

from .entities import Actor


def summarize(result) -> dict:
    actors: list[Actor] = result.actors
    orders = result.orders
    events = result.events

    n_orders = len(orders)
    n_completed = sum(a.orders_completed for a in actors)
    n_declined = sum(1 for e in events if e.kind == "order_declined")
    n_expired = sum(1 for e in events if e.kind == "order_expired")
    n_stranded = sum(a.stranded_count for a in actors)

    trips = [a.trips_done for a in actors]
    payouts = [a.payout_vnd for a in actors]
    ft = [a for a in actors if (a.shift_end_min - a.shift_start_min) >= 8 * 60]

    swap_waits = [e.detail.get("wait_min", 0.0) for e in events if e.kind == "swap_done"]

    return {
        "seed": result.seed,
        "orders_total": n_orders,
        "orders_completed": n_completed,
        "served_rate": round(n_completed / n_orders, 3) if n_orders else 0.0,
        "unserved_rate": round(1 - n_completed / n_orders, 3) if n_orders else 0.0,
        "orders_declined": n_declined,
        "orders_expired": n_expired,
        "battery_stranded": n_stranded,
        "trips_per_actor_median": median(trips) if trips else 0,
        "trips_per_actor_mean": round(mean(trips), 1) if trips else 0,
        "trips_fulltime_median": median([a.trips_done for a in ft]) if ft else 0,
        "payout_per_actor_median": int(median(payouts)) if payouts else 0,
        "payout_fulltime_median": int(median([a.payout_vnd for a in ft])) if ft else 0,
        "swap_events": len(swap_waits),
        "swap_wait_min_max": round(max(swap_waits), 1) if swap_waits else 0.0,
        "n_actors": len(actors),
        "n_fulltime": len(ft),
    }


def trips_by_hour(result) -> dict[int, int]:
    out: dict[int, int] = {}
    for e in result.events:
        if e.kind == "dropoff":
            h = int(e.t_min // 60) % 24
            out[h] = out.get(h, 0) + 1
    return dict(sorted(out.items()))

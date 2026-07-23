"""Derive L3 `bonus_gap_input` từ L1 records (mock hoặc thật) — input cho solver S1.

Điểm KHÔNG lưu ở ledger (observable là trip + policy) → suy `points_now` từ trip_points.
historical_points_per_hour: median điểm/giờ-online theo khung từ N ngày lịch sử;
thiếu (<3 ngày) → rỗng → solver fallback policy. Nhãn source MOCK.
"""

from __future__ import annotations

from collections import defaultdict

from gsm_core.policy import PolicyBundle


def _hour(iso: str) -> int:
    return int(iso[11:13])


def _date(iso: str) -> str:
    return iso[:10]


def _bucket(policy: PolicyBundle, hour: int) -> str:
    return "peak" if policy.is_peak(hour) else "offpeak"


def _points_on_date(trips: list[dict], driver: str, date: str, policy: PolicyBundle) -> int:
    return sum(policy.trip_points(_hour(t["t_request"]))
               for t in trips if t["driver_id"] == driver and _date(t["t_request"]) == date)


def _online_hours_on_date(events: list[dict], driver: str, date: str) -> float:
    """Giờ online = từ go_online sớm nhất tới event muộn nhất trong ngày (xấp xỉ observable)."""
    ts = sorted(e["t"] for e in events
                if e["driver_id"] == driver and _date(e["t"]) == date)
    if len(ts) < 2:
        return 0.0
    return (_hour(ts[-1]) * 60 + int(ts[-1][14:16]) - _hour(ts[0]) * 60 - int(ts[0][14:16])) / 60.0


def derive_bonus_gap_input(driver_id: str, t_now: str, l1: dict, policy: PolicyBundle,
                           shift_window: list[int], history: list[dict]) -> dict:
    """
    l1: {"trip_record": [...], "app_event": [...]} — data của driver (đã lọc/hoặc full).
    shift_window: [start_min, end_min] declared.
    history: list ngày lịch sử [{"date": "...", "points": int, "online_h": float, ...}]
             — nếu rỗng, tự tính từ l1 các ngày trước today.
    """
    today = _date(t_now)
    trips = l1.get("trip_record", [])
    events = l1.get("app_event", [])

    points_now = _points_on_date(trips, driver_id, today, policy)

    # acceptance/completion từ app_event (observable)
    acc = sum(1 for e in events if e["driver_id"] == driver_id and e["kind"] == "accept")
    dec = sum(1 for e in events if e["driver_id"] == driver_id and e["kind"] == "decline")
    comp = sum(1 for e in events if e["driver_id"] == driver_id and e["kind"] == "complete")
    acceptance = acc / (acc + dec) if (acc + dec) else 1.0
    completion = comp / acc if acc else 1.0

    # hours_budget = phần còn lại của declared window sau t_now
    now_min = _hour(t_now) * 60 + int(t_now[14:16])
    hours_budget = max(0.0, (shift_window[1] - now_min) / 60.0)

    # historical_points_per_hour theo khung — từ history hoặc tự tính từ các ngày < today
    per_bucket: dict[str, list[float]] = defaultdict(list)
    days = {_date(t["t_request"]) for t in trips if t["driver_id"] == driver_id} - {today}
    for d in sorted(days):
        oh = _online_hours_on_date(events, driver_id, d)
        if oh <= 0:
            continue
        # điểm theo bucket trong ngày d
        bp: dict[str, int] = defaultdict(int)
        for t in trips:
            if t["driver_id"] == driver_id and _date(t["t_request"]) == d:
                bp[_bucket(policy, _hour(t["t_request"]))] += policy.trip_points(_hour(t["t_request"]))
        for b, pts in bp.items():
            per_bucket[b].append(pts / oh)  # điểm/giờ ngày đó
    hist_rate: dict[str, float] = {}
    for b, rates in per_bucket.items():
        if len(rates) >= 3:  # đủ data mới tin cá nhân
            hist_rate[b] = round(sorted(rates)[len(rates) // 2], 3)  # median

    next_tiers = [[pt, vnd] for pt, vnd in policy.day_bonus_tiers if pt > points_now]

    return {
        "schema_version": "1.0.0", "driver_id": driver_id, "t_now": t_now,
        "points_now": points_now, "next_tiers": next_tiers,
        "historical_points_per_hour": hist_rate,
        "hours_budget_remaining": round(hours_budget, 3),
        "acceptance_rate": round(acceptance, 4), "completion_rate": round(completion, 4),
        "policy_bundle_version": policy.version, "view_version": "1.0.0", "source": "MOCK",
    }

"""PI-4a — Derive L3 views TỪ BẢNG THẬT (l1r) thay vì recompute từ event sim.

Khác biệt cốt lõi vs `bonus_gap.py`/`session_summary.py` (đường L1 sim): bảng thật
gsm-data-prod đã có **field ĐO ĐƯỢC** — `acceptance_rate`, `fulfillment_rate`,
`online_time`, `total_fee`/`commission` — nên ĐỌC THẲNG, KHÔNG tự đếm lại từ event
(recompute chính là nguồn sai lệch: gốc BUG-PI2b-02 online=0).

Chỉ thứ bảng thật KHÔNG có mới tính: `points_now` (điểm = trips × PolicyBundle),
`historical_points_per_hour`. `soc_pct` = None (13 bảng không có telemetry pin — TBC).

Input `l1r` = dict {entity: [records]} (shape `generate_realdata()["tables"]`) — KHÔNG
đọc file (file I/O thuộc PI-3 DataSource). S4 `allocation_input` KHÔNG remap: bảng thật
thiếu station/battery capacity.
"""

from __future__ import annotations

from collections import defaultdict

from gsm_core.policy import PolicyBundle
from gsm_core.features._common import date as _date, hour as _hour, min_of_day

VIEW_VERSION = "1.0.0"


def _rows(l1r: dict, entity: str) -> list[dict]:
    return l1r.get(entity) or []


def _provenance(*records) -> str:
    """Nhãn source THEO record nguồn (§5) — không hard-code MOCK."""
    for r in records:
        if r and r.get("source") == "REAL":
            return "REAL"
    return "MOCK"


def _stat_row(l1r: dict, driver_id: str, d: str) -> dict | None:
    for r in _rows(l1r, "driver_statistic_daily"):
        if r["driver_id"] == driver_id and r["local_date"] == d:
            return r
    return None


def _online_row(l1r: dict, driver_id: str, d: str) -> dict | None:
    for r in _rows(l1r, "driver_online_hours"):
        if r["driver_id"] == driver_id and r["local_date"] == d:
            return r
    return None


def _income_row(l1r: dict, driver_id: str, d: str) -> dict | None:
    for r in _rows(l1r, "driver_income_daily"):
        if r["driver_id"] == driver_id and r["order_date"] == d:
            return r
    return None


def _driver_trips(l1r: dict, driver_id: str, d: str | None = None) -> list[dict]:
    out = [t for t in _rows(l1r, "trips") if t["driver_id"] == driver_id]
    if d is not None:
        out = [t for t in out if _date(t["complete_time"]) == d]
    return sorted(out, key=lambda t: t["complete_time"])


def _points_from_trips(trips: list[dict], policy: PolicyBundle) -> int:
    """Điểm KHÔNG có trong bảng thật → suy từ giờ KHÁCH ĐẶT (request_time) × policy."""
    return sum(policy.trip_points(_hour(t["request_time"])) for t in trips)


# ---------- S1: bonus_gap_input ----------

def derive_bonus_gap_input_l1r(driver_id: str, t_now: str, l1r: dict, policy: PolicyBundle,
                               shift_window: list[int] | None = None) -> dict:
    """acceptance/completion ĐỌC THẲNG từ `driver_statistic_daily` (đo được)."""
    today = _date(t_now)
    stat = _stat_row(l1r, driver_id, today)
    onl = _online_row(l1r, driver_id, today)
    trips_today = _driver_trips(l1r, driver_id, today)

    points_now = _points_from_trips(trips_today, policy)

    # measured — KHÔNG tự đếm accept/decline.
    # Không có dòng đo cho hôm nay (vd sáng sớm chưa có cuốc) → KHÔNG bịa 1.0 lạc quan:
    # carry-forward giá trị ĐO gần nhất, và hạ nhãn source xuống ESTIMATED (§5 truy vết).
    estimated = False
    if stat:
        acceptance = float(stat["acceptance_rate"])
        completion = float(stat["fulfillment_rate"])
    else:
        prior = sorted((r for r in _rows(l1r, "driver_statistic_daily")
                        if r["driver_id"] == driver_id and r["local_date"] < today),
                       key=lambda r: r["local_date"])
        estimated = True
        if prior:
            acceptance = float(prior[-1]["acceptance_rate"])
            completion = float(prior[-1]["fulfillment_rate"])
        else:  # chưa từng có dữ liệu đo → neutral, nhãn ESTIMATED (không phải "đo được")
            acceptance = completion = 1.0

    # quỹ giờ còn: ưu tiên declared window; nếu không có → suy từ online_time đã dùng
    now_min = min_of_day(t_now)
    if shift_window:
        hours_budget = max(0.0, (shift_window[1] - now_min) / 60.0)
    else:
        # ASSUMPTION: trần ca 12h/ngày (không có declared window trong bảng thật)
        used = float(onl["online_time"]) if onl else 0.0
        hours_budget = max(0.0, min(12.0 - used, (24 * 60 - now_min) / 60.0))

    # historical điểm/giờ theo khung (ngày trước today)
    per_bucket: dict[str, list[float]] = defaultdict(list)
    hist_days = sorted({_date(t["complete_time"]) for t in _driver_trips(l1r, driver_id)} - {today})
    for d in hist_days:
        o = _online_row(l1r, driver_id, d)
        oh = float(o["online_time"]) if o else 0.0
        if oh <= 0:
            continue
        bp: dict[str, int] = defaultdict(int)
        for t in _driver_trips(l1r, driver_id, d):
            h = _hour(t["request_time"])
            bp["peak" if policy.is_peak(h) else "offpeak"] += policy.trip_points(h)
        for b, pts in bp.items():
            per_bucket[b].append(pts / oh)
    hist_rate = {b: round(sorted(v)[len(v) // 2], 3) for b, v in per_bucket.items() if len(v) >= 3}

    return {
        "schema_version": "1.0.0", "driver_id": driver_id, "t_now": t_now,
        "points_now": points_now,
        "next_tiers": [[pt, vnd] for pt, vnd in policy.day_bonus_tiers if pt > points_now],
        "historical_points_per_hour": hist_rate,
        "hours_budget_remaining": round(hours_budget, 3),
        "acceptance_rate": round(acceptance, 4), "completion_rate": round(completion, 4),
        "policy_bundle_version": policy.version, "view_version": VIEW_VERSION,
        # ESTIMATED khi rate là carry-forward/neutral (không có dòng đo hôm nay)
        "source": "ESTIMATED" if estimated else _provenance(stat, onl),
    }


# ---------- S3: session_summary_input ----------

def derive_session_summary_input_l1r(driver_id: str, session_date: str, l1r: dict,
                                     policy: PolicyBundle | None = None) -> dict:
    """payout_breakdown ĐỌC THẲNG: gross=total_fee, driver_payout=commission (đã tách sẵn)."""
    inc = _income_row(l1r, driver_id, session_date)
    stat = _stat_row(l1r, driver_id, session_date)
    onl = _online_row(l1r, driver_id, session_date)
    trips = _driver_trips(l1r, driver_id, session_date)

    gross = int(inc["total_fee"]) if inc else sum(int(t["gross_vnd"]) for t in trips)
    payout = int(inc["commission"]) if inc else 0

    day_state = {}
    if stat:
        day_state = {"acceptance_rate": stat["acceptance_rate"],
                     "fulfillment_rate": stat["fulfillment_rate"],
                     "completed_count": stat["completed_count"],
                     "count_rating_5_star": stat.get("count_rating_5_star"),
                     "online_time": (onl or {}).get("online_time")}
        if policy is not None:
            day_state["points"] = _points_from_trips(trips, policy)

    return {
        "schema_version": "1.0.0", "driver_id": driver_id, "session_date": session_date,
        "trips": [{"trip_id": t["trip_id"], "request_time": t["request_time"],
                   "complete_time": t["complete_time"], "gross_vnd": t["gross_vnd"],
                   "distance_km": t.get("distance_km"), "rush_hour": t.get("rush_hour"),
                   "pickup_h3": t.get("pickup_h3"), "drop_h3": t.get("drop_h3")} for t in trips],
        "inferred_activities": [],  # L2i — điền ở PI-5 (idle từ hex_tracking)
        "payout_breakdown": {
            "gross_vnd": gross, "driver_payout_vnd": payout,
            # estimated_net CHỈ khi đủ known cost + definition version (§5) — chưa có
            "estimated_net_vnd": None, "net_definition_version": None},
        "day_state_end": day_state,
        "view_version": VIEW_VERSION, "source": _provenance(inc, stat),
    }


# ---------- S2: shift_plan_input ----------

def derive_shift_plan_input_l1r(driver_id: str, t_now: str, l1r: dict, policy: PolicyBundle,
                                bucket_min: int = 60, top_cells: int = 3) -> dict:
    """demand_forecast từ MẬT ĐỘ TRIPS THẬT; soc_pct=None (không có telemetry pin).

    Contract L3 (`shift_plan_input`): `buckets_remaining` = **SỐ bucket còn lại** (int);
    `demand_forecast` = [{bucket (ISO start), cell_cluster (H3), expected_orders}].
    `expected_orders` = trung bình cuốc/ngày trong (giờ × cell) tính từ `trips` thật —
    nhãn ESTIMATED-from-REAL (chỉ đếm đơn ĐÃ phục vụ, không có unserved).
    """
    today = _date(t_now)
    now_min = min_of_day(t_now)
    trips_today = _driver_trips(l1r, driver_id, today)
    points_now = _points_from_trips(trips_today, policy)

    all_trips = _rows(l1r, "trips")
    n_days = len({_date(t["request_time"]) for t in all_trips}) or 1
    by_hour_cell: dict[tuple[int, str], int] = defaultdict(int)
    for t in all_trips:
        by_hour_cell[(_hour(t["request_time"]), t.get("pickup_h3") or "unknown")] += 1

    starts = [s for s in range(now_min - now_min % bucket_min, 24 * 60, bucket_min)
              if s + bucket_min > now_min]
    forecast = []
    for s in starts:
        h = s // 60
        cells = sorted(((c, n) for (hh, c), n in by_hour_cell.items() if hh == h),
                       key=lambda x: (-x[1], x[0]))[:top_cells]
        for cell, n in cells:
            forecast.append({"bucket": f"{today}T{s // 60:02d}:{s % 60:02d}:00+07:00",
                             "cell_cluster": cell,
                             "expected_orders": round(n / n_days, 3)})

    stat = _stat_row(l1r, driver_id, today)
    return {
        "schema_version": "1.0.0", "driver_id": driver_id, "t_now": t_now,
        "buckets_remaining": len(starts),
        "soc_pct": None,  # TBC-với-GSM: 13 bảng thật không có telemetry pin
        "points_now": points_now,
        "demand_forecast": forecast,
        "policy_bundle_version": policy.version, "view_version": VIEW_VERSION,
        "source": _provenance(stat),
    }

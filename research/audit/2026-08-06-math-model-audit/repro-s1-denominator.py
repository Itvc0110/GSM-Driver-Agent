# -*- coding: utf-8 -*-
"""Repro MM-06-S1-#1: mau so bucket = gio online TOAN NGAY, solver hieu la gio TRONG bucket.

Kich ban: tai xe online 08:00-18:00 (10h/ngay) x 4 ngay lich su.
Moi ngay: 12 cuoc offpeak (8h-15h) x 5d = 60d ; 6 cuoc peak (16h,17h) x 10d = 60d.
Rate THAT: peak 60d/2h = 30 d/h ; offpeak 60d/8h = 7.5 d/h.
Producer tinh: peak 60/10 = 6.0 ; offpeak 60/10 = 6.0  (chia cho 10h ca ngay).

Query 15:00, points_now=110 (moc ke 160, gap 50), quy 6h (den 21:00).
THAT: 1h offpeak 7.5 + can 42.5 @30/h ~ 1.42h -> ~2.4h <= 6h => FEASIBLE.
"""
import json
from gsm_core.policy import PolicyBundle
from gsm_core.features.bonus_gap import derive_bonus_gap_input
from gsm_core.solvers.bonus_feasibility import solve

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
policy = PolicyBundle.from_record(POLICY_REC)

driver = "d-1"
trips, events = [], []
hist_dates = [f"2026-07-{d:02d}" for d in (1, 2, 3, 4)]
oid = 0
for date in hist_dates:
    def t(h, m=0, _date=date):
        return f"{_date}T{h:02d}:{m:02d}:00+07:00"
    # 12 cuoc offpeak: 8..15h, 90 trips? -> 8 gio x 1.5 cuoc/h = 12 cuoc
    hours = [8, 8, 9, 10, 10, 11, 12, 13, 13, 14, 15, 15] + [16, 16, 16, 17, 17, 17]
    for h in hours:
        oid += 1
        trips.append({"schema_version": "1.0.0", "order_id": f"o{oid}", "driver_id": driver,
                      "service_type": "bike", "t_request": t(h), "t_assign": t(h),
                      "t_pickup": t(h), "t_complete": t(h, 20),
                      "pickup": {"lat": 21.0, "lon": 105.8, "h3": "x"},
                      "drop": {"lat": 21.0, "lon": 105.8, "h3": "y"},
                      "dist_km": 3.0, "gross_vnd": 17000, "source": "MOCK"})
        events.append({"schema_version": "1.0.0", "event_id": f"a{oid}", "driver_id": driver,
                       "t": t(h), "kind": "accept", "source": "MOCK"})
        events.append({"schema_version": "1.0.0", "event_id": f"c{oid}", "driver_id": driver,
                       "t": t(h, 20), "kind": "complete", "source": "MOCK"})
    # online span 08:00 -> 18:00 = 10h (online_minutes_on_date = last - first event)
    events.append({"schema_version": "1.0.0", "event_id": f"on-{date}", "driver_id": driver,
                   "t": t(8), "kind": "go_online", "source": "MOCK"})
    events.append({"schema_version": "1.0.0", "event_id": f"off-{date}", "driver_id": driver,
                   "t": t(18), "kind": "go_offline", "source": "MOCK"})

# hom nay: da co 110 diem (points_now suy tu trips hom nay -> tao 11 cuoc peak 6-7h? de don gian:
# 11 cuoc gio 6,7 (peak 10d) = 110d)
today = "2026-07-05"
for i in range(11):
    h = 6 if i < 6 else 7
    oid += 1
    trips.append({"schema_version": "1.0.0", "order_id": f"o{oid}", "driver_id": driver,
                  "service_type": "bike", "t_request": f"{today}T{h:02d}:05:00+07:00",
                  "t_assign": f"{today}T{h:02d}:05:00+07:00",
                  "t_pickup": f"{today}T{h:02d}:05:00+07:00",
                  "t_complete": f"{today}T{h:02d}:25:00+07:00",
                  "pickup": {"lat": 21.0, "lon": 105.8, "h3": "x"},
                  "drop": {"lat": 21.0, "lon": 105.8, "h3": "y"},
                  "dist_km": 3.0, "gross_vnd": 17000, "source": "MOCK"})

l1 = {"trip_record": trips, "app_event": events}
gi = derive_bonus_gap_input(driver, f"{today}T15:00:00+07:00", l1, policy,
                            shift_window=[360, 1260], history=[])  # ca den 21:00
print("hist_rate producer:", gi["historical_points_per_hour"])
print("points_now:", gi["points_now"], "| budget_h:", gi["hours_budget_remaining"],
      "| acceptance:", gi["acceptance_rate"])

rep = solve(gi, policy)
print("\n--- verdict voi hist tu PRODUCER (mau so = gio ca ngay) ---")
print("feasible:", rep["solution"]["feasible"], "| hours_needed:", rep["solution"]["hours_needed"])
print("infeasible_reason:", rep["infeasible_reason"])

# doi chieu: rate THAT theo gio-trong-bucket
gi_true = dict(gi)
gi_true["historical_points_per_hour"] = {"peak": 30.0, "offpeak": 7.5}
rep2 = solve(gi_true, policy)
print("\n--- verdict voi rate THAT (diem / gio TRONG bucket) ---")
print("feasible:", rep2["solution"]["feasible"], "| hours_needed:", rep2["solution"]["hours_needed"])
print("infeasible_reason:", rep2["infeasible_reason"])

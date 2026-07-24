"""PI-2 — gen MOCK 13 bảng l1r (shape data thật) bằng sim→AGGREGATE (P3 grandplan).

Tái dùng `adapter_sim.generate_day` (event nền) → aggregate ra KPI daily/weekly + reshape
trips/hex + rule-based mission/penalty/fraud. Aggregate LUÔN nhất quán event nền (verify R3).
Mọi record source=MOCK/INFERRED. Deterministic theo seed.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import date as _date, datetime, timedelta
from pathlib import Path

import polars as pl

from gsm_core.mockgen.adapter_sim import generate_day
from gsm_core.schema_registry import SchemaRegistry, L1R_ENTITIES

ROOT = Path(__file__).resolve().parents[3]
RUSH_HOURS = {6, 7, 8, 16, 17, 18}


def _hour(iso: str) -> int:
    return datetime.fromisoformat(iso).hour


def _date_of(iso: str) -> str:
    return datetime.fromisoformat(iso).date().isoformat()


def _week_key(d: str) -> tuple[str, str, str]:
    dt = _date.fromisoformat(d)
    iso = dt.isocalendar()
    monday = dt - timedelta(days=dt.weekday())
    return f"{iso.year}-W{iso.week:02d}", monday.isoformat(), (monday + timedelta(days=6)).isoformat()


def _num(rng: random.Random, mu: float, sd: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, rng.gauss(mu, sd)))


def aggregate_days(days: list[dict], share: float, profiles: dict, seed: int) -> dict[str, list[dict]]:
    """days = list of generate_day output. Trả {l1r_entity: records}."""
    rng = random.Random(seed ^ 0x5EED)
    trips_all: list[dict] = []
    events_all: list[dict] = []
    pings_all: list[dict] = []
    for day in days:
        trips_all += day.get("trip_record", [])
        events_all += day.get("app_event", [])
        pings_all += day.get("gps_ping", [])

    # index per (driver, date)
    dd = lambda: defaultdict(list)  # noqa: E731
    trips_by = defaultdict(list)
    for t in trips_all:
        trips_by[(t["driver_id"], _date_of(t["t_complete"]))].append(t)
    ev_by = defaultdict(lambda: defaultdict(int))
    online_by = defaultdict(list)
    for e in events_all:
        d = _date_of(e["t"])
        ev_by[(e["driver_id"], d)][e["kind"]] += 1
        if e["kind"] in ("go_online", "go_offline"):
            online_by[(e["driver_id"], d)].append((e["t"], e["kind"]))

    out: dict[str, list[dict]] = {e: [] for e in L1R_ENTITIES}
    keys = sorted(set(trips_by) | set(ev_by) | set(online_by))

    for (drv, d) in keys:
        trips = sorted(trips_by[(drv, d)], key=lambda x: x["t_complete"])
        ev = ev_by[(drv, d)]
        accepted = ev.get("accept", len(trips))
        completed = len(trips)
        declined = ev.get("decline", 0)
        accepted = max(accepted, completed)
        req_accept = accepted + declined
        cancelled = max(0, accepted - completed)
        acc_rate = round(accepted / req_accept, 4) if req_accept else 1.0
        ful_rate = round(completed / accepted, 4) if accepted else 1.0
        can_rate = round(cancelled / req_accept, 4) if req_accept else 0.0
        n_rated = completed
        n_5star = int(round(n_rated * _num(rng, 0.78, 0.08, 0.4, 1.0)))
        avg_star = _num(rng, 4.7, 0.15, 3.5, 5.0)

        # --- driver_statistic_daily ---
        out["driver_statistic_daily"].append({
            "schema_version": "1.0.0", "source": "MOCK", "local_date": d, "driver_id": drv,
            "completed_count": completed, "accepted_count": accepted, "cancelled_count": cancelled,
            "total_request_calculate_complete": accepted,
            "total_request_calculate_cancel": cancelled + declined,
            "total_request_calculate_accept": req_accept,
            "count_cancel_not_relate_driver": max(0, cancelled - int(cancelled * 0.5)),
            "total_rating": round(avg_star * n_rated, 2), "total_order_rating": n_rated,
            "count_rating_5_star": min(n_5star, n_rated),
            "acceptance_rate": acc_rate, "fulfillment_rate": ful_rate, "cancellation_rate": can_rate})

        # --- online hours ---
        spans = sorted(online_by[(drv, d)], key=lambda x: x[0])
        online_h = 0.0
        stack = None
        for ts, kind in spans:
            if kind == "go_online":
                stack = ts
            elif kind == "go_offline" and stack:
                online_h += (datetime.fromisoformat(ts) - datetime.fromisoformat(stack)).total_seconds() / 3600
                stack = None
        prof = profiles.get(drv, {})
        out["driver_online_hours"].append({
            "schema_version": "1.0.0", "source": "MOCK", "local_date": d, "schedule_date": d,
            "driver_id": drv, "full_name": f"MOCK Driver {drv}", "sap_profile_id": f"SAP-{drv}",
            "hub_id": "hub-dongda", "depot_id": "depot-01", "phone_number": "+8490MOCK000",
            "driver_type": prof.get("vehicle_type", "bike-electric"),
            "online_time": round(online_h, 2)})

        # --- income + rush split ---
        gross = sum(t["gross_vnd"] for t in trips)
        commission = int(round(gross * share))
        rnrd = gross - commission
        rush_trips = [t for t in trips if _hour(t["t_complete"]) in RUSH_HOURS]
        g_rush = sum(t["gross_vnd"] for t in rush_trips)
        c_rush = int(round(g_rush * share))
        g_norm, c_norm = gross - g_rush, commission - c_rush
        out["driver_orders_rush_hours"].append({
            "schema_version": "1.0.0", "source": "MOCK", "driver_id": drv, "local_date": d,
            "total_order": completed, "commission": commission, "total_fee": gross,
            "revenue_not_relate_driver": rnrd,
            "total_order_normal_hour": completed - len(rush_trips), "commission_normal_hour": c_norm,
            "total_fee_normal_hour": g_norm, "revenue_not_relate_driver_normal_hour": g_norm - c_norm,
            "total_order_rush_hour": len(rush_trips), "commission_rush_hour": c_rush,
            "total_fee_rush_hour": g_rush, "revenue_not_relate_driver_rush_hour": g_rush - c_rush})
        out["driver_income_daily"].append({
            "schema_version": "1.0.0", "source": "MOCK", "driver_id": drv, "order_date": d,
            "commission": commission, "total_order": completed, "total_fee": gross,
            "revenue_not_relate_driver": rnrd,
            "avg_daily_revenue": round(gross / completed, 2) if completed else 0.0,
            "total_core_order": completed})

        # --- stoppoints (proxy: mỗi trip 1 điểm drop) ---
        out["driver_bike_stoppoints"].append({
            "schema_version": "1.0.0", "source": "MOCK", "driver_id": drv, "local_date": d,
            "total_stoppoints": completed, "total_stoppoints_rush_hour": len(rush_trips)})

        # --- trips (reshape dispatch) ---
        for t in trips:
            out["trips"].append({
                "schema_version": "1.0.0", "source": "MOCK", "trip_id": t["order_id"],
                "driver_id": drv, "customer_id": f"cust-{t['order_id']}", "service_type": "bike",
                "status": "completed", "request_time": t["t_request"], "assign_time": t["t_assign"],
                "pickup_time": t["t_pickup"], "complete_time": t["t_complete"],
                "pickup_h3": t["pickup"]["h3"], "drop_h3": t["drop"]["h3"],
                "distance_km": t["dist_km"],
                "duration_seconds": int((datetime.fromisoformat(t["t_complete"])
                                         - datetime.fromisoformat(t["t_pickup"])).total_seconds()),
                "gross_vnd": t["gross_vnd"], "commission_vnd": int(round(t["gross_vnd"] * share)),
                "rush_hour": _hour(t["t_complete"]) in RUSH_HOURS, "travel_mode": "bike",
                "created_at": t["t_request"], "datastream_metadata": None})

    # --- hex_tracking từ gps dwell segments ---
    pings_by = defaultdict(list)
    for p in pings_all:
        pings_by[p["driver_id"]].append(p)
    hx = 0
    for drv, ps in sorted(pings_by.items()):
        ps.sort(key=lambda x: x["t"])
        seg_hex, seg_start, prev_hex = None, None, None
        for p in ps:
            h = p["location"]["h3"]
            if h != seg_hex:
                if seg_hex is not None:
                    dur = int((datetime.fromisoformat(prev_t) - datetime.fromisoformat(seg_start)).total_seconds())
                    out["driver_hex_tracking"].append({
                        "schema_version": "1.0.0", "source": "MOCK", "id": f"hx-{seed}-{hx}",
                        "driver_id": drv, "campaign_id": None, "log_id": None,
                        "init_hex": prev_hex, "current_hex": seg_hex, "last_hex": prev_hex,
                        "target_hex": None, "last_seen_at": prev_t, "entered_current_hex_at": seg_start,
                        "stay_duration_seconds": dur, "reached_target": None, "reached_target_at": None,
                        "hex_history": None, "created_at": seg_start, "updated_at": prev_t,
                        "schedule_job_id": None, "datastream_metadata": None,
                        "tracking_status": "idle" if dur > 300 else "moving"})
                    hx += 1
                seg_hex, seg_start, prev_hex = h, p["t"], seg_hex
            prev_t = p["t"]

    return out


def build_weekly_and_missions(daily: dict, profiles: dict, seed: int) -> None:
    """kpi_weekly_calculator + mission_catalog/earn/progress + penalization + fraud (rule-based)."""
    rng = random.Random(seed ^ 0xB0B)
    # weekly rollup từ income_daily
    by_dw = defaultdict(list)
    for r in daily["driver_income_daily"]:
        wk, ws, we = _week_key(r["order_date"])
        by_dw[(r["driver_id"], wk, ws, we)].append(r)
    kid = 0
    for (drv, wk, ws, we), rows in sorted(by_dw.items()):
        rev = sum(x["total_fee"] for x in rows)
        status = "achieved" if rev >= 2_000_000 else ("at_risk" if len(rows) < 5 else "active")
        daily["kpi_weekly_calculator"].append({
            "schema_version": "1.0.0", "source": "MOCK", "id": f"kpi-{seed}-{kid}", "driver_id": drv,
            "driver_name": f"MOCK Driver {drv}", "sap_id": f"SAP-{drv}", "status": status,
            "week_key": wk, "week_start": ws, "week_end": we,
            "kpi_month": _date.fromisoformat(ws).month, "kpi_year": _date.fromisoformat(ws).year,
            "email": None, "tel": None, "engname": None, "depot_code": "DPT01", "depot_name": "Dong Da",
            "vehicle_vin_number": f"VIN{drv}", "vehicle_license_plate": f"29-MOCK{drv}",
            "vehicle_model": "Feliz S", "country": "VN", "type": profiles.get(drv, {}).get("track", "platform"),
            "last_updated_date": f"{we}T23:59:00+07:00"})
        kid += 1

    # mission catalog (rule-based, grounded mini-task thật)
    missions = [
        {"id": "m-trip20", "mission_type": "trip_count", "name": "20 chuyến/ngày",
         "target_count": 20, "reward_vnd": 30000, "rush": False},
        {"id": "m-rush", "mission_type": "rush_hour", "name": "2 chuyến khung vàng",
         "target_count": 2, "reward_vnd": 30000, "rush": True},
        {"id": "m-week250", "mission_type": "trip_count", "name": "250 chuyến/tuần",
         "target_count": 250, "reward_vnd": 1000000, "rush": False},
    ]
    for m in missions:
        daily["mission_catalog"].append({
            "schema_version": "1.0.0", "source": "MOCK", "id": m["id"], "created_at": "2026-07-01T00:00:00+07:00",
            "updated_at": None, "deleted_at": None, "created_by": "gsm", "updated_by": None,
            "mission_type": m["mission_type"], "parent_id": None, "name": m["name"], "state": "active",
            "audience": "bike_platform", "description": m["name"],
            "start_time": "2026-07-01T00:00:00+07:00", "end_time": "2026-12-31T23:59:00+07:00",
            "point_id": None, "rewards": {"vnd": m["reward_vnd"], "target_count": m["target_count"]},
            "mission_claim": None, "mission_code": m["id"], "time_claim_reward": None, "rule_code": None,
            "meta_data": None, "contract_type": None, "qualify_execute_code": None, "status": "active",
            "datastream_metadata": None, "business_code": None, "show_only": False, "is_ddi_mission": False})

    # earn_history + progress: gán mission m-trip20 theo ngày đạt ≥20 chuyến
    eid = pid = 0
    trips_by_dd = defaultdict(int)
    for r in daily["driver_income_daily"]:
        trips_by_dd[(r["driver_id"], r["order_date"])] = r["total_order"]
    prog = defaultdict(int)
    for (drv, d), n in sorted(trips_by_dd.items()):
        if n >= 20:
            daily["mission_earn_history"].append({
                "schema_version": "1.0.0", "source": "MOCK", "id": f"eh-{seed}-{eid}", "mission_id": "m-trip20",
                "order_id": None, "order_status": "completed", "driver_id": drv, "customer_id": None,
                "service_type": "bike", "order_time": f"{d}T20:00:00+07:00", "complete_time": f"{d}T20:00:00+07:00",
                "travel_mode": "bike", "sap_contract_type": "platform", "type": "mission",
                "count_order": n, "count_stoppoint": n, "earn": 30000, "description": "20 chuyến/ngày",
                "datastream_metadata": None, "reward_level": "1"})
            eid += 1
        prog[drv] += n
    for drv, total in sorted(prog.items()):
        daily["user_mission_progress"].append({
            "schema_version": "1.0.0", "source": "MOCK", "id": f"ump-{seed}-{pid}", "driver_id": drv,
            "mission_id": "m-week250", "progress_count": min(total, 250), "target_count": 250,
            "progress_value_vnd": 0, "target_value_vnd": 1000000,
            "state": "completed" if total >= 250 else "in_progress",
            "started_at": "2026-07-01T00:00:00+07:00", "updated_at": None, "claimed_at": None,
            "datastream_metadata": None})
        pid += 1

    # penalization: clawback khi tuần at_risk (rev thấp) — hiếm
    for k in daily["kpi_weekly_calculator"]:
        if k["status"] == "at_risk" and rng.random() < 0.5:
            daily["driver_penalization"].append({
                "schema_version": "1.0.0", "source": "MOCK", "penalization_id": f"pen-{seed}-{k['id']}",
                "driver_id": k["driver_id"], "local_date": k["week_end"], "week_key": k["week_key"],
                "penalty_type": "clawback_khoan", "amount_vnd": 40000,
                "reason": "không đạt khoán tuần", "related_metric": "weekly_revenue",
                "ata_code": None, "status": "applied", "created_at": f"{k['week_end']}T23:00:00+07:00"})

    # fraud: rất hiếm (~1% driver-day) — INFERRED
    fid = 0
    for r in daily["driver_statistic_daily"]:
        if rng.random() < 0.01:
            daily["fraud_flag"].append({
                "schema_version": "1.0.0", "source": "INFERRED", "fraud_id": f"f-{seed}-{fid}",
                "driver_id": r["driver_id"], "detected_at": f"{r['local_date']}T18:00:00+07:00",
                "fraud_type": "route_deviation", "severity": "low", "confidence": 0.4,
                "evidence_ref": None, "status": "open", "created_at": f"{r['local_date']}T18:00:00+07:00",
                "datastream_metadata": None})
            fid += 1


def generate_realdata(days: int, seed_base: int, out_dir: Path,
                      config_path: Path | None = None, start_date: str = "2026-07-01") -> dict:
    cfg_path = config_path or (ROOT / "configs" / "pilot_dongda.yaml")
    out_dir.mkdir(parents=True, exist_ok=True)
    day_outputs, profiles, share = [], {}, 0.75
    d0 = _date.fromisoformat(start_date)
    for i in range(days):
        day = generate_day(cfg_path, seed=seed_base + i, date=(d0 + timedelta(days=i)).isoformat())
        day_outputs.append(day)
        if i == 0:
            share = float(day["policy_bundle"][0]["driver_share"])
            profiles = {p["driver_id"]: p for p in day["driver_profile"]}
    tables = aggregate_days(day_outputs, share, profiles, seed_base)
    build_weekly_and_missions(tables, profiles, seed_base)

    counts = {}
    for entity, records in tables.items():
        flat = [{k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
                 for k, v in r.items()} for r in records]
        pl.DataFrame(flat).write_parquet(out_dir / f"{entity}.parquet")
        counts[entity] = len(records)
    manifest = {"label": "MOCK", "generator": "gsm_core.mockgen.realdata v1", "days": days,
                "seed_base": seed_base, "start_date": start_date, "record_counts": counts,
                "schema_versions": {e: "1.0.0" for e in tables}}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    return {"tables": tables, "manifest": manifest}

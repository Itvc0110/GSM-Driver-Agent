"""PI-2/PI-2b — gen MOCK 13 bảng l1r (shape data thật) profile-driven.

BIKE simulate qua `adapter_sim.generate_day` (event nền); car/premium/rto sinh trips
RULE-BASED (không sim). Aggregate ĐỒNG NHẤT → KPI daily/weekly. **Acceptance theo
archetype target + noise** (sửa caveat R2 acceptance≈1.00, thêm randomness). Per-driver
`driver_share`. Mọi record MOCK/INFERRED, deterministic seed. Zone enlargement DEFER.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import date as _date, datetime, timedelta
from pathlib import Path

import polars as pl

from gsm_core.mockgen.adapter_sim import generate_day
from gsm_core.mockgen.profiles import build_profile_universe, kind_distribution
from gsm_core.schema_registry import L1R_ENTITIES

ROOT = Path(__file__).resolve().parents[3]
RUSH_HOURS = {6, 7, 8, 16, 17, 18}
# demand shape theo giờ 6..22 (2 đỉnh sáng/chiều) — trọng số cho rule-based trips
_HOUR_W = {6: 3, 7: 5, 8: 4, 9: 2, 10: 2, 11: 3, 12: 3, 13: 1, 14: 1, 15: 2,
           16: 4, 17: 5, 18: 5, 19: 3, 20: 3, 21: 2, 22: 1}


def write_table_parquet(records: list[dict], path: Path) -> int:
    """Ghi parquet AN TOÀN KIỂU (BUG-PI2b-05).

    `pl.DataFrame(...)` mặc định chỉ suy kiểu từ 100 dòng đầu → cột THƯA
    (`campaign_id`/`target_hex` chỉ ~5% có giá trị) bị suy thành Null rồi CRASH khi
    gặp giá trị str ở dòng sau ("could not append value ... to the builder").
    Lỗi phụ thuộc seed → phải quét TOÀN BỘ (`infer_schema_length=None`).
    """
    flat = [{k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
             for k, v in r.items()} for r in records]
    pl.DataFrame(flat, infer_schema_length=None).write_parquet(path)
    return len(records)


def _hour(iso: str) -> int:
    return datetime.fromisoformat(iso).hour


def _date_of(iso: str) -> str:
    return datetime.fromisoformat(iso).date().isoformat()


def _week_key(d: str):
    dt = _date.fromisoformat(d)
    iso = dt.isocalendar()
    monday = dt - timedelta(days=dt.weekday())
    return f"{iso.year}-W{iso.week:02d}", monday.isoformat(), (monday + timedelta(days=6)).isoformat()


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def rule_based_trips(profile: dict, date_str: str, rng: random.Random) -> list[dict]:
    """Trips cho driver KHÔNG simulate (car/premium/rto) — shape ~ trip_record sim.

    BUG-PI2b-03 fix: complete_time PHẢI nằm trong ngày (không tràn nửa đêm) — nếu tràn
    thì dịch cả cuốc sớm lại, giữ bất biến R3 (statistic.completed == trips theo ngày).
    """
    if rng.random() < 0.12:  # ~12% ngày nghỉ (randomness)
        return []
    n = rng.randint(profile["trips_lo"], profile["trips_hi"])
    hours = list(_HOUR_W)
    weights = [_HOUR_W[h] for h in hours]
    day_end = datetime.fromisoformat(f"{date_str}T23:59:00+07:00")
    trips = []
    for i in range(n):
        h = rng.choices(hours, weights=weights)[0]
        mi = rng.randint(0, 59)
        base = datetime.fromisoformat(f"{date_str}T{h:02d}:{mi:02d}:00+07:00")
        dist = round(_clamp(rng.gauss(4.5, 2.2), 0.8, 18.0), 2)
        dur_s = int(dist / max(12, rng.gauss(22, 4)) * 3600) + rng.randint(120, 420)
        fare = rng.randint(profile["fare_lo"], profile["fare_hi"])
        # giữ trong ngày: nếu kết thúc quá 23:59 → dịch base sớm lại đúng phần tràn
        overflow = (base + timedelta(seconds=240 + dur_s)) - day_end
        if overflow.total_seconds() > 0:
            base -= timedelta(seconds=int(overflow.total_seconds()) + 60)
        t_req = base.isoformat()
        t_assign = (base + timedelta(seconds=60)).isoformat()
        t_pickup = (base + timedelta(seconds=240)).isoformat()
        t_complete = (base + timedelta(seconds=240 + dur_s)).isoformat()
        trips.append({
            "order_id": f"{profile['driver_id']}-{date_str}-{i}", "driver_id": profile["driver_id"],
            "t_request": t_req, "t_assign": t_assign, "t_pickup": t_pickup, "t_complete": t_complete,
            "pickup": {"h3": f"8amock{rng.randint(0, 60):02d}"},
            "drop": {"h3": f"8amock{rng.randint(0, 60):02d}"},
            "dist_km": dist, "gross_vnd": fare})
    return sorted(trips, key=lambda x: x["t_complete"])


def _trip_hours(trips: list) -> float:
    """Tổng giờ THỰC phục vụ cuốc (request→complete) — sàn cho online_time."""
    tot = 0.0
    for t in trips:
        tot += (datetime.fromisoformat(t["t_complete"])
                - datetime.fromisoformat(t["t_request"])).total_seconds() / 3600
    return tot


def _emit_day(out: dict, drv: str, d: str, trips: list, prof: dict, online_h: float,
              rng: random.Random) -> None:
    """Aggregate 1 driver-day → mọi bảng KPI daily + trips. Acceptance từ profile target.

    BUG-PI2b-02 fix: online_time PHẢI ≥ giờ phục vụ cuốc (không thể có cuốc khi offline).
    Sàn = trip_hours/0.55 (utilization ≤55% — realism-benchmarks FT 45-55%).
    """
    share = prof["driver_share"]
    if trips:
        online_h = max(online_h, _trip_hours(trips) / 0.55)
    completed = len(trips)
    ful = _clamp(rng.gauss(prof["target_fulfil"], 0.02), 0.6, 1.0)
    accepted = max(completed, round(completed / ful)) if completed else 0
    acc = _clamp(rng.gauss(prof["target_acceptance"], 0.04), 0.5, 1.0)
    req_accept = max(accepted, round(accepted / acc)) if accepted else 0
    declined = req_accept - accepted
    cancelled = accepted - completed
    acc_rate = round(accepted / req_accept, 4) if req_accept else 1.0
    ful_rate = round(completed / accepted, 4) if accepted else 1.0
    can_rate = round(cancelled / req_accept, 4) if req_accept else 0.0
    n_5 = int(round(completed * _clamp(rng.gauss(0.78, 0.08), 0.4, 1.0)))
    avg_star = _clamp(rng.gauss(4.7, 0.15), 3.5, 5.0)

    out["driver_statistic_daily"].append({
        "schema_version": "1.0.0", "source": "MOCK", "local_date": d, "driver_id": drv,
        "completed_count": completed, "accepted_count": accepted, "cancelled_count": cancelled,
        "total_request_calculate_complete": accepted, "total_request_calculate_cancel": cancelled + declined,
        "total_request_calculate_accept": req_accept,
        "count_cancel_not_relate_driver": rng.randint(0, cancelled) if cancelled else 0,
        "total_rating": round(avg_star * completed, 2), "total_order_rating": completed,
        "count_rating_5_star": min(n_5, completed),
        "acceptance_rate": acc_rate, "fulfillment_rate": ful_rate, "cancellation_rate": can_rate})

    out["driver_online_hours_sap_id"].append({
        "schema_version": "1.0.0", "source": "MOCK", "local_date": d, "schedule_date": d,
        "driver_id": drv, "full_name": f"MOCK Driver {drv}", "sap_profile_id": f"SAP-{drv}",
        "hub_id": "hub-dongda", "depot_id": "depot-01", "phone_number": "+8490MOCK000",
        "driver_type": prof["driver_type"], "online_time": round(online_h, 2)})

    gross = sum(t["gross_vnd"] for t in trips)
    commission = int(round(gross * share))
    rush = [t for t in trips if _hour(t["t_complete"]) in RUSH_HOURS]
    g_rush = sum(t["gross_vnd"] for t in rush)
    c_rush = int(round(g_rush * share))
    g_norm, c_norm = gross - g_rush, commission - c_rush
    out["driver_orders_rush_hours"].append({
        "schema_version": "1.0.0", "source": "MOCK", "driver_id": drv, "local_date": d,
        "total_order": completed, "commission": commission, "total_fee": gross,
        "revenue_not_relate_driver": gross - commission,
        "total_order_normal_hour": completed - len(rush), "commission_normal_hour": c_norm,
        "total_fee_normal_hour": g_norm, "revenue_not_relate_driver_normal_hour": g_norm - c_norm,
        "total_order_rush_hour": len(rush), "commission_rush_hour": c_rush,
        "total_fee_rush_hour": g_rush, "revenue_not_relate_driver_rush_hour": g_rush - c_rush})
    # BUG-PI2b-04 fix: core_order ⊊ total (85-95% — catalog), KHÔNG degenerate
    core = int(round(completed * _clamp(rng.gauss(0.90, 0.04), 0.80, 1.0)))
    out["driver_income_daily"].append({
        "schema_version": "1.0.0", "source": "MOCK", "driver_id": drv, "order_date": d,
        "commission": commission, "total_order": completed, "total_fee": gross,
        "revenue_not_relate_driver": gross - commission,
        "avg_daily_revenue": round(gross / completed, 2) if completed else 0.0,
        "total_core_order": min(core, completed)})
    # BUG-PI2b-04 fix: stoppoints = điểm trả khách + điểm dừng CHỜ (idle) → ≠ số cuốc
    idle_stops = rng.randint(0, max(1, completed // 2)) if completed else 0
    idle_rush = rng.randint(0, idle_stops) if idle_stops else 0
    out["driver_bike_stoppoints"].append({
        "schema_version": "1.0.0", "source": "MOCK", "driver_id": drv, "local_date": d,
        "total_stoppoints": completed + idle_stops,
        "total_stoppoints_rush_hour": len(rush) + idle_rush})

    for t in trips:
        out["trips"].append({
            "schema_version": "1.0.0", "source": "MOCK", "trip_id": t["order_id"], "driver_id": drv,
            "customer_id": f"cust-{t['order_id']}", "service_type": prof["service_type"],
            "status": "completed", "request_time": t["t_request"], "assign_time": t["t_assign"],
            "pickup_time": t["t_pickup"], "complete_time": t["t_complete"],
            "pickup_h3": t["pickup"]["h3"], "drop_h3": t["drop"]["h3"], "distance_km": t["dist_km"],
            "duration_seconds": int((datetime.fromisoformat(t["t_complete"])
                                     - datetime.fromisoformat(t["t_pickup"])).total_seconds()),
            "gross_vnd": t["gross_vnd"], "commission_vnd": int(round(t["gross_vnd"] * share)),
            "rush_hour": _hour(t["t_complete"]) in RUSH_HOURS, "travel_mode": prof["service_type"],
            "created_at": t["t_request"], "datastream_metadata": None})


def build_tables(day_outputs: list[dict], universe: dict, seed: int) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {e: [] for e in L1R_ENTITIES}
    rng = random.Random(seed ^ 0x5EED)

    # --- BIKE simulated: gom trips + online span + pings từ sim ---
    trips_by = defaultdict(list)
    online_by = defaultdict(list)
    pings_all = []
    dates = set()
    for day in day_outputs:
        for t in day.get("trip_record", []):
            trips_by[(t["driver_id"], _date_of(t["t_complete"]))].append(t)
        for e in day.get("app_event", []):
            if e["kind"] in ("go_online", "go_offline"):
                online_by[(e["driver_id"], _date_of(e["t"]))].append((e["t"], e["kind"]))
        pings_all += day.get("gps_ping", [])
    for day in day_outputs:  # tập ngày
        for t in day.get("trip_record", []):
            dates.add(_date_of(t["t_complete"]))
    dates = sorted(dates)

    def online_hours(drv, d):
        spans = sorted(online_by[(drv, d)])
        h, stack = 0.0, None
        for ts, kind in spans:
            if kind == "go_online":
                stack = ts
            elif kind == "go_offline" and stack:
                h += (datetime.fromisoformat(ts) - datetime.fromisoformat(stack)).total_seconds() / 3600
                stack = None
        return h

    # emit bike-sim driver-days
    for (drv, d), trips in sorted(trips_by.items()):
        prof = universe.get(drv)
        if prof is None:
            continue
        _emit_day(out, drv, d, sorted(trips, key=lambda x: x["t_complete"]), prof,
                  online_hours(drv, d), rng)

    # --- Rule-based (car/premium/rto): sinh trips + emit ---
    for drv, prof in sorted(universe.items()):
        if prof["simulated"]:
            continue
        for d in dates:
            trips = rule_based_trips(prof, d, rng)
            if not trips:
                continue
            oh = _clamp(rng.gauss((prof["online_lo"] + prof["online_hi"]) / 2, 1.0),
                        0.0, prof["online_hi"] + 1)
            _emit_day(out, drv, d, trips, prof, oh, rng)

    # --- hex_tracking (BIKE simulate only) từ gps dwell ---
    pings_by = defaultdict(list)
    for p in pings_all:
        pings_by[p["driver_id"]].append(p)
    hx = 0
    for drv, ps in sorted(pings_by.items()):
        ps.sort(key=lambda x: x["t"])
        seg_hex = seg_start = prev_hex = prev_t = None
        for p in ps:
            h = p["location"]["h3"]
            if h != seg_hex:
                if seg_hex is not None:
                    dur = int((datetime.fromisoformat(prev_t) - datetime.fromisoformat(seg_start)).total_seconds())
                    reposition = rng.random() < 0.05  # ~5% có target reposition (diversity)
                    out["public_driver_hex_tracking"].append({
                        "schema_version": "1.0.0", "source": "MOCK", "id": f"hx-{seed}-{hx}", "driver_id": drv,
                        "campaign_id": "repo-01" if reposition else None, "log_id": None,
                        "init_hex": prev_hex, "current_hex": seg_hex, "last_hex": prev_hex,
                        "target_hex": (f"8amock{rng.randint(0, 60):02d}") if reposition else None,
                        "last_seen_at": prev_t, "entered_current_hex_at": seg_start,
                        "stay_duration_seconds": dur,
                        "reached_target": (rng.random() < 0.6) if reposition else None,
                        "reached_target_at": None, "hex_history": None, "created_at": seg_start,
                        "updated_at": prev_t, "schedule_job_id": None, "datastream_metadata": None,
                        "tracking_status": "idle" if dur > 300 else "moving"})
                    hx += 1
                seg_hex, seg_start, prev_hex = h, p["t"], seg_hex
            prev_t = p["t"]
    return out


def build_weekly_and_missions(daily: dict, universe: dict, seed: int) -> None:
    rng = random.Random(seed ^ 0xB0B)
    by_dw = defaultdict(list)
    for r in daily["driver_income_daily"]:
        wk, ws, we = _week_key(r["order_date"])
        by_dw[(r["driver_id"], wk, ws, we)].append(r)
    kid = 0
    for (drv, wk, ws, we), rows in sorted(by_dw.items()):
        rev = sum(x["total_fee"] for x in rows)
        prof = universe.get(drv, {})
        status = "achieved" if rev >= 2_000_000 else ("at_risk" if len(rows) < 5 else "active")
        daily["kpi_driver_platform_calculator_gbq"].append({
            "schema_version": "1.0.0", "source": "MOCK", "id": f"kpi-{seed}-{kid}", "driver_id": drv,
            "driver_name": f"MOCK Driver {drv}", "sap_id": f"SAP-{drv}", "status": status,
            "week_key": wk, "week_start": ws, "week_end": we, "kpi_month": _date.fromisoformat(ws).month,
            "kpi_year": _date.fromisoformat(ws).year, "email": None, "tel": None, "engname": None,
            "depot_code": "DPT01", "depot_name": "Dong Da", "vehicle_vin_number": f"VIN{drv}",
            "vehicle_license_plate": f"29-MOCK{drv}", "vehicle_model": prof.get("vehicle_model", "Feliz S"),
            "country": "VN", "type": prof.get("track", "platform"), "last_updated_date": f"{we}T23:59:00+07:00"})
        kid += 1

    # (id, type, tên, thưởng VND, SỐ CUỐC CẦN) — target_count BẮT BUỘC: thiếu thì
    # mission vô nghĩa (remaining=0 → S6 coi như đã xong). Grounded mini-task thật.
    missions = [
        ("m-trip20", "trip_count", "20 chuyến/ngày", 30000, 20),
        ("m-rush", "rush_hour", "2 chuyến khung vàng", 30000, 2),
        ("m-week250", "trip_count", "250 chuyến/tuần", 1000000, 250),
    ]
    for mid, mtype, name, reward, target in missions:
        daily["public_mission"].append({
            "schema_version": "1.0.0", "source": "MOCK", "id": mid, "created_at": "2026-07-01T00:00:00+07:00",
            "updated_at": None, "deleted_at": None, "created_by": "gsm", "updated_by": None,
            "mission_type": mtype, "parent_id": None, "name": name, "state": "active", "audience": "bike_platform",
            "description": name, "start_time": "2026-07-01T00:00:00+07:00", "end_time": "2026-12-31T23:59:00+07:00",
            "point_id": None, "rewards": {"vnd": reward, "target_count": target},
            "mission_claim": None, "mission_code": mid,
            "time_claim_reward": None, "rule_code": None, "meta_data": None, "contract_type": None,
            "qualify_execute_code": None, "status": "active", "datastream_metadata": None,
            "business_code": None, "show_only": False, "is_ddi_mission": False})

    eid = pid = 0
    trips_by_dd = {(r["driver_id"], r["order_date"]): r["total_order"] for r in daily["driver_income_daily"]}
    prog = defaultdict(int)
    for (drv, d), n in sorted(trips_by_dd.items()):
        if n >= 20:
            daily["public_mission_earn_history"].append({
                # THỨ TỰ CỘT theo đúng spec GSM (21 cột) — id, audit, rồi nghiệp vụ
                "schema_version": "1.0.0", "source": "MOCK", "id": f"eh-{seed}-{eid}",
                "created_at": f"{d}T20:00:00+07:00", "updated_at": f"{d}T20:00:00+07:00",
                "deleted_at": None, "mission_id": "m-trip20",
                "order_id": None, "order_status": "completed", "driver_id": drv, "customer_id": None,
                "service_type": universe.get(drv, {}).get("service_type", "bike"),
                "order_time": f"{d}T20:00:00+07:00", "complete_time": f"{d}T20:00:00+07:00", "travel_mode": "bike",
                "sap_contract_type": universe.get(drv, {}).get("track", "platform"), "type": "mission",
                "count_order": n, "count_stoppoint": n, "earn": 30000, "description": "20 chuyến/ngày",
                "datastream_metadata": None, "reward_level": "1"})
            eid += 1
        prog[drv] += n
    for drv, total in sorted(prog.items()):
        daily["public_user_mission_progress"].append({
            "schema_version": "1.0.0", "source": "MOCK", "id": f"ump-{seed}-{pid}", "driver_id": drv,
            "mission_id": "m-week250", "progress_count": min(total, 250), "target_count": 250,
            "progress_value_vnd": 0, "target_value_vnd": 1000000,
            "state": "completed" if total >= 250 else "in_progress",
            "started_at": "2026-07-01T00:00:00+07:00", "updated_at": None, "claimed_at": None,
            "datastream_metadata": None})
        pid += 1

    ptypes = ["clawback_khoan", "conduct", "late", "acceptance"]
    for k in daily["kpi_driver_platform_calculator_gbq"]:
        if k["status"] == "at_risk" and rng.random() < 0.5:
            pt = rng.choice(ptypes)
            daily["driver_penalization_ATA"].append({
                "schema_version": "1.0.0", "source": "MOCK", "penalization_id": f"pen-{seed}-{k['id']}",
                "driver_id": k["driver_id"], "local_date": k["week_end"], "week_key": k["week_key"],
                "penalty_type": pt, "amount_vnd": rng.choice([40000, 100000, 200000]),
                "reason": f"vi phạm {pt}", "related_metric": "weekly_revenue", "ata_code": None,
                "status": "applied", "created_at": f"{k['week_end']}T23:00:00+07:00"})

    ftypes = ["route_deviation", "gps_anomaly", "off_app", "abnormal_cancel"]
    fid = 0
    for r in daily["driver_statistic_daily"]:
        if rng.random() < 0.01:
            daily["public_frauds"].append({
                "schema_version": "1.0.0", "source": "INFERRED", "fraud_id": f"f-{seed}-{fid}",
                "driver_id": r["driver_id"], "detected_at": f"{r['local_date']}T18:00:00+07:00",
                "fraud_type": rng.choice(ftypes), "severity": rng.choice(["low", "medium", "high"]),
                "confidence": round(rng.uniform(0.3, 0.8), 2), "evidence_ref": None, "status": "open",
                "created_at": f"{r['local_date']}T18:00:00+07:00", "datastream_metadata": None})
            fid += 1


def generate_realdata(days: int, seed_base: int, out_dir: Path, config_path: Path | None = None,
                      start_date: str = "2026-07-01", extra_kinds: bool = True) -> dict:
    cfg_path = config_path or (ROOT / "configs" / "pilot_dongda.yaml")
    out_dir.mkdir(parents=True, exist_ok=True)
    day_outputs = []
    d0 = _date.fromisoformat(start_date)
    bike_ids = []
    for i in range(days):
        day = generate_day(cfg_path, seed=seed_base + i, date=(d0 + timedelta(days=i)).isoformat())
        day_outputs.append(day)
        if i == 0:
            bike_ids = [p["driver_id"] for p in day["driver_profile"]]
    counts_kwargs = {} if extra_kinds else dict(n_bike_rto=0, n_car_platform=0, n_car_employee=0, n_car_premium=0)
    universe = build_profile_universe(bike_ids, seed_base, **counts_kwargs)
    tables = build_tables(day_outputs, universe, seed_base)
    build_weekly_and_missions(tables, universe, seed_base)

    counts = {}
    for entity, records in tables.items():
        counts[entity] = write_table_parquet(records, out_dir / f"{entity}.parquet")
    manifest = {"label": "MOCK", "generator": "gsm_core.mockgen.realdata v2 (profile-driven)",
                "days": days, "seed_base": seed_base, "start_date": start_date, "record_counts": counts,
                "profile_universe": kind_distribution(universe),
                "schema_versions": {e: "1.0.0" for e in tables}}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    return {"tables": tables, "manifest": manifest, "universe": universe}

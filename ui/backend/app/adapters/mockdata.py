"""Adapter đọc bộ mock 90 ngày `data/mock/realdata-v1` cho UI backend.

Nguồn sự thật DUY NHẤT của mọi con số trên UI driver: các bảng parquet do
`gsm_core.mockgen` sinh (nhãn MOCK, seed ghi trong manifest). Adapter CHỈ đọc +
reshape theo contract `ui/contracts/*.json` — không sinh số mới, không random.

Ngoại lệ có nhãn: `soc_percent` không tồn tại trong 13 bảng GSM (state runtime,
không phải bảng analytics) → suy DETERMINISTIC từ (driver_id, date) và ghi chú
PROXY trong response. Không dùng RNG để UI reload không nhảy số.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date as _date
from functools import lru_cache
from pathlib import Path

import polars as pl

REPO_ROOT = Path(__file__).resolve().parents[4]  # adapters→app→backend→ui→repo
DATA_DIR = REPO_ROOT / "data" / "mock" / "realdata-v1"
STATIONS_FILE = REPO_ROOT / "research" / "simulation" / "data" / "batt_dd.json"

_TABLES: dict[str, pl.DataFrame] = {}


def _table(name: str) -> pl.DataFrame:
    if name not in _TABLES:
        _TABLES[name] = pl.read_parquet(DATA_DIR / f"{name}.parquet")
    return _TABLES[name]


@lru_cache(maxsize=1)
def manifest() -> dict:
    return json.loads((DATA_DIR / "manifest.json").read_text(encoding="utf-8"))


# prefix → đội (theo generator realdata.py: d-* là 90 tài xế BIKE mô phỏng bằng sim engine;
# các đội khác rule-based). Advisor S1 (policy bike) chỉ phủ đội bike.
FLEET_BY_PREFIX = {"d": "bike-sim", "r": "bike-rto", "cp": "car-premium",
                   "ce": "car-employee", "px": "premium"}


@lru_cache(maxsize=1)
def catalog() -> dict:
    """Danh sách driver + dải ngày cho picker của UI."""
    st = _table("driver_statistic_daily")
    dates = sorted(st["local_date"].unique().to_list())
    ids = st["driver_id"].unique().to_list()
    drivers = sorted(ids, key=lambda d: (d.split("-")[0], int(d.split("-")[1])))
    return {"data_mode": "mock-realdata", "is_mock": True,
            "label": manifest().get("label", "MOCK"),
            "engine_commit": manifest().get("engine_commit"),
            "dates": dates,
            "drivers": [{"driver_id": d,
                         "fleet": FLEET_BY_PREFIX.get(d.split("-")[0], "unknown")}
                        for d in drivers]}


def _soc_proxy(driver_id: str, date: str) -> int:
    """PROXY deterministic 30..95 — SOC không có trong bảng GSM (xem docstring module)."""
    h = hashlib.sha256(f"{driver_id}|{date}|soc".encode()).digest()
    return 30 + h[0] % 66


def _stat_row(driver_id: str, date: str) -> dict | None:
    df = _table("driver_statistic_daily").filter(
        (pl.col("driver_id") == driver_id) & (pl.col("local_date") == date))
    return df.row(0, named=True) if df.height else None


def _income_row(driver_id: str, date: str) -> dict | None:
    df = _table("driver_income_daily").filter(
        (pl.col("driver_id") == driver_id) & (pl.col("order_date") == date))
    return df.row(0, named=True) if df.height else None


def _missions(driver_id: str) -> list[dict]:
    """Tiến độ mission (bảng progress là snapshot NGÀY CUỐI của chuỗi 90 ngày — nhãn rõ)."""
    prog = _table("public_user_mission_progress").filter(pl.col("driver_id") == driver_id)
    if not prog.height:
        return []
    mi = _table("public_mission")
    name_by_id = dict(zip(mi["id"].to_list(), mi["name"].to_list()))
    reward_by_id: dict[str, int] = {}
    for row in mi.iter_rows(named=True):
        try:
            rw = json.loads(row["rewards"]) if isinstance(row["rewards"], str) else row["rewards"]
            reward_by_id[row["id"]] = int(rw.get("vnd", 0)) if isinstance(rw, dict) else 0
        except Exception:
            reward_by_id[row["id"]] = 0
    out = []
    for r in prog.iter_rows(named=True):
        out.append({
            "mission_id": r["mission_id"],
            "title": name_by_id.get(r["mission_id"], r["mission_id"]),
            "progress": int(r["progress_count"] or 0),
            "target": int(r["target_count"] or 0),
            "reward_vnd": reward_by_id.get(r["mission_id"], 0),
            "done": (r["state"] or "").lower() in ("completed", "claimed", "done"),
        })
    return out


def _mission_reward_on(driver_id: str, date: str) -> int:
    """Thưởng mission ĐÃ TRẢ trong ngày — từ earn_history (sự kiện sim)."""
    eh = _table("public_mission_earn_history")
    if "driver_id" not in eh.columns:
        return 0
    df = eh.filter(pl.col("driver_id") == driver_id)
    if not df.height:
        return 0
    # schema thật của bảng: thưởng = `earn`, mốc đạt = `complete_time`
    df = df.filter(pl.col("complete_time").str.starts_with(date))
    return int(df["earn"].sum() or 0) if df.height else 0


def driver_state(driver_id: str, date: str) -> dict:
    """Contract driver_state v1.1 — số từ bảng mock, tiền tách gross/payout."""
    stat = _stat_row(driver_id, date)
    inc = _income_row(driver_id, date)
    if stat is None or inc is None:
        raise KeyError(f"không có dữ liệu cho {driver_id} ngày {date}")

    gross = int(inc["total_fee"])
    payout_trip = int(inc["commission"])          # gross × driver_share (generator realdata.py)
    mission_paid = _mission_reward_on(driver_id, date)
    soc = _soc_proxy(driver_id, date)
    rated_n = int(stat["total_order_rating"] or 0)

    return {
        "driver_id": driver_id,
        "driver_name": f"Tài xế mô phỏng {driver_id}",
        "shift_status": "ON_SHIFT" if int(stat["completed_count"]) > 0 else "OFF_SHIFT",
        "soc_percent": soc,                        # PROXY deterministic — xem docstring
        "vehicle_range_km": round(soc * 1.1, 1),   # PROXY: ~110km/100% (bike điện, ASSUMPTION)
        "money": {
            "gross_vnd": gross,
            "payout_vnd": payout_trip + mission_paid,
            "payout_breakdown": {
                "trip_payout_vnd": payout_trip,
                "mission_reward_vnd": mission_paid,
                # day_bonus/newbie không có bảng riêng trong 13 bảng GSM — xem khu Mô phỏng
            },
            "est_net_vnd": None,                   # chưa đủ known costs + definition (CLAUDE §5)
            "definition_version": "mock-realdata-v1",
        },
        "rating": {
            "n": rated_n,
            "avg": round(float(stat["total_rating"]) / rated_n, 2) if rated_n else None,
            "five_rate": round(int(stat["count_rating_5_star"]) / rated_n, 3) if rated_n else None,
        },
        "missions": _missions(driver_id),
        "payout_summary": {                        # khối v1.0 — Flutter v0 của Khánh vẫn đọc được
            "value": float(payout_trip + mission_paid),
            "currency": "VND",
            "trips_count": int(stat["completed_count"]),
            "scenario_id": f"mock-realdata:{date}",
            "seed": int(manifest().get("seed_base", 0)),
            "data_mode": "mock-realdata",
            "is_mock": True,
        },
    }


def driver_history(driver_id: str, end_date: str, days: int = 14) -> dict:
    """Chuỗi ngày (payout/gross/cuốc/giờ online) lùi từ end_date — cho màn Thu nhập."""
    inc = _table("driver_income_daily").filter(pl.col("driver_id") == driver_id)
    stat = _table("driver_statistic_daily").filter(pl.col("driver_id") == driver_id)
    onl = _table("driver_online_hours_sap_id").filter(pl.col("driver_id") == driver_id)
    acc_by_date = {r["local_date"]: r for r in stat.iter_rows(named=True)}
    onl_by_date = {r["local_date"]: float(r["online_time"]) for r in onl.iter_rows(named=True)}
    rows = [r for r in inc.iter_rows(named=True) if r["order_date"] <= end_date]
    rows.sort(key=lambda r: r["order_date"])
    rows = rows[-days:]
    out = []
    for r in rows:
        d = r["order_date"]
        s = acc_by_date.get(d, {})
        out.append({
            "date": d,
            "gross_vnd": int(r["total_fee"]),
            "payout_vnd": int(r["commission"]) + _mission_reward_on(driver_id, d),
            "trips": int(r["total_order"]),
            "online_h": round(onl_by_date.get(d, 0.0), 2),
            "acceptance_rate": float(s.get("acceptance_rate", 0.0) or 0.0),
        })
    return {"driver_id": driver_id, "data_mode": "mock-realdata", "is_mock": True,
            "days": out}


@lru_cache(maxsize=1)
def stations() -> list[dict]:
    """11 tủ đổi pin THẬT (OSM Overpass, research/simulation/data/batt_dd.json)."""
    raw = json.loads(STATIONS_FILE.read_text(encoding="utf-8"))
    out = []
    for el in raw.get("elements", []):
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        tags = el.get("tags", {})
        out.append({"id": f"osm-{el.get('id')}", "lat": float(lat), "lng": float(lon),
                    "name": tags.get("name") or tags.get("operator") or "Tủ đổi pin (OSM)",
                    "available_ports": None, "total_ports": None, "distance_km": None})
    return out


@lru_cache(maxsize=64)
def _demand_by_hex(date: str, hour: int) -> list[tuple[str, int]]:
    t = _table("trips").filter(
        pl.col("request_time").str.starts_with(date)
        & (pl.col("request_time").str.slice(11, 2) == f"{hour:02d}"))
    if not t.height:
        return []
    agg = t.group_by("pickup_h3").len().sort("len", descending=True)
    return [(r["pickup_h3"], int(r["len"])) for r in agg.iter_rows(named=True)]


def map_context(date: str, hour: int, driver_id: str | None = None) -> dict:
    """Contract map_context — demand zones = SỐ CUỐC ĐẶT theo hex×giờ từ bảng trips.

    Đây là demand PROXY đúng nghĩa SCOPE F2 (số đơn đặt theo khu vực × thời điểm),
    không phải pool matching và không hứa đơn nào về tay ai.
    """
    import h3
    pairs = _demand_by_hex(date, hour)
    top = pairs[:12]
    max_n = top[0][1] if top else 1
    zones = []
    for hex_id, n in top:
        try:
            lat, lng = h3.cell_to_latlng(hex_id)
        except Exception:
            continue
        zones.append({"h3_index": hex_id, "lat": lat, "lng": lng,
                      "intensity": round(n / max_n, 2), "freshness_sec": 0})
    center = (21.0180, 105.8300)
    if driver_id and zones:
        center = (zones[0]["lat"], zones[0]["lng"])
    alerts = []
    if top and top[0][1] >= 5:
        alerts.append({
            "id": f"demand-{date}-{hour:02d}", "type": "high_demand",
            "title": f"Nhu cầu cao lúc {hour:02d}h (dữ liệu mô phỏng)",
            "message": f"Khu vực đông đơn nhất có {top[0][1]} đơn đặt trong khung {hour:02d}h. "
                       "Số đơn ĐẶT theo khu vực — không đảm bảo đơn được phân cho bạn.",
            "severity": "info"})
    return {
        "scenario_id": f"mock-realdata:{date}:{hour:02d}",
        "seed": int(manifest().get("seed_base", 0)),
        "data_mode": "mock-realdata",
        "timestamp": f"{date}T{hour:02d}:00:00+07:00",
        "driver_location": {"lat": center[0], "lng": center[1], "heading": 0.0, "speed_kmh": 0.0},
        "demand_zones": zones,
        "charging_stations": stations(),
        "alerts": alerts,
    }


def default_view() -> dict:
    """Driver/ngày mặc định khi UI mở lần đầu: tài xế BIKE-SIM nhiều cuốc nhất
    (đội d-* — nơi advisor S1 có policy đúng; các đội khác vẫn chọn được qua picker)."""
    cat = catalog()
    date = cat["dates"][-1]
    st = _table("driver_statistic_daily").filter(
        (pl.col("local_date") == date) & pl.col("driver_id").str.starts_with("d-")) \
        .sort("completed_count", descending=True)
    fallback = cat["drivers"][0]["driver_id"]
    return {"driver_id": st["driver_id"][0] if st.height else fallback, "date": date}

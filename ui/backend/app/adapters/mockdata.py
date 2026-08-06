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


@lru_cache(maxsize=1)
def _soc_low_threshold_pct() -> float:
    """Ngưỡng SOC 'thấp' — đọc ĐÚNG ngưỡng engine dùng để quyết định đi đổi pin (`E1a`, r06 CO-3).

    Bản cũ: client hardcode 25 trong khi engine dùng `vehicle.swap_soc_threshold_pct = 20` —
    UI tự đặt ngưỡng khác canonical source, đúng họ lỗi `D-M3-17` (tầm pin từng lệch 1,76×
    cũng vì kiểu này). Client chỉ được ĐỌC số này qua payload, không tự bịa.
    """
    from gsm_sim.runner import Config
    veh = Config.load(str(REPO_ROOT / "configs" / "pilot_dongda.yaml")).get("vehicle")
    return float(veh["swap_soc_threshold_pct"])


@lru_cache(maxsize=1)
def _range_band() -> tuple[float, float, float, float]:
    """Dải tầm pin ở SOC hiện tại — suy từ ĐÚNG hệ số engine dùng (`D-M3-17`).

    Trả `(km_per_pct_ngan, km_per_pct_dai, consume_lon, consume_nho)`.

    Vì sao phải dùng một DẢI chứ không một số: `13 bảng GSM` và bảng mock **không có** thông tin
    đội pin — `driver_type` chỉ nói loại xe (`bike-electric`, `car`…), còn engine phân đội pin
    theo *archetype* (P1 sạc · P2/P4/P6/P7 đổi pin · P3/P5 chia 50/50). Nên ở đây ta **không
    biết** tài xế thuộc đội nào.

    Bản cũ giải quyết bằng cách bịa một hệ số (`soc * 1.1` ⇒ 110 km ở SOC 100%), lệch tới
    **1,76×** so với đội đổi pin (62,5 km) — đó chính là `D-M3-17`. Nay: lấy hệ số từ
    `configs/pilot_dongda.yaml` (nguồn cấu hình duy nhất) và **hiển thị đầu THẤP của dải**.

    Chọn thận trọng vì hậu quả không đối xứng: báo tầm ngắn hơn thực tế chỉ gây bất tiện, báo dài
    hơn thực tế có thể làm tài xế hết pin giữa đường.
    """
    from gsm_sim.runner import Config
    veh = Config.load(str(REPO_ROOT / "configs" / "pilot_dongda.yaml")).get("vehicle")
    swap = float(veh["swap_consume_pct_per_km"])
    charge = float(veh["charge_consume_pct_per_km"])
    lon, nho = max(swap, charge), min(swap, charge)
    return 1.0 / lon, 1.0 / nho, lon, nho


def _range_fields(soc: int, fleet: str) -> dict:
    """Khối field tầm pin — kèm CỜ cho biết con số có cơ sở hay không (`D-M3-18`).

    Engine chỉ mô hình xe máy điện (hai loại pin). Với tài xế xe hơi, hệ số xe máy không áp dụng
    được, và repo chưa có tham số nào cho xe hơi ⇒ ta phải nói *"chưa có cơ sở"* thay vì lặng lẽ
    đưa một con số sai loại xe.
    """
    km_ngan, km_dai, lon, nho = _range_band()
    la_bike = fleet.startswith("bike")
    return {
        "vehicle_range_km": round(soc * km_ngan, 1),
        "vehicle_range_km_low": round(soc * km_ngan, 1),
        "vehicle_range_km_high": round(soc * km_dai, 1),
        "vehicle_range_km_applicable": la_bike,
        "vehicle_range_km_basis": (
            f"THẬN TRỌNG — mức tiêu hao cao nhất ({lon:.2f}%/km, đội đổi pin); đội sạc đi xa hơn "
            f"({nho:.2f}%/km). Bảng dữ liệu không cho biết tài xế thuộc đội nào nên hiển thị đầu "
            f"thấp của dải."
            if la_bike else
            f"KHÔNG CÓ CƠ SỞ cho đội `{fleet}` — hệ số {lon:.2f}/{nho:.2f}%/km là của XE MÁY "
            f"điện; repo chưa có tham số tiêu hao cho xe hơi. Không hiển thị số này cho tài xế "
            f"(D-M3-18)."),
    }


# prefix → đội (theo generator realdata.py: d-* là 90 tài xế BIKE mô phỏng bằng sim engine;
# các đội khác rule-based). Advisor S1 (policy bike) chỉ phủ đội bike.
# R5-B F-01 (UPDATE-072): map SAI một bậc — generator `mockgen/profiles.py:65` gán
# cp=car_platform (VF5) và px=car_premium (VF8 Luxury); bản cũ ghi cp→"car-premium",
# px→"premium" ⇒ 15 tài xế VF5 hiện nhãn "premium" ngay trên picker của Cường.
FLEET_BY_PREFIX = {"d": "bike-sim", "r": "bike-rto", "cp": "car-platform",
                   "ce": "car-employee", "px": "car-premium"}


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
        # Q-06 (Cường chốt 2026-07-28, phương án b): nhãn nguồn đi CÙNG dữ liệu, không để UI
        # tự nhớ. 13 bảng GSM KHÔNG có telemetry pin ⇒ số này là mô phỏng, phải nói rõ với
        # tài xế. Nếu chỉ sửa `app.js` thì màn hình khác / Flutter của Khánh lại quên —
        # đúng mẫu lỗi "sửa một tầng, tầng khác không biết".
        "soc_source": "MOCK",
        # E1a: ngưỡng cảnh báo SOC — client ĐỌC, không tự đặt (bản cũ app.js hardcode 25 ≠
        # engine 20; họ D-M3-17). Test parity: ui/backend/tests/test_range_matches_engine.py
        "soc_low_threshold_pct": _soc_low_threshold_pct(),
        "vehicle_range_km_source": "MOCK",          # suy TỪ soc bịa ⇒ cũng là mock
        # D-M3-17: tầm pin nay suy từ ĐÚNG hệ số engine (xem `_range_band`). Hiển thị đầu THẤP
        # của dải vì không biết tài xế thuộc đội đổi pin hay đội sạc; dải đầy đủ + cơ sở đi kèm
        # để người đọc biết đây là số thận trọng, không phải số chính xác.
        #
        # D-M3-18: hệ số này là của XE MÁY. Engine và config KHÔNG mô hình xe hơi, mà catalog có
        # 40/150 tài xế car (cp/ce/px). Với họ con số dưới đây KHÔNG có cơ sở — nên có cờ
        # `vehicle_range_km_applicable=False`. Giữ nguyên kiểu `number` (không trả null) vì
        # `driver_state.dart:56` ép `as num` ⇒ null sẽ làm app Flutter crash; UI đọc cờ để ẩn.
        **_range_fields(soc, FLEET_BY_PREFIX.get(driver_id.split("-")[0], "unknown")),
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

"""Derive L3 `allocation_input` — input S4 CapacityAlloc (platform-level chống herding).

candidates = advice của nhiều driver (swap_window/standby_zone). station_capacity từ
station_registry throughput; zone_supply từ config threshold. Nhãn source MOCK.
"""

from __future__ import annotations

BUCKET_MIN = 30        # mặc định lịch sử — giữ để caller cũ không đổi hành vi


def derive_allocation_input(t_now: str, driver_reports: list[dict],
                            stations: list[dict], zones: list[dict],
                            params: dict | None = None,
                            bucket_min: int = BUCKET_MIN) -> dict:
    """Dựng `allocation_input` cho S4.

    `bucket_min` là **độ dài bucket THẬT của caller**, tính bằng phút. Trước 2026-07-28 hàm này
    dùng cứng hằng `BUCKET_MIN = 30`, nên bất kỳ ai chạy nhịp khác 30′ đều nhận trần trạm sai mà
    **không có tín hiệu nào** (b0-C): batch tick 60′ sẽ chỉ thấy **một nửa** sức chứa, rồi số
    `unassigned` cao sẽ bị đọc nhầm thành "chống dồn cục hiệu quả".

    Lưu ý ĐƠN VỊ — hai loại trần khác nhau, đừng gộp:
      * **trạm** = thông lượng (cuốc đổi pin/giờ) ⇒ **có** nhân theo độ dài bucket;
      * **zone** = số tài xế đứng cùng lúc ⇒ **không** nhân theo thời gian.
    """
    if int(bucket_min) <= 0:
        raise ValueError("bucket_min phải > 0")
    p = {"zone_capacity_default": 5, **(params or {})}
    bucket = t_now

    candidates = [{
        "driver_id": r["driver_id"], "advice_kind": r["advice_kind"],
        "target": r["target"], "priority_soc": r.get("priority_soc"),
    } for r in driver_reports]

    # station capacity = throughput danh định × độ dài bucket (giờ); default nếu null
    station_cap = []
    for s in stations:
        thr = s.get("throughput_nominal_per_hour")
        cap = int(round((thr if thr else 6.0) * (int(bucket_min) / 60.0)))
        station_cap.append({"station_id": s["station_id"], "bucket": bucket,
                            "capacity": max(1, cap)})

    zone_cap = [{"zone": z["zone"], "bucket": bucket,
                 "capacity": int(z.get("capacity", p["zone_capacity_default"]))}
                for z in zones]

    return {
        "schema_version": "1.0.0", "t_now": t_now, "candidates": candidates,
        "station_capacity": station_cap, "zone_supply": zone_cap,
        "view_version": "1.0.0", "source": "MOCK",
    }

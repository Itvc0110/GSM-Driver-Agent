"""Kịch bản CANONICAL dùng chung cho mọi test của `D-ADV-04` (mẫu số bucket của S1).

Tên bắt đầu bằng `_` ⇒ pytest KHÔNG collect (cùng mẫu `_health_boundary_manifest.py`).

## Vì sao MỘT fixture cho cả ba đường

Bug `D-ADV-04` là **lệch đơn vị giữa producer và solver**, và nó xuất hiện ở **ba** producer độc lập
(L1 mock · L1R · đường sản phẩm) vì cả ba **chép cùng một quy ước sai**. Nếu mỗi test tự dựng dữ liệu
riêng thì ta lại có ba kịch bản cho một sự thật — đúng cái lỗi đang sửa. Mọi test đọc **một** kịch bản
ở đây, chỉ khác hình dạng bản ghi.

## Kịch bản (khớp đúng `research/audit/2026-08-06-math-model-audit/repro-s1-denominator.py`)

Tài xế online **08:00–18:00** (10h/ngày) trong 4 ngày lịch sử; mỗi ngày kiếm:
- **60đ peak** trong **2 giờ** peak nằm trong ca (giờ 16, 17) — 6 cuốc × 10đ
- **60đ offpeak** trong **8 giờ** offpeak nằm trong ca (giờ 8..15) — 12 cuốc × 5đ

⇒ Mẫu số ĐÚNG (giờ **TRONG** bucket): `{peak: 60/2 = 30.0, offpeak: 60/8 = 7.5}`
⇒ Mẫu số SAI hiện tại (giờ **TOÀN NGÀY**): `{peak: 60/10 = 6.0, offpeak: 60/10 = 6.0}` — peak ước non **5×**

Hôm nay: hỏi lúc **15:00**, `points_now = 110` (⇒ mốc kế 160, thiếu **50đ**), quỹ giờ **6h**
(`shift_window[1] = 1260` = 21:00). Với rate đúng, `_walk` đi 15h(7,5) → 16h(30) → 17h(30) đạt 50đ tại
**2,42h**; với rate sai chỉ kiếm được **42đ** trong toàn bộ khung còn lại ⇒ **INFEASIBLE**.
"""

from __future__ import annotations

# Giờ peak/offpeak lấy theo POLICY_REC dùng chung: peak_hours = [6, 7, 16, 17], window = 6..21.
PEAK_HOURS_IN_SHIFT = [16, 17]              # 2 giờ peak nằm trong ca 08–18
OFFPEAK_HOURS_IN_SHIFT = [8, 9, 10, 11, 12, 13, 14, 15]   # 8 giờ offpeak nằm trong ca
ONLINE_START_H, ONLINE_END_H = 8, 18

HIST_DAYS = ["2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04"]
TODAY = "2026-07-05"
T_NOW = f"{TODAY}T15:00:00+07:00"
SHIFT_WINDOW = [ONLINE_START_H * 60, 1260]  # 08:00 → 21:00 ⇒ quỹ còn 6h lúc 15:00

# Kỳ vọng — hằng số của kịch bản, KHÔNG phải tham số hệ thống (đừng trích ra ngoài file này)
RATE_DUNG = {"peak": 30.0, "offpeak": 7.5}
RATE_SAI_HIEN_TAI = {"peak": 6.0, "offpeak": 6.0}
GAP_POINTS = 50
HOURS_NEEDED_DUNG = 2.4167     # 15h:7,5 + 16h:30 → 37,5; còn 12,5 tại rate 30 ⇒ 17h + 0,4167


def _iso(date: str, h: int, m: int = 0) -> str:
    return f"{date}T{h:02d}:{m:02d}:00+07:00"


def _trip(driver: str, date: str, h: int, i: int) -> dict:
    return {"schema_version": "1.0.0", "order_id": f"o-{date}-{i}", "driver_id": driver,
            "service_type": "bike", "t_request": _iso(date, h), "t_assign": _iso(date, h),
            "t_pickup": _iso(date, h), "t_complete": _iso(date, h, 20),
            "pickup": {"lat": 21.0, "lon": 105.8, "h3": "x"},
            "drop": {"lat": 21.0, "lon": 105.8, "h3": "y"},
            "dist_km": 3.0, "gross_vnd": 17000, "source": "MOCK"}


def _ev(driver: str, date: str, h: int, kind: str, i: int) -> dict:
    return {"schema_version": "1.0.0", "event_id": f"e-{date}-{kind}-{i}",
            "driver_id": driver, "t": _iso(date, h), "kind": kind, "source": "MOCK"}


def _day_trips(driver: str, date: str, peak_hours: list[int],
               offpeak_hours: list[int]) -> list[dict]:
    """6 cuốc peak (10đ) trên `peak_hours` + 12 cuốc offpeak (5đ) trên `offpeak_hours`."""
    out, i = [], 0
    if peak_hours:
        for n in range(6):
            out.append(_trip(driver, date, peak_hours[n % len(peak_hours)], i)); i += 1
    if offpeak_hours:
        for n in range(12):
            out.append(_trip(driver, date, offpeak_hours[n % len(offpeak_hours)], i)); i += 1
    return out


def build_l1(driver: str = "d-1", *,
             hist_peak_hours: list[int] | None = None,
             hist_offpeak_hours: list[int] | None = None,
             online_start_h: int = ONLINE_START_H,
             online_end_h: int = ONLINE_END_H,
             today_trips: int = 22) -> dict:
    """Hình dạng L1 (`trip_record` + `app_event`) cho `derive_bonus_gap_input`.

    Mẫu số của đường L1 lấy từ `online_minutes_on_date` = event CUỐI − event ĐẦU ⇒ fixture đặt đúng
    hai mốc `go_online`/`go_offline` để span = ca khai báo.
    Tham số `hist_*_hours` cho phép dựng ca survivorship (bucket phủ mà 0 điểm) và ca không-bằng-chứng.
    """
    ph = PEAK_HOURS_IN_SHIFT if hist_peak_hours is None else hist_peak_hours
    oh = OFFPEAK_HOURS_IN_SHIFT if hist_offpeak_hours is None else hist_offpeak_hours

    trips: list[dict] = []
    events: list[dict] = []
    for d in HIST_DAYS:
        trips += _day_trips(driver, d, ph, oh)
        events += [_ev(driver, d, online_start_h, "go_online", 0),
                   _ev(driver, d, online_end_h, "go_offline", 1)]

    # HÔM NAY: `today_trips` cuốc offpeak × 5đ, tất cả TRƯỚC 15:00.
    # 22 cuốc = 110đ ⇒ mốc kế 160, thiếu 50đ (kịch bản chính, khớp repro).
    # 29 cuốc = 145đ ⇒ thiếu 15đ — dùng cho test ghim quy ước ở cửa sổ THUẦN offpeak (18–21h,
    # 4 giờ × 7,5đ = 30đ tối đa, nên gap phải ≤ 30 mới đóng được).
    for n in range(today_trips):
        trips.append(_trip(driver, TODAY, OFFPEAK_HOURS_IN_SHIFT[n % 7], 100 + n))
    events += [_ev(driver, TODAY, online_start_h, "go_online", 0)]
    # acceptance = 1.0, completion = 1.0 ⇒ cô lập ràng buộc GIỜ (không để tỷ lệ chặn verdict)
    events += [_ev(driver, TODAY, 9, "accept", i) for i in range(30)]
    events += [_ev(driver, TODAY, 9, "complete", i) for i in range(30)]
    return {"trip_record": trips, "app_event": events}


def build_l1r(driver: str = "d-1", *,
              hist_peak_hours: list[int] | None = None,
              hist_offpeak_hours: list[int] | None = None) -> dict:
    """Hình dạng L1R: bảng `online` chỉ có TỔNG `online_time` (KHÔNG có mốc thời gian).

    Đây chính là ràng buộc của dữ liệu thật (`specs/real-data/data-contract-counterfactual.md`:
    không có `go_online`/`go_offline`) ⇒ đường này buộc phải XẤP XỈ giờ-trong-bucket từ span hoạt động.
    """
    ph = PEAK_HOURS_IN_SHIFT if hist_peak_hours is None else hist_peak_hours
    oh = OFFPEAK_HOURS_IN_SHIFT if hist_offpeak_hours is None else hist_offpeak_hours
    trips: list[dict] = []
    for d in HIST_DAYS:
        for t in _day_trips(driver, d, ph, oh):
            trips.append({"driver_id": driver, "request_time": t["t_request"],
                          "complete_time": t["t_complete"], "gross_vnd": 17000,
                          "dist_km": 3.0, "source": "MOCK"})
    for n in range(22):
        h = OFFPEAK_HOURS_IN_SHIFT[n % 7]
        trips.append({"driver_id": driver, "request_time": _iso(TODAY, h),
                      "complete_time": _iso(TODAY, h, 20), "gross_vnd": 17000,
                      "dist_km": 3.0, "source": "MOCK"})
    online = [{"driver_id": driver, "local_date": d,
               "online_time": float(ONLINE_END_H - ONLINE_START_H), "source": "MOCK"}
              for d in HIST_DAYS + [TODAY]]
    return {"trips": trips, "online": online}

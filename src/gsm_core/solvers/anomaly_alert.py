"""Solver S9 — AnomalyAlert (UC7). Rule thuần, deterministic.

Bài toán: báo cho tài xế biết hệ thống **ghi nhận DẤU HIỆU bất thường** để họ chủ động
kiểm tra/khiếu nại — trước khi bị xử lý mà không hiểu vì sao.

GUARDRAIL (nghiêm ngặt — đây là tính năng dễ gây hại nhất):
  - **KHÔNG KẾT TỘI**: chỉ "hệ thống ghi nhận dấu hiệu"; nền tảng mới là bên phán định.
    Tuyệt đối không dùng từ khẳng định vi phạm ("gian lận", "anh/chị đã vi phạm"…).
  - **Luôn kèm `INFERRED` + confidence** — cờ là suy diễn, có thể sai (false positive).
  - **KHÔNG lộ cách/ngưỡng phát hiện** (chống dạy lách) — không in `evidence_ref`.
  - Cờ đã `cleared` → **im lặng** (không cằn nhằn chuyện đã xong).
  - Luôn hướng tới **kiểm tra lại + liên hệ hỗ trợ**, không hù doạ.
"""

from __future__ import annotations

from datetime import datetime

SOLVER = "anomaly_alert"

OPEN_STATUSES = ("open", "reviewing")  # chỉ báo cái CHƯA khép lại
_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Thang CHÍNH THỨC tài xế nhìn thấy trong app ("Mức độ cảnh báo gian lận", 10/10/2025):
# Không / Thấp / Cao / Rất cao. Dùng đúng từ của app để lời tư vấn KHỚP cái họ đang xem
# (research đợt 4 — app-features-refresh-2026-07-24.md §F-2).
OFFICIAL_LEVEL = {"low": "Thấp", "medium": "Cao", "high": "Rất cao"}
NO_ALERT_LEVEL = "Không"

# "Giải trình trực tuyến" (official 15/12/2025): BẮT BUỘC trong 48 GIỜ, quá hạn ảnh
# hưởng tài khoản → nhắc quyền + hạn (KHÔNG thay tài xế giải trình — D-007).
EXPLAIN_DEADLINE_HOURS = 48.0
EXPLAIN_RIGHT = ("Nếu anh/chị thấy đánh giá chưa chính xác, có thể **giải trình trực tuyến "
                 "ngay trên app** (kèm thông tin/hình ảnh chứng minh).")


def _hours_since(detected_at: str | None, t_now: str) -> float | None:
    """Số giờ đã trôi từ lúc bị gắn cờ (None nếu thiếu mốc thời gian — KHÔNG đoán)."""
    if not detected_at:
        return None
    try:
        return (datetime.fromisoformat(t_now)
                - datetime.fromisoformat(detected_at)).total_seconds() / 3600.0
    except ValueError:
        return None

# mô tả TRUNG TÍNH theo loại — mô tả HIỆN TƯỢNG, không quy kết hành vi
_TYPE_VN = {
    "route_deviation": "lộ trình chuyến đi khác nhiều so với tuyến thường",
    "gps_anomaly": "tín hiệu định vị có đoạn bất thường",
    "off_app": "có chuyến ghi nhận dấu hiệu ngoài ứng dụng",
    "abnormal_cancel": "tỷ lệ/kiểu hủy chuyến khác thường",
    "multi_account": "hoạt động trùng khớp với tài khoản khác",
}
_SEVERITY_VN = {"high": "cần lưu ý sớm", "medium": "nên kiểm tra", "low": "mức nhẹ"}

RECOMMEND = ("Anh/chị kiểm tra lại thông tin chuyến liên quan; nếu thấy chưa chính xác, "
             "liên hệ bộ phận hỗ trợ để được rà soát.")
NOT_CONCLUSION = ("Đây là DẤU HIỆU do hệ thống tự động ghi nhận (có thể chưa chính xác), "
                  "KHÔNG phải kết luận vi phạm.")


def _num(value, unit, source):
    return {"value": round(float(value), 3), "unit": unit, "source": source}


def solve(ai: dict) -> dict:
    drv = ai["driver_id"]
    flags = [f for f in (ai.get("flags") or []) if f.get("status") in OPEN_STATUSES]
    flags.sort(key=lambda f: (_SEVERITY_ORDER.get(f["severity"], 9),
                              f.get("detected_at") or "", f["fraud_id"]))

    inputs_used = [{"view_id": f"anomaly_alert_input:{drv}",
                    "version": ai["view_version"], "freshness": ai["t_now"]}]
    caveats = [NOT_CONCLUSION, RECOMMEND, EXPLAIN_RIGHT]

    # không có cờ mở → IM LẶNG (không bịa cảnh báo, không nhắc chuyện đã khép)
    if not flags:
        return {
            "schema_version": "1.0.0", "solver": SOLVER,
            "problem_digest": (f"Tài xế {drv}: không có dấu hiệu bất thường nào đang mở "
                               f"(mức cảnh báo: {NO_ALERT_LEVEL})."),
            "inputs_used": inputs_used,
            "solution": {"notable": False, "open_count": 0, "items": [],
                          "official_level_top": NO_ALERT_LEVEL},
            "numbers": [], "sensitivity": [], "confidence": 0.8,
            "caveats": caveats, "infeasible_reason": "không có cảnh báo đang mở",
        }

    deadline_h = ai.get("explain_deadline_hours")
    deadline_h = EXPLAIN_DEADLINE_HOURS if deadline_h is None else float(deadline_h)

    items, numbers = [], [_num(len(flags), "count", "frauds:open")]
    for f in flags:
        desc = _TYPE_VN.get(f["fraud_type"], "dấu hiệu bất thường trong hoạt động")
        numbers.append(_num(f["confidence"], "ratio", f"frauds:{f['fraud_id']}"))
        elapsed = _hours_since(f.get("detected_at"), ai["t_now"])
        hours_left = None if elapsed is None else round(deadline_h - elapsed, 1)
        if hours_left is not None and hours_left > 0:
            # số giờ còn lại PHẢI truy vết được (không phải số trần trong text)
            numbers.append(_num(hours_left, "hours",
                                f"frauds:{f['fraud_id']}|deadline={deadline_h:g}h"))
        items.append({
            "fraud_id": f["fraud_id"],
            "description": desc,                      # mô tả hiện tượng, KHÔNG quy kết
            "severity": f["severity"],
            "severity_note": _SEVERITY_VN.get(f["severity"], ""),
            "official_level": OFFICIAL_LEVEL.get(f["severity"], ""),  # thang app
            "confidence": f["confidence"],
            "detected_at": f.get("detected_at"),
            "status": f["status"],
            "explain_hours_left": hours_left,         # None = thiếu mốc thời gian
            "explain_overdue": (hours_left is not None and hours_left <= 0),
            # KHÔNG có evidence_ref / ngưỡng phát hiện (chống dạy lách)
        })

    top = items[0]
    digest = (f"Tài xế {drv}: hệ thống ghi nhận {len(items)} dấu hiệu cần xem lại "
              f"— nổi bật: {top['description']} (mức cảnh báo: {top['official_level']}, "
              f"độ tin cậy {top['confidence']:.0%}). {NOT_CONCLUSION} {RECOMMEND}")
    if top["explain_hours_left"] is not None:
        digest += (f" Anh/chị còn khoảng {top['explain_hours_left']:.0f} giờ để giải trình "
                   "trực tuyến trên app." if not top["explain_overdue"]
                   else " Thời hạn giải trình trực tuyến có thể đã qua — liên hệ hỗ trợ sớm.")

    return {
        "schema_version": "1.0.0", "solver": SOLVER,
        "problem_digest": digest, "inputs_used": inputs_used,
        "solution": {"notable": True, "open_count": len(items), "items": items,
                      "top_severity": top["severity"],
                      "official_level_top": top["official_level"],
                      "explain_deadline_hours": deadline_h},
        "numbers": numbers, "sensitivity": [],
        # confidence của SOLVER = mức tin vào việc "có dấu hiệu đáng xem", cố ý thấp
        "confidence": 0.6,
        "caveats": caveats, "infeasible_reason": None,
    }

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

SOLVER = "anomaly_alert"

OPEN_STATUSES = ("open", "reviewing")  # chỉ báo cái CHƯA khép lại
_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

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
    caveats = [NOT_CONCLUSION, RECOMMEND]

    # không có cờ mở → IM LẶNG (không bịa cảnh báo, không nhắc chuyện đã khép)
    if not flags:
        return {
            "schema_version": "1.0.0", "solver": SOLVER,
            "problem_digest": f"Tài xế {drv}: không có dấu hiệu bất thường nào đang mở.",
            "inputs_used": inputs_used,
            "solution": {"notable": False, "open_count": 0, "items": []},
            "numbers": [], "sensitivity": [], "confidence": 0.8,
            "caveats": caveats, "infeasible_reason": "không có cảnh báo đang mở",
        }

    items, numbers = [], [_num(len(flags), "count", "frauds:open")]
    for f in flags:
        desc = _TYPE_VN.get(f["fraud_type"], "dấu hiệu bất thường trong hoạt động")
        numbers.append(_num(f["confidence"], "ratio", f"frauds:{f['fraud_id']}"))
        items.append({
            "fraud_id": f["fraud_id"],
            "description": desc,                      # mô tả hiện tượng, KHÔNG quy kết
            "severity": f["severity"],
            "severity_note": _SEVERITY_VN.get(f["severity"], ""),
            "confidence": f["confidence"],
            "detected_at": f.get("detected_at"),
            "status": f["status"],
            # KHÔNG có evidence_ref / ngưỡng phát hiện (chống dạy lách)
        })

    top = items[0]
    digest = (f"Tài xế {drv}: hệ thống ghi nhận {len(items)} dấu hiệu cần xem lại "
              f"— nổi bật: {top['description']} ({top['severity_note']}, "
              f"độ tin cậy {top['confidence']:.0%}). {NOT_CONCLUSION} {RECOMMEND}")

    return {
        "schema_version": "1.0.0", "solver": SOLVER,
        "problem_digest": digest, "inputs_used": inputs_used,
        "solution": {"notable": True, "open_count": len(items), "items": items,
                      "top_severity": top["severity"]},
        "numbers": numbers, "sensitivity": [],
        # confidence của SOLVER = mức tin vào việc "có dấu hiệu đáng xem", cố ý thấp
        "confidence": 0.6,
        "caveats": caveats, "infeasible_reason": None,
    }

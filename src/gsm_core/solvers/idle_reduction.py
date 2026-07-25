"""Solver S7 — IdleReduction (UC5 "Reduce Idle"). Rule/stat thuần, deterministic.

Bài toán: tài xế chờ (idle) bao lâu, khoảng chờ nào **rơi vào khung nhu cầu thấp** →
gợi ý **dời nghỉ/sạc** vào đúng khung đó (thay vì đứng chờ vô ích).

GUARDRAIL D-004b (`research/simulation/action-space.md` §Phạm vi advisor) — BẮT BUỘC:
  1. **B1: khuyên MỨC THỜI GIAN, KHÔNG chọn điểm đứng hộ** → solver KHÔNG sinh/không
     đề xuất ô H3 nào (`hex` trong input chỉ để thống kê).
  2. Khu vực CHỈ nhắc lại **nhiệm vụ reposition CHÍNH THỨC của GSM** (`active_reposition`
     có `campaign_id`); không có thì KHÔNG nói gì về khu vực.
  3. Luôn kèm cảnh báo: đơn có thể phát khi đang di chuyển; từ chối ảnh hưởng tỷ lệ nhận.
  4. Demand là **PROXY** (chỉ đơn ĐÃ phục vụ) — nhãn bắt buộc, không hứa thu nhập.
  5. Không khuyên nhận/từ chối/hủy đơn cụ thể (§5).
"""

from __future__ import annotations

SOLVER = "idle_reduction"

# ngưỡng: chờ >45 phút/ca hoặc 1 khoảng >25 phút mới coi là đáng lưu ý (tránh bịa vấn đề)
IDLE_TOTAL_ALERT_MIN = 45.0
IDLE_LONGEST_ALERT_MIN = 25.0
LOW_DEMAND_MAX = 0.5  # demand proxy ≤ ngưỡng này = khung "thấp điểm"

WARN_ACCEPTANCE = ("Đơn có thể được phát trong lúc anh/chị di chuyển; "
                   "từ chối sẽ ảnh hưởng tỷ lệ nhận cuốc.")
WARN_PROXY = ("Mức nhu cầu theo khung giờ là ƯỚC LƯỢNG từ cuốc đã hoàn thành "
              "(không phải dự báo chính thức của hãng).")
# F-1 (research đợt 4): app đã CÓ bản đồ nhiệt + "Nhiệm Vụ Tiếp Theo" (15/04/2026).
# ⇒ KHÔNG tự gợi ý khu (chồng đè tối ưu của hãng) mà TRỎ VỀ tính năng chính thức.
USE_OFFICIAL_FEATURE = ("Anh/chị có thể bật \"Dẫn đường\" ở chế độ Trực tuyến để xem "
                        "\"Nhiệm vụ tiếp theo\" — gợi ý khu vực nhiều khách của hãng.")


def _num(value, unit, source):
    return {"value": round(float(value), 3), "unit": unit, "source": source}


def solve(ii: dict) -> dict:
    drv = ii["driver_id"]
    segs = ii.get("idle_segments") or []
    total_min = float(ii.get("total_idle_min") or 0.0)
    longest_min = float(ii.get("longest_idle_min") or 0.0)
    online_h = ii.get("online_hours")
    demand = ii.get("demand_by_hour") or {}
    repo = ii.get("active_reposition")
    src = "hex_tracking:measured"

    inputs_used = [{"view_id": f"idle_reduction_input:{drv}",
                    "version": ii["view_version"], "freshness": ii["t_now"]}]
    numbers = [_num(total_min, "minutes", src)]
    if longest_min:
        numbers.append(_num(longest_min, "minutes", src))
    idle_share = None
    data_warning = None
    if online_h and online_h > 0:
        raw_share = (total_min / 60.0) / float(online_h)
        # BUG-PI5b-01: TRƯỚC ĐÂY `min(1.0, …)` CHE trạng thái bất khả (idle > online:
        # dwell offline bị gán "idle"). Nay vẫn kẹp để không hiển thị >100%, NHƯNG
        # ghi cờ cảnh báo dữ liệu thay vì im lặng.
        if raw_share > 1.01:
            data_warning = (f"dữ liệu chờ ({total_min:.0f} phút) vượt giờ online "
                            f"({float(online_h) * 60:.0f} phút) — cần kiểm tra nguồn")
        idle_share = min(1.0, raw_share)
        numbers.append(_num(idle_share, "ratio", src))

    # gom idle theo giờ → tìm khung vừa chờ NHIỀU vừa nhu cầu THẤP
    by_hour: dict[int, float] = {}
    for s in segs:
        by_hour[s["hour"]] = by_hour.get(s["hour"], 0.0) + s["duration_seconds"] / 60.0
    worst = None
    for h, mins in sorted(by_hour.items(), key=lambda x: (-x[1], x[0])):
        if demand.get(str(h), 1.0) <= LOW_DEMAND_MAX:
            worst = {"hour": h, "idle_min": round(mins, 1),
                     "demand_index": demand.get(str(h))}
            break

    notable = total_min >= IDLE_TOTAL_ALERT_MIN or longest_min >= IDLE_LONGEST_ALERT_MIN
    caveats = [WARN_ACCEPTANCE, WARN_PROXY, USE_OFFICIAL_FEATURE]
    if data_warning:
        caveats.append(data_warning)

    # KHÔNG bịa vấn đề khi tài xế không chờ nhiều
    if not notable:
        return {
            "schema_version": "1.0.0", "solver": SOLVER,
            "problem_digest": (f"Tài xế {drv}: tổng thời gian chờ {total_min:.0f} phút — "
                               "không có khoảng chờ bất thường."),
            "inputs_used": inputs_used,
            "solution": {"feasible": False, "notable": False,
                          "total_idle_min": total_min, "longest_idle_min": longest_min,
                          "idle_share": idle_share, "worst_window": None,
                          "reposition_mission": None, "data_warning": data_warning},
            "numbers": numbers, "sensitivity": [], "confidence": 0.7,
            "caveats": caveats, "infeasible_reason": "không có khoảng chờ đáng lưu ý",
        }

    if worst:
        numbers.append(_num(worst["idle_min"], "minutes", src))
        rec = (f"khung {worst['hour']:02d}h nhu cầu thấp mà anh/chị chờ "
               f"{worst['idle_min']:.0f} phút — cân nhắc dồn nghỉ/đổi pin vào khung này")
    else:
        rec = "cân nhắc dồn thời gian nghỉ/đổi pin vào khung nhu cầu thấp trong ngày"

    # điều kiện 2: CHỈ nhắc nhiệm vụ reposition chính thức nếu data có
    repo_note = None
    if repo and repo.get("campaign_id"):
        reached = repo.get("reached")
        repo_note = ("anh/chị đang có nhiệm vụ di chuyển của hãng"
                     + (" (đã hoàn thành)" if reached else " (chưa hoàn thành)"))

    digest = (f"Tài xế {drv}: chờ tổng {total_min:.0f} phút"
              + (f" ({idle_share:.0%} thời gian online)" if idle_share is not None else "")
              + f", khoảng dài nhất {longest_min:.0f} phút. Gợi ý: {rec}."
              + (f" Lưu ý: {repo_note}." if repo_note else ""))

    return {
        "schema_version": "1.0.0", "solver": SOLVER,
        "problem_digest": digest, "inputs_used": inputs_used,
        "solution": {
            "feasible": True, "notable": True,
            "total_idle_min": total_min, "longest_idle_min": longest_min,
            "idle_share": idle_share, "worst_window": worst,
            "reposition_mission": repo_note, "data_warning": data_warning,
            # KHÔNG có field nào chỉ định ô H3 để tài xế tới (D-004b/B1)
        },
        "numbers": numbers,
        "sensitivity": [{"param": "idle_threshold",
                         "total_alert_min": IDLE_TOTAL_ALERT_MIN,
                         "longest_alert_min": IDLE_LONGEST_ALERT_MIN}],
        "confidence": 0.75 if worst else 0.6,
        "caveats": caveats, "infeasible_reason": None,
    }

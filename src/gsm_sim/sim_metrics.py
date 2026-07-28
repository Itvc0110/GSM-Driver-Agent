"""SIM-5 — BỘ METRIC ĐẦY ĐỦ theo spec `00-sim-overhaul-master.md` §6.

Ba nhóm bắt buộc:
  - **Hệ thống**: served/expired rate, **thời gian chờ khách**, **mật độ cung/cầu hex × giờ**.
  - **Tài xế**: accept / completion / cancel / util / idle / cuốc / payout / điểm.
  - **Advisor (A vs B)**: uỷ quyền cho `parallel.compare` — KHÔNG viết lại ở đây.

## Nguyên tắc: KHÔNG có hai con số cho cùng một sự thật

Đây là bài học đắt nhất của SIM-1 (data nói acceptance 0.88 trong khi sim hành xử 0.96). Vì vậy:

- `driver_metrics()` **gộp từ `journey.build_journey()`**, không tự tính lại từ event.
- `system_metrics()` giữ nguyên định nghĩa của `metrics.summarize()` cho các chỉ số đã có, chỉ
  **bổ sung** phần còn thiếu.
- Có test chứng minh hai đường cho cùng kết quả.
"""

from __future__ import annotations

import statistics as st

from .journey import build_journey
from .metrics import summarize


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(round(q * (len(s) - 1)))))
    return float(s[k])


def customer_wait(result) -> dict:
    """Thời gian khách chờ từ lúc đặt tới lúc ghép được tài xế (phút).

    Chỉ tính đơn ĐƯỢC GHÉP — đơn hết hạn không có thời gian chờ hữu hạn, gộp vào sẽ bóp méo
    trung vị (và che chính vấn đề đơn không ai nhận, vốn đã có `expired_rate` riêng).
    """
    t_of = {o.order_id: o.t_min for o in result.orders}
    waits = [e.t_min - t_of[e.detail["order_id"]]
             for e in result.events
             if e.kind == "order_matched" and e.detail.get("order_id") in t_of]
    if not waits:
        return {"matched_n": 0, "wait_median_min": 0.0, "wait_p90_min": 0.0, "wait_max_min": 0.0}
    return {
        "matched_n": len(waits),
        "wait_median_min": round(st.median(waits), 3),
        "wait_p90_min": round(_pct(waits, 0.90), 3),
        "wait_max_min": round(max(waits), 3),
    }


def supply_demand_density(result) -> dict:
    """Mật độ CUNG/CẦU theo (hex, giờ) và theo giờ.

    Đây chính là phép đo đã tìm ra khuyết tật SIM-1 (05-06h có **0 tài xế** cho 93 đơn). Lúc đó
    nó là script dùng một lần; nay thành API có test để không phải dựng lại mỗi lần nghi ngờ.

    `supply` = số tài xế ĐANG TRONG CA tại giữa giờ đó (xấp xỉ theo khung ca, không phải theo
    trạng thái từng phút — đủ để phát hiện khung trống, đó là mục đích).
    """
    demand_hour: dict[int, int] = {}
    demand_cell_hour: dict[tuple[str, int], int] = {}
    for o in result.orders:
        h = int(o.t_min // 60) % 24
        demand_hour[h] = demand_hour.get(h, 0) + 1
        key = (o.pickup_cell, h)
        demand_cell_hour[key] = demand_cell_hour.get(key, 0) + 1

    expired_hour: dict[int, int] = {}
    t_of = {o.order_id: o.t_min for o in result.orders}
    for e in result.events:
        if e.kind == "order_expired":
            t = t_of.get(e.detail.get("order_id"))
            if t is not None:
                h = int(t // 60) % 24
                expired_hour[h] = expired_hour.get(h, 0) + 1

    supply_hour: dict[int, int] = {}
    for a in result.actors:
        for h in range(24):
            mid = h * 60 + 30
            if a.shift_start_min <= mid <= a.shift_end_min:
                supply_hour[h] = supply_hour.get(h, 0) + 1

    per_hour = {}
    for h in sorted(demand_hour):
        sup = supply_hour.get(h, 0)
        per_hour[h] = {
            "demand": demand_hour[h],
            "supply_drivers": sup,
            "orders_per_driver": round(demand_hour[h] / sup, 3) if sup else None,
            "expired_rate": round(expired_hour.get(h, 0) / demand_hour[h], 4),
        }
    starved = [h for h, v in per_hour.items() if v["expired_rate"] > 0.40]
    return {"per_hour": per_hour, "starved_hours": sorted(starved),
            "top_cells": sorted(demand_cell_hour.items(), key=lambda kv: -kv[1])[:10]}


def driver_metrics(result) -> dict:
    """Phân phối metric TỪNG TÀI XẾ, gộp từ `journey.build_journey`.

    Cố ý KHÔNG tính lại từ event: journey đã là nguồn sự thật per-driver và đã có bộ test bảo
    toàn riêng (SIM-2). Tính lại ở đây sẽ tạo nguồn thứ hai — đúng lỗi mà SIM-1 phải đi sửa.
    """
    rows = [build_journey(result, a.actor_id).metrics for a in result.actors]
    active = [m for m in rows if m["offers"] > 0]

    def dist(key: str, src: list[dict]) -> dict:
        vals = [float(m[key]) for m in src if m.get(key) is not None]
        if not vals:
            return {"n": 0}
        return {"n": len(vals), "median": round(st.median(vals), 4),
                "mean": round(st.mean(vals), 4),
                "p10": round(_pct(vals, 0.10), 4), "p90": round(_pct(vals, 0.90), 4)}

    by_arch: dict[str, list[float]] = {}
    for a in result.actors:
        m = build_journey(result, a.actor_id).metrics
        if m["acceptance_rate"] is not None:
            by_arch.setdefault(a.archetype, []).append(m["acceptance_rate"])

    return {
        "n_drivers": len(rows), "n_active": len(active),
        "acceptance_rate": dist("acceptance_rate", active),
        "completion_rate": dist("completion_rate", active),
        "utilization": dist("utilization", active),
        "idle_min": dist("idle_min", active),
        "trips_completed": dist("trips_completed", active),
        "payout_vnd": dist("payout_vnd", active),
        "day_bonus_vnd": dist("day_bonus_vnd", active),
        "points": dist("points", active),
        "online_min": dist("online_min", active),
        "cancel_after_accept": sum(m["cancelled_after_accept"] for m in rows),
        "skipped_soc": sum(m["skipped_soc"] for m in rows),
        "acceptance_by_archetype": {k: round(st.median(v), 4) for k, v in sorted(by_arch.items())},
    }


def system_metrics(result) -> dict:
    """Chỉ số hệ thống: kế thừa `summarize()` + bổ sung phần spec §6 còn thiếu."""
    base = summarize(result)
    return {**base, "customer_wait": customer_wait(result),
            "density": supply_demand_density(result)}


def full_report(result) -> dict:
    """Bộ metric đầy đủ cho 1 run. Advisor A/B nằm ở `parallel.compare` (không nhân bản)."""
    return {"seed": result.seed, "system": system_metrics(result),
            "drivers": driver_metrics(result), "source": "MOCK"}


# ---------------------------------------------------------------------------
# ĐA-08 bước 1 (UPDATE-075) — CÔNG BẰNG · TẬP TRUNG · KHÁCH HÀNG
#
# Vì sao thêm: hồ sơ `research/audit/2026-07-27-current-state/07` đo được advice diện rộng làm
# `served_rate` giảm 6/10 seed và đơn hết hạn +8/ngày — nhưng guardrail A/B hiện có 5 trường và
# KHÔNG bắt được điều đó. Bộ dưới đây là điều kiện tiên quyết của "chỉ tiêu chấp nhận kép":
# một kênh advice chỉ có giá trị khi Δpayout cá nhân > 0 VÀ hệ thống/khách/công bằng không xấu đi.
#
# Nguyên tắc: mọi hàm đọc THẲNG từ `RunResult` — không tính lại luật, không cần đụng engine.


def gini(values: list[float]) -> float:
    """Hệ số Gini của một phân phối (0 = đều tuyệt đối, →1 = một người ôm hết).

    Bất biến theo thang (nhân đôi mọi thu nhập không đổi kết quả) — tính chất bắt buộc để so
    được giữa hai thế giới có tổng payout khác nhau.
    """
    vals = sorted(float(v) for v in values)
    n = len(vals)
    total = sum(vals)
    if n == 0 or total <= 0:
        return 0.0
    cum = sum((2 * i - n + 1) * v for i, v in enumerate(vals))
    return round(cum / (n * total), 4)


def hhi(shares: list[float]) -> float:
    """Herfindahl chuẩn hoá về [0,1]: 0 = trải đều tuyệt đối, 1 = dồn hết vào một chỗ."""
    vals = [float(v) for v in shares if v > 0]
    n = len(vals)
    total = sum(vals)
    if n <= 1 or total <= 0:
        return 1.0 if n == 1 else 0.0
    raw = sum((v / total) ** 2 for v in vals)
    return round((raw - 1.0 / n) / (1.0 - 1.0 / n), 4)


def fairness_metrics(result) -> dict:
    """Phân phối thu nhập giữa các tài xế + TỔNG payout.

    `total_payout_vnd` là trường quan trọng nhất: không có nó thì không phân biệt được advice
    TẠO THÊM giá trị (positive-sum) với advice chỉ TÁI PHÂN PHỐI (zero-sum).
    """
    pay = [a.payout_vnd for a in result.actors]
    if not pay:
        return {"n_actors": 0, "gini_payout": 0.0, "total_payout_vnd": 0,
                "payout_p10": 0, "payout_median": 0, "payout_p90": 0}
    return {
        "n_actors": len(pay),
        "gini_payout": gini(pay),
        "total_payout_vnd": int(sum(pay)),
        "payout_p10": int(_pct(pay, 0.10)),
        "payout_median": int(st.median(pay)),
        "payout_p90": int(_pct(pay, 0.90)),
    }


def concentration_metrics(result) -> dict:
    """Dồn cục: tải giữa các TRẠM, cung giữa các Ô, và đỉnh đồng thời theo giờ.

    Đây là guardrail chống herding mà `research/00_SUMMARY.md` #15 gọi là "veto metric" —
    advice làm tăng các số này nghĩa là advisor đang tự phá giá trị của chính nó.
    """
    from collections import Counter

    import h3

    st_load = Counter(e.detail.get("station") for e in result.events
                      if e.kind in ("swap_done", "swap_failed") and e.detail.get("station"))

    # Cung theo ô = **phút hiện diện** của tài xế, quy về ô H3 của ĐIỂM ĐẾN segment.
    #
    # Vì sao điểm đến (PROXY, có chủ ý): tín hiệu herding cần bắt là *tài xế dồn về đâu*. Với
    # `rest`/`charge` thì from == to nên không sai; với `enroute`/`relocate` thì đích chính là
    # chỗ advice đẩy người ta tới. Chia đôi from/to sẽ làm loãng đúng tín hiệu cần đo.
    #
    # KHÔNG đọc `segment["cell"]` — `world._seg` KHÔNG ghi field đó (bản nháp đầu của hàm này
    # đọc nhầm và trả 0.0 im lặng; xem `test_supply_cell_hhi_is_not_silently_zero`).
    res = result.grid.res
    cell_minutes: Counter = Counter()
    for sgm in result.segments:
        dt = max(0.0, float(sgm["t1"]) - float(sgm["t0"]))
        lat, lon = sgm.get("to_lat"), sgm.get("to_lon")
        if dt <= 0.0 or lat is None or lon is None:
            continue
        cell_minutes[h3.latlng_to_cell(float(lat), float(lon), res)] += dt

    swap_hour = Counter(int(e.t_min // 60) for e in result.events if e.kind == "go_swap")
    rest_hour = Counter(int(e.t_min // 60) for e in result.events if e.kind == "rest")
    return {
        "station_hhi": hhi(list(st_load.values())),
        "supply_cell_hhi": hhi(list(cell_minutes.values())),
        "n_supply_cells": len(cell_minutes),
        "supply_minutes_total": round(sum(cell_minutes.values()), 1),
        "peak_swap_per_hour": max(swap_hour.values()) if swap_hour else 0,
        "peak_rest_per_hour": max(rest_hour.values()) if rest_hour else 0,
        "n_stations_used": len(st_load),
    }


def customer_impact(result) -> dict:
    """Tác động lên KHÁCH — gồm cả đơn KHÔNG ai nhận (thứ `customer_wait` cố ý bỏ ra).

    `customer_wait()` chỉ đo đơn được ghép, đúng về thống kê nhưng che mất phần hại lớn nhất.
    Ở đây tách rõ: chờ của đơn được phục vụ, và các dạng KHÔNG được phục vụ.
    """
    from collections import Counter
    w = customer_wait(result)
    kinds = Counter(e.kind for e in result.events)
    total = len(result.orders)
    expired = kinds.get("order_expired", 0)
    return {
        "orders_total": total,
        "expired_n": expired,
        "expired_rate": round(expired / total, 4) if total else 0.0,
        "wait_median_min": w["wait_median_min"],
        "wait_p90_min": w["wait_p90_min"],
        "unserved_breakdown": {
            "expired": expired,
            "censored": kinds.get("order_censored", 0),
            "cancelled_after_accept": kinds.get("order_cancelled_after_accept", 0),
        },
    }


def system_guardrail(result) -> dict:
    """Gói 4 tầng cho chỉ tiêu kép: hệ thống · khách hàng · công bằng · tập trung."""
    s = summarize(result)
    out = {"served_rate": s["served_rate"], "orders_completed": s["orders_completed"]}
    out.update(fairness_metrics(result))
    out.update(customer_impact(result))
    out.update(concentration_metrics(result))
    # `supply_demand_density()` có từ SIM-5 nhưng chưa consumer nào gọi. Rút một SCALAR so được
    # A/B: số giờ "đói cung" (>40% đơn hết hạn trong giờ đó). Không định nghĩa lại — gọi hàm gốc.
    out["starved_hours_n"] = len(supply_demand_density(result)["starved_hours"])
    return out

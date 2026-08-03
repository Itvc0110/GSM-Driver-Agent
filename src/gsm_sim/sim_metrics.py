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


def cost_summary(result) -> dict:
    """B1 (PLAN-cycle-wx): đọc sổ chi phí `actor.cost_vnd` (T-045b) — tới nay KHÔNG thước nào
    đọc nó, sổ chết. CHỈ đọc, không trừ vào `payout_vnd` (§5 CLAUDE.md: gross/payout/net tách
    bạch) — `net_mean_vnd` là khoá MỚI, không đụng payout của bất kỳ actor nào.

    Mặc định config chi phí = 0 (T-045b) ⇒ `cost_total_vnd == 0` và `net_mean_vnd ==
    payout_vnd.mean` cho tới khi bước sau (B3/C1) bật chi phí thật."""
    pays = [float(a.payout_vnd) for a in result.actors]
    costs = [float(a.cost_vnd) for a in result.actors]
    nets = [p - c for p, c in zip(pays, costs)]
    return {
        "cost_total_vnd": int(round(sum(costs))),
        "cost_mean_vnd": round(st.mean(costs), 2) if costs else 0.0,
        "net_mean_vnd": round(st.mean(nets), 2) if nets else 0.0,
    }


def full_report(result) -> dict:
    """Bộ metric đầy đủ cho 1 run. Advisor A/B nằm ở `parallel.compare` (không nhân bản)."""
    return {"seed": result.seed, "system": system_metrics(result),
            "drivers": driver_metrics(result), "cost": cost_summary(result), "source": "MOCK"}


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
    """Gói NĂM tầng cho chỉ tiêu kép: hệ thống · khách hàng · công bằng · tập trung ·
    SỨC KHOẺ (D-M3-05 — lan can còn nguyên không)."""
    s = summarize(result)
    out = {"served_rate": s["served_rate"], "orders_completed": s["orders_completed"]}
    out.update(fairness_metrics(result))
    out.update(customer_impact(result))
    out.update(concentration_metrics(result))
    # `supply_demand_density()` có từ SIM-5 nhưng chưa consumer nào gọi. Rút một SCALAR so được
    # A/B: số giờ "đói cung" (>40% đơn hết hạn trong giờ đó). Không định nghĩa lại — gọi hàm gốc.
    out["starved_hours_n"] = len(supply_demand_density(result)["starved_hours"])
    out.update(health_guardrail(result))
    return out


# ---------------------------------------------------------------------------
# D-M3-05 — GUARDRAIL TẦNG 5: "lan can sức khoẻ còn nguyên không"
#
# Vì sao tồn tại: phản biện chéo từng đo được (5 seed) rằng xoá lan can `fatigued` làm
# veto đi 54/90 → 0/90 mà test vẫn xanh, `net_mean_all` TĂNG, và guardrail 4 tầng không
# tầng nào tố giác — đúng kịch bản "mua Δ bằng cách xoá lan can".
#
# KỶ LUẬT (spec §1.2b + PHÁN QUYẾT 2026-07-31): tầng 5 chỉ phát ĐẾM (lần) và PHÚT.
# Không hệ số, không `*_vnd`, không vào công thức chấp nhận — bất kỳ hằng nào nhân các số
# này với tiền chính là ∂payout/∂F. Cổng MỘT CHIỀU (chỉ tố giác suy giảm) — chống Goodhart:
# không ai được thưởng vì veto CAO (ép tài xế chạm mệt nhiều hơn để "qua cổng").
#
# HAI định nghĩa quá-sức đo SONG SONG (Cường chốt 2026-07-31 — 62/90 vs 25/90 vượt 240′
# tuỳ định nghĩa, chọn một là mù nửa bức tranh):
#   work_span  = khoảng nghỉ→nghỉ, GỒM đứng chờ khách (làm việc liên tục không nghỉ);
#   drive_min  = tổng phút LÁI THẬT (enroute/on_trip/relocate) trong khoảng đó.
# ---------------------------------------------------------------------------

REST_RAILS = ("soc_low", "fatigued", "defer_cap")
_DRIVE_KINDS = frozenset({"enroute", "on_trip", "relocate"})
_RECOVERY_KINDS = frozenset({"rest", "charge"})
# Ngưỡng break DẪN XUẤT từ phân phối nghỉ của world (uniform[REST_MIN, REST_MAX]) —
# mọi lần nghỉ thật đều reset chuỗi; swap pin 1–2′ thì KHÔNG (không phải hồi phục).
# Đổi phân phối nghỉ ở world mà không căn lại ⇒ test T7 đỏ.
DRIVE_BREAK_MIN = 20.0
RAIL_ALIVE_MIN_N = 20           # dưới mức này rail "sống/chết" không phân biệt được với nhiễu
REST_TOTAL_DROP_TOL = 0.02      # rest_min_total giảm >2% giữa hai arm ⇒ tố giác
SPAN_P90_RISE_TOL = 0.10        # p90 quá-sức tăng >10% ⇒ tố giác (p90, KHÔNG max — nhiễu ±36%)


def rest_rails_audit(result) -> dict:
    """Đếm veto lan can từ event `advice_rest_veto` (log-only, world ghi mọi kết cục
    không-defer). `veto_calls_n` đi kèm BẮT BUỘC: advice làm tài xế online lâu hơn ⇒ mẫu
    số veto đổi theo arm — đọc count trần mà không đọc calls là đọc sai."""
    out = {f"veto_{r}_n": 0 for r in REST_RAILS}
    calls = 0
    for e in result.events:
        if e.kind != "advice_rest_veto":
            continue
        calls += 1
        r = e.detail.get("reason")
        if r in REST_RAILS:
            out[f"veto_{r}_n"] += 1
    out["veto_calls_n"] = calls
    out["veto_fired_n"] = sum(out[f"veto_{r}_n"] for r in REST_RAILS)
    return out


def continuous_work(result, break_min: float = DRIVE_BREAK_MIN) -> dict:
    """Per-actor rồi tổng hợp: work_span (nghỉ→nghỉ) và drive_min (phút lái thật) —
    chuỗi reset khi gặp segment rest/charge dài ≥ `break_min`; khoảng trống idle (đứng
    chờ khách) KHÔNG reset span và không cộng vào drive."""
    import collections
    by_actor: dict[int, list] = collections.defaultdict(list)
    for s in result.segments:
        by_actor[s["actor_id"]].append(s)
    spans, drives = [], []
    for segs in by_actor.values():
        segs.sort(key=lambda s: (s["t0"], s["t1"]))
        span0 = span1 = None
        drive = 0.0
        best_span = best_drive = 0.0
        for s in segs:
            if s["kind"] in _RECOVERY_KINDS and (s["t1"] - s["t0"]) >= break_min:
                if span0 is not None:
                    best_span = max(best_span, span1 - span0)
                    best_drive = max(best_drive, drive)
                span0, drive = None, 0.0
                continue
            if s["kind"] not in _DRIVE_KINDS:
                continue
            if span0 is None:
                span0 = s["t0"]
            span1 = s["t1"] if span1 is None else max(span1, s["t1"])
            drive += s["t1"] - s["t0"]
        if span0 is not None:
            best_span = max(best_span, span1 - span0)
            best_drive = max(best_drive, drive)
        spans.append(best_span)
        drives.append(best_drive)
    import numpy as np
    sp, dr = np.asarray(spans or [0.0]), np.asarray(drives or [0.0])
    return {"work_span_p50": round(float(np.percentile(sp, 50)), 1),
            "work_span_p90": round(float(np.percentile(sp, 90)), 1),
            "work_span_max": round(float(sp.max()), 1),
            "drive_min_p50": round(float(np.percentile(dr, 50)), 1),
            "drive_min_p90": round(float(np.percentile(dr, 90)), 1),
            "drive_min_max": round(float(dr.max()), 1)}


def touched_actors(result, channel: str | None = None) -> set[int]:
    """Tập actor THỰC SỰ nhận lời khuyên (bị can thiệp chạm tới).

    Vì sao cần (vòng soi D-M3-04, 2026-07-31): cổng tầng 5 đặt trên TỔNG cohort chỉ đủ nhạy
    khi can thiệp chạm gần hết đội. Đo được: ladder `all` + coverage `all` chạm **100%** tài
    xế (`rest_min_total` +15% ≫ tolerance 2%) — cổng ổn. NHƯNG kênh THƯA như `rest_window`
    trong multiday chỉ nói ~11 lần/ngày cho 90 tài xế ⇒ chạm ~10% ⇒ hiệu ứng bị **pha loãng
    ~10×** xuống dưới nhiễu seed ⇒ cổng canh NHIỄU, verdict thành tuỳ seed, và người sửa sẽ
    nới tolerance thay vì sửa mẫu số (mẫu `D-R20`).
    """
    ids: set[int] = set()
    for e in result.events:
        if not str(e.kind).startswith("advice_") or int(e.actor_id) < 0:
            continue
        if channel is not None and (e.detail or {}).get("channel") != channel:
            continue
        ids.add(int(e.actor_id))
    return ids


def health_guardrail(result, actor_ids: set[int] | None = None) -> dict:
    """Tầng 5 — chỉ ĐẾM và PHÚT, không bao giờ VND.

    `actor_ids`: giới hạn `rest_min_total` về NHÓM BỊ CHẠM (xem `touched_actors`). None =
    toàn cohort (hành vi cũ, giữ nguyên cho mọi consumer hiện có).
    """
    acts = (result.actors if actor_ids is None
            else [a for a in result.actors if int(a.actor_id) in actor_ids])
    out = {"rest_min_total": round(sum(a.rest_min for a in acts), 1),
           "n_actors_scope": len(acts)}
    out.update(rest_rails_audit(result))
    out.update(continuous_work(result))
    return out


def health_guardrail_flags(a: dict, b: dict) -> list[str]:
    """Cổng MỘT CHIỀU giữa arm đối chứng `a` và arm advice `b` — tố giác SUY GIẢM sức khoẻ.

    (i) lan can SỤP VỀ 0 (sống ở A với mẫu đủ, chết ở B) — kịch bản xoá-lan-can;
    (ii) tổng phút nghỉ giảm quá tolerance;
    (iii) p90 của MỘT TRONG HAI định nghĩa quá-sức tăng quá tolerance.
    Không có chiều khen — veto cao hơn/nghỉ nhiều hơn KHÔNG cộng điểm (chống Goodhart).
    """
    flags: list[str] = []
    for r in REST_RAILS:
        va, vb = int(a.get(f"veto_{r}_n") or 0), int(b.get(f"veto_{r}_n") or 0)
        if va >= RAIL_ALIVE_MIN_N and vb == 0:
            flags.append(f"lan can `{r}` SỤP VỀ 0 (A={va}, B=0) — nghi xoá lan can, "
                         f"TREO mọi Δ cho tới khi giải thích được")
    ra, rb = float(a.get("rest_min_total") or 0), float(b.get("rest_min_total") or 0)
    if ra > 0 and (ra - rb) / ra > REST_TOTAL_DROP_TOL:
        flags.append(f"rest_min_total giảm {(ra - rb) / ra:.1%} (A={ra:.0f}′ → B={rb:.0f}′) "
                     f"— advice đang ăn vào nghỉ")
    for k in ("work_span_p90", "drive_min_p90"):
        ka, kb = float(a.get(k) or 0), float(b.get(k) or 0)
        if ka > 0 and (kb - ka) / ka > SPAN_P90_RISE_TOL:
            flags.append(f"{k} tăng {(kb - ka) / ka:.1%} (A={ka:.0f}′ → B={kb:.0f}′) "
                         f"— advice kéo dài chuỗi làm việc liên tục")
    return flags


# ---------------------------------------------------------------------------
# D-M3-10: CỔNG HỢP LỆ CỦA MỌI ARM A/B — adherence phải nằm TRONG artifact
#
# Luật đã có từ lâu trong tài liệu: *"mọi arm phải báo kèm `decision_adherence` per
# archetype so với danh nghĩa; lệch > 0,02 ⇒ TREO kết quả"*. Đo được 2026-07-30:
# `parallel.py` / `sim_metrics.py` / `scripts/run_parallel.py` tham chiếu
# `adherence`/`followed`/`decided` **ĐÚNG 0 LẦN**, và artifact 35–39 **không có khoá
# `adherence` nào**. Tức cổng chỉ tồn tại trên giấy.
#
# Đó là LÝ DO TRỰC TIẾP `D-M3-01` sống được qua 39 artifact: `shift_extend` báo
# `decision_adherence = 1,000` (sự thật 0,473) suốt 39 lần mà không cổng nào bắn.
# ---------------------------------------------------------------------------

# Hai loại cổng, và chúng KHÁC NHAU về bản chất — đừng gộp:
#
#   (1) BẤT KHẢ (hard, per-seed): trạng thái không thể đúng dù nhiễu thế nào.
#       `decision_adherence` đúng bằng 1,0 hoặc 0,0 trên mẫu số đủ lớn là dấu hiệu
#       mẫu số/tử số hụt, KHÔNG phải may mắn thống kê. Cổng này bắt `D-M3-01` ngay
#       từ artifact đầu tiên nếu nó đã tồn tại.
#   (2) THỐNG KÊ (soft, aggregate): |đo − danh nghĩa| > tolerance.
#       ⚠ Ngưỡng 0,02 của luật gốc **KHÔNG áp per-seed được**: với ~250 quyết định,
#       sai số chuẩn lấy mẫu ≈ 0,03 ⇒ cổng 0,02 mỗi seed sẽ bắn liên tục vì NHIỄU.
#       Nó chỉ có nghĩa trên TỔNG nhiều seed. Ghi rõ ở đây để người sau không "sửa"
#       bằng cách nới ngưỡng.
IMPOSSIBLE_ADHERENCE_MIN_DENOM = 20     # dưới mức này thì 1,0/0,0 có thể là may mắn thật


def adherence_audit(result, run_id: str | None = None) -> dict:
    """`decided/followed/adherence` theo KÊNH và theo (kênh × archetype).

    Đọc `projections.adherence_view` — **không** tự cài lại phép đếm (chống lỗi
    "hai nguồn sự thật" mà `D-SIM-09` đã trả giá).

    Trả `{"by_channel": {...}, "by_channel_archetype": {...}, "flags": [...]}`.
    `flags` rỗng = không phát hiện trạng thái bất khả.
    """
    from gsm_core.lifecycle import projections as P

    lifecycle = (P.sim_events_to_lifecycle(result.events, run_id) if run_id
                 else P.sim_events_to_lifecycle(result.events))
    view = P.adherence_view(lifecycle)
    # `N5` (UPDATE-129): `adherence_view` loại quyết định bằng `continue` ⇒ cú loại KHÔNG để lại dấu
    # vết, và cổng dưới đây chỉ kiểm `event_decided == 0 and decided > 0` nên **không thể thấy một
    # khoá VẮNG MẶT**. Nếu producer sinh topic lạ hoặc trộn topic thì mẫu số tụt mà không ai biết —
    # đúng hình dạng `D-M3-01` (số sai sống qua 39 artifact vì không cơ chế nào kêu).
    drops = P.adherence_drops(lifecycle)
    arche = {str(a.actor_id): a.archetype for a in result.actors}

    by_ch: dict[str, dict] = {}
    by_ch_ar: dict[str, dict] = {}
    for (_run, drv, topic), v in view.items():
        if topic is None:
            continue
        for bucket, key in ((by_ch, topic),
                            (by_ch_ar, f"{topic}|{arche.get(str(drv), '?')}")):
            row = bucket.setdefault(key, {"decided": 0, "followed": 0, "dismissed": 0,
                                          "suppressed": 0, "event_decided": 0,
                                          "event_followed": 0})
            for k in row:
                row[k] += int(v.get(k) or 0)

    for bucket in (by_ch, by_ch_ar):
        for row in bucket.values():
            row["decision_adherence"] = (row["followed"] / row["decided"]
                                         if row["decided"] else None)
            row["event_adherence"] = (row["event_followed"] / row["event_decided"]
                                      if row["event_decided"] else None)

    # L3-04 (phản biện 2026-07-31, ĐO ĐƯỢC): `event_adherence` là estimator **LỆCH THEO
    # CẤU TRÚC** ở kênh có HỎI LẠI — tần suất hỏi lại phụ thuộc chính kết cục: người KHÔNG
    # theo bị hỏi lại mỗi tick (mẫu số event phình), người ĐÃ theo thì thôi. Đo seed 5100
    # ladder=all: `accept_lift` decision 0,714 (n=63) vs event 0,524 (n=147) ⇒ **lệch
    # −19,0đp**; ba kênh không-hỏi-lại lệch đúng 0,0đp.
    #
    # Không "sửa" được vì nó đo một thứ khác — nhưng phải GẮN NHÃN, nếu không ai đó sẽ so
    # event_adherence GIỮA các kênh (kênh hỏi lại luôn trông tệ hơn) hoặc trích nó như
    # adherence thật. Với kênh hỏi lại, event_adherence là **chặn DƯỚI**.
    for bucket in (by_ch, by_ch_ar):
        for row in bucket.values():
            row["event_repeat_ratio"] = (row["event_decided"] / row["decided"]
                                         if row["decided"] else None)
            row["event_adherence_is_lower_bound"] = bool(
                row["event_decided"] > row["decided"])

    # SỬA THƯỚC (UPDATE-113): "nghe lời" và "làm được" là HAI câu hỏi. `followed` nay là
    # kết cục COIN tại lúc gán (`projections`); tỷ lệ THI HÀNH tách ra đây. Nó KHÔNG vào
    # cổng adherence (cổng đo tính toàn vẹn của thước, không đo dynamics) — nhưng bản thân
    # nó là một finding đáng báo: coin-true mà không thi hành được là lời khuyên rơi vãi.
    exec_n = sum(1 for e in result.events if e.kind == "standby_followed")
    coin_n = sum(len(e.detail.get("coin_follow_ids") or [])
                 for e in result.events if e.kind == "standby_alloc")
    execution = {"positioning": {"coin_true_n": coin_n, "executed_n": exec_n,
                                 "execution_rate": (exec_n / coin_n) if coin_n else None}}

    # Rà 2026-07-30 (UPDATE-107): cổng BẤT KHẢ phải biết NOMINAL của run. Với arm
    # tuân-thủ-tuyệt-đối (`adherence_by_archetype: 1.0` — chính khái niệm "so thế giới
    # không advisor vs HOÀN TOÀN tuân thủ"), adherence đo được 1,0 là ĐÚNG chứ không
    # bất khả; cổng cũ sẽ TREO oan mọi kênh mọi seed ⇒ arm hợp lệ nhất bị chặn vĩnh
    # viễn ⇒ cổng bị tắt (mẫu D-R20). Bounds tính per-KÊNH từ archetype kênh đó chạm.
    from .advice_bridge import DEFAULT_ADHERENCE
    adv = (getattr(result, "config", None) and result.config.data.get("advice")) or {}
    nominal = {**DEFAULT_ADHERENCE, **(adv.get("adherence_by_archetype") or {})}
    bounds: dict[str, tuple[float, float]] = {}
    for key in by_ch_ar:
        ch, _, ar = key.partition("|")
        p = nominal.get(ar)
        if p is None:
            continue
        lo, hi = bounds.get(ch, (1.0, 0.0))
        bounds[ch] = (min(lo, float(p)), max(hi, float(p)))

    return {"by_channel": by_ch, "by_channel_archetype": by_ch_ar,
            "execution": execution, "drops": drops,
            "flags": adherence_flags(by_ch, channel_nominal_bounds=bounds, drops=drops)}


def adherence_flags(by_channel: dict,
                    channel_nominal_bounds: dict[str, tuple[float, float]] | None = None,
                    drops: dict | None = None) -> list[str]:
    """Cổng BẤT KHẢ (loại 1): trạng thái không thể đúng dù nhiễu thế nào.

    Mỗi flag là một câu nói rõ **cái gì** sai và **vì sao nó bất khả** — để người đọc
    artifact không phải tra cứu. Có flag ⇒ kết quả arm đó phải bị TREO, không phải
    "ghi chú nhỏ".

    `channel_nominal_bounds`: {kênh: (min_p, max_p)} nominal của các archetype kênh đó
    chạm. adherence = 1,0 chỉ BẤT KHẢ khi `max_p < 1.0` (coin còn tính ngẫu nhiên);
    tương tự 0,0 chỉ bất khả khi `min_p > 0.0`. Không có bounds ⇒ giả định coin ngẫu
    nhiên thật (hành vi cũ) — đúng cho mọi config không set nominal cực trị.
    """
    bounds = channel_nominal_bounds or {}
    out: list[str] = []
    for ch, r in sorted(by_channel.items()):
        d, adh = r["decided"], r["decision_adherence"]
        if d == 0:
            out.append(f"{ch}: decided=0 — kênh có event nhưng KHÔNG có quyết định nào "
                       f"vào mẫu số (mẫu số RỖNG, không phải 'thiếu')")
            continue
        if d < IMPOSSIBLE_ADHERENCE_MIN_DENOM:
            continue                      # mẫu số quá nhỏ: 1,0/0,0 có thể là may mắn thật
        min_p, max_p = bounds.get(ch, (0.5, 0.5))   # không bounds ⇒ coi coin ngẫu nhiên
        if adh is not None and adh >= 1.0 and max_p < 1.0:
            out.append(f"{ch}: decision_adherence = 1,000 trên {d} quyết định — BẤT KHẢ với "
                       f"coin ngẫu nhiên (nominal ≤ {max_p:.2f}); dấu hiệu mẫu số chỉ chứa "
                       f"người ĐÃ THEO (D-M3-01)")
        if adh is not None and adh <= 0.0 and min_p > 0.0:
            out.append(f"{ch}: decision_adherence = 0,000 trên {d} quyết định — BẤT KHẢ "
                       f"(nominal ≥ {min_p:.2f}); dấu hiệu tử số không được ghi")
        if r["event_decided"] == 0 and r["decided"] > 0:
            out.append(f"{ch}: event_decided=0 trong khi decided={d} — một nửa bộ đo "
                       f"hai-đơn-vị chết im lặng (event_adherence sẽ là None)")

    # `N5` (UPDATE-129) — cổng cho thứ KHÔNG có mặt trong `by_channel`.
    #
    # Mọi kiểm ở trên soi các khoá ĐANG CÓ. Nhưng `adherence_view` **loại** quyết định có topic
    # chưa khai / trộn topic, nên chúng **vắng mặt** — và một khoá vắng thì không vòng lặp nào ở
    # trên chạm tới được. Đó đúng là hình dạng `D-M3-01`: mẫu số thiếu, mọi số còn lại trông vẫn
    # bình thường. Vì vậy cổng này đọc `adherence_drops()` thay vì đọc `by_channel`.
    #
    # Cường chốt 2026-08-03: topic chưa khai ⇒ **TREO**, không phải chỉ cờ đỏ. Lý do: repo có lịch
    # sử **cảnh báo bị bỏ qua** — `D-M3-01` sống qua 39 artifact vì không ai chặn. Cùng nguyên tắc
    # `D-M3-10`: mẫu số không đầy đủ thì mọi Δ đều đáng ngờ.
    if drops:
        if drops.get("unknown"):
            out.append(
                f"TREO: {drops['unknown']} quyết định bị loại khỏi mẫu số vì topic CHƯA PHÂN LOẠI "
                f"{drops.get('topics_unknown') or ''} — mẫu số KHÔNG đầy đủ nên mọi Δ tính trên nó "
                f"đều đáng ngờ. Khai topic vào `gsm_core.lifecycle.advice_topics` "
                f"(MEASURED_TOPICS nếu là lời khuyên kinh tế, SOFT_TOPICS nếu là khuyên mềm) rồi "
                f"đo lại. ĐỪNG đọc Δ này.")
        if drops.get("mixed"):
            out.append(
                f"TREO: {drops['mixed']} quyết định mang CẢ topic được-đo lẫn topic bị-loại trên "
                f"cùng một `decision_id` — đây là LỖI PRODUCER (không đường ghi nào hôm nay tạo "
                f"được). Cả cụm bị loại (đánh đổi khai ở `projections.adherence_view`), nên mẫu số "
                f"tụt. Tìm producer đang trộn topic trước khi tin bất kỳ số nào.")
        # `drops["soft"]` KHÔNG gắn cờ: đó là ranh giới KHUYÊN MỀM đang chạy ĐÚNG, không phải bất
        # thường. Gắn cờ nó sẽ dạy người đọc bỏ qua cờ — cách nhanh nhất giết một cổng.
    return out


# ---------------------------------------------------------------------------
# D-M3-10 cổng THỐNG KÊ — chốt 2026-07-30 (UPDATE-103 §3, Cường duyệt nguyên tắc):
# kiểm định z Poisson-binomial PHÂN TÍCH, không bootstrap, TREO khi |z| > 4.
#
# Vì sao không bootstrap: ta BIẾT CHÍNH XÁC phân phối null — mỗi quyết định i là
# Bernoulli(p_i) với p_i = adherence danh nghĩa của archetype của CHÍNH tài xế đó.
# Bootstrap resample các quyết định ĐÃ QUAN SÁT nên coi mọi quyết định là trao đổi
# được; công thức đóng thì không — nó tự xử lý HỖN HỢP ARCHETYPE: một kênh chỉ chạm
# P3/P5 (p=0,30) có null là 0,30, không phải trung bình toàn đội.
#
# Vì sao |z| > 4 (DẪN XUẤT, không chọn bừa — UPDATE-103 §3):
#   - lỗi thật D-M3-01 (adherence 1,000 trên 101 QĐ, mu 0,500) cho z = 10 ⇒ biên 2,5×;
#   - "lệch 0,02" của luật cũ là 0,40σ ở n=100 và 2,83σ ở n=5000 ⇒ ngưỡng cố định
#     trên hiệu tuyệt đối không thể đúng ở cả hai đầu — đó là lý do luật cũ chết;
#   - family-wise trên 28 ô (4 kênh × 7 archetype): >3,0 = 7,29% (quá ồn, sẽ bị tắt);
#     >4,0 = 0,18%; >4,5 = 0,02% (chặt hơn mức cần).
# ⚠ ĐỪNG NỚI ngưỡng này khi nó bắn — nó bắn oan 0,18%/lần chạy; nếu nó bắn thì gần
# chắc chắn thước đo hỏng, không phải nhiễu (mẫu D-R20: người sửa nới ngưỡng thay
# vì sửa lỗi).
# ---------------------------------------------------------------------------

ADHERENCE_Z_MAX = 4.0
STAT_GATE_MIN_DENOM = 20      # dưới mức này phương sai ước lượng quá thô — bỏ qua ô


def poisson_binomial_z(followed: int, ps: list[float]) -> float:
    """z của `followed` so với null Poisson-binomial xác định bởi `ps`.

    `ps[i]` = xác suất nghe theo DANH NGHĨA của quyết định i (theo archetype của tài
    xế ra quyết định đó). Điều kiện dùng được công thức đóng: các quyết định độc lập —
    ĐÚNG với coin keyed sha256 (`adherence_coin`): seed nằm trong khoá ⇒ độc lập giữa
    khoá và giữa seed.
    """
    n = len(ps)
    if n == 0:
        return 0.0
    mu = sum(ps)
    var = sum(p * (1.0 - p) for p in ps)
    if var <= 0.0:                # danh nghĩa 0 hoặc 1 tuyệt đối — z vô nghĩa
        return 0.0
    return (float(followed) - mu) / (var ** 0.5)


def adherence_stat_flags(by_channel_archetype: dict, nominal: dict[str, float]) -> list[str]:
    """Cổng THỐNG KÊ trên các ô (kênh × archetype) + tổng hợp theo KÊNH.

    Input đúng dạng `adherence_audit(...)["by_channel_archetype"]` (khoá `"kênh|arche"`).
    `nominal` = adherence danh nghĩa theo archetype (`advice_bridge.DEFAULT_ADHERENCE`).
    Trả list câu TREO — rỗng nghĩa là không ô/kênh nào lệch null quá |z| > 4.
    """
    out: list[str] = []
    per_channel: dict[str, tuple[int, list[float]]] = {}
    for key, row in sorted(by_channel_archetype.items()):
        ch, _, arche = key.partition("|")
        p = nominal.get(arche)
        d, f = int(row.get("decided") or 0), int(row.get("followed") or 0)
        if p is None or d == 0:
            continue                      # archetype lạ: không có null để so — cổng BẤT KHẢ lo phần denom
        fol, ps = per_channel.get(ch, (0, []))
        per_channel[ch] = (fol + f, ps + [p] * d)
        if d < STAT_GATE_MIN_DENOM:
            continue
        z = poisson_binomial_z(f, [p] * d)
        if abs(z) > ADHERENCE_Z_MAX:
            out.append(f"{key}: adherence {f}/{d} = {f / d:.3f} vs danh nghĩa {p:.2f} — "
                       f"z = {z:+.1f} (|z| > {ADHERENCE_Z_MAX:.0f}) ⇒ TREO: thước đo lệch "
                       f"null quá mức nhiễu cho phép")
    for ch, (fol, ps) in sorted(per_channel.items()):
        if len(ps) < STAT_GATE_MIN_DENOM:
            continue
        z = poisson_binomial_z(fol, ps)
        if abs(z) > ADHERENCE_Z_MAX:
            mu = sum(ps) / len(ps)
            out.append(f"{ch} (gộp hỗn hợp archetype): adherence {fol}/{len(ps)} = "
                       f"{fol / len(ps):.3f} vs null Poisson-binomial mu={mu:.3f} — "
                       f"z = {z:+.1f} ⇒ TREO")
    return out

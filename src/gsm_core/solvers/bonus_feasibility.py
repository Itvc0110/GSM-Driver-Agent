"""Solver S1 — BonusFeasibility. Thuần đại số, deterministic.

Bài toán: cho bonus_gap_input → cần thêm bao nhiêu cuốc/giờ để đạt mốc thưởng kế,
FEASIBLE không (đa ràng buộc: điểm ∧ acceptance ∧ completion). Trả SolverReport.
Trả lời US-F0-01, US-F1-03/04. Mọi số có source (traceability=1.0); không bịa số.

AUDIT A1 (UPDATE-065): tốc độ điểm không còn là hằng của bucket tại t_now — solver
ĐI THEO TỪNG GIỜ còn lại trong ngày (S1-2/S1-5), giờ ngoài khung điểm cho 0 điểm
(S1-3), và nhánh đã-đạt-mốc vẫn phải kiểm ràng buộc tỷ lệ (S1-1).
"""

from __future__ import annotations

import math

from gsm_core.policy import PolicyBundle

# 1.5 cuốc/giờ = số ĐO trong repo (configs/pilot_dongda.yaml advice.trips_per_hour_est,
# nhãn "ĐO") — AUDIT S1-4 thay 3.0 không nguồn; fallback này vẫn mang confidence thấp.
DEFAULT_TRIPS_PER_HOUR = 1.5
CLIFF_MARGIN = 0.03           # acceptance trong [ngưỡng, ngưỡng+margin] → cảnh báo cliff
DAY_END_HOUR = 24.0           # walk không vượt quá nửa đêm (ngày sim/ngày policy)


def _hour(iso: str) -> int:
    return int(iso[11:13])


def _minute(iso: str) -> int:
    return int(iso[14:16])


def _num(value, unit, source):
    v = 0.0 if value is None else float(value)
    if math.isinf(v):
        v = -1.0  # sentinel "không đạt được" — schema không nhận Infinity
    return {"value": round(v, 3), "unit": unit, "source": source}


def _hour_rate(policy: PolicyBundle, hist: dict, hour: int,
               scale: float = 1.0) -> tuple[float, float, str | None]:
    """(điểm/giờ, điểm/cuốc, source) cho MỘT giờ đồng hồ — (0, 0, None) ngoài khung điểm."""
    ppt = policy.trip_points(hour)
    if ppt <= 0:
        return 0.0, 0.0, None
    bucket = "peak" if policy.is_peak(hour) else "offpeak"
    # E1b ADV-05 (khớp REVIEW-C9 ở bridge): lịch sử 0.0 điểm/giờ là DỮ LIỆU HỢP LỆ — tài xế
    # từng online khung này mà không có cuốc. Bản cũ `> 0` rơi 0.0 về ước lượng lý thuyết DƯƠNG
    # ⇒ "còn kịp" lạc quan đúng ở những khung tài xế biết rõ là chết. Thiếu khoá / None mới là
    # thiếu dữ liệu.
    if hist.get(bucket) is not None:
        return float(hist[bucket]) * scale, float(ppt), "historical:self"
    return float(ppt) * DEFAULT_TRIPS_PER_HOUR * scale, float(ppt), "dp:policy_theoretical"


def _walk(policy: PolicyBundle, hist: dict, start_h: float, gap: float,
          scale: float = 1.0) -> dict:
    """Đi từng giờ từ `start_h` (giờ thập phân) tới nửa đêm, cộng dồn điểm/cuốc.

    Trả: hours_to_gap (∞ nếu hết ngày chưa đạt), trips_to_gap, sources đã dùng,
    points_possible(budget_h→điểm tối đa kiếm được trong budget đó).
    """
    t = start_h
    pts = 0.0
    trips = 0.0
    hours_to_gap = math.inf
    trips_to_gap: float | None = None
    sources: set[str] = set()
    checkpoints: list[tuple[float, float]] = []  # (giờ đã trôi, điểm cộng dồn)
    while t < DAY_END_HOUR - 1e-9:
        span = min(math.floor(t + 1e-9) + 1, DAY_END_HOUR) - t   # phần còn lại của giờ hiện tại
        rate, ppt, src = _hour_rate(policy, hist, int(t + 1e-9), scale)
        if src:
            sources.add(src)
        if rate > 0 and math.isinf(hours_to_gap) and pts + rate * span >= gap - 1e-9:
            need = (gap - pts) / rate
            hours_to_gap = (t + need) - start_h
            trips_to_gap = trips + (gap - pts) / ppt
        pts += rate * span
        trips += (rate / ppt) * span if ppt > 0 else 0.0
        t += span
        checkpoints.append((t - start_h, pts))
    return {"hours_to_gap": hours_to_gap, "trips_to_gap": trips_to_gap,
            "sources": sources, "checkpoints": checkpoints}


def _points_possible(checkpoints: list[tuple[float, float]], budget_h: float) -> float:
    """Điểm tối đa kiếm được trong `budget_h` giờ đầu của walk (nội suy tuyến tính)."""
    prev_t, prev_p = 0.0, 0.0
    for t, p in checkpoints:
        if budget_h <= t + 1e-9:
            frac = (budget_h - prev_t) / (t - prev_t) if t > prev_t else 0.0
            return prev_p + (p - prev_p) * frac
        prev_t, prev_p = t, p
    return prev_p


def solve(gi: dict, policy: PolicyBundle) -> dict:
    """gi = bonus_gap_input record. Trả solver_report record."""
    points_now = int(gi["points_now"])
    t_now = gi["t_now"]
    start_h = _hour(t_now) + _minute(t_now) / 60.0
    hours_budget = float(gi["hours_budget_remaining"])
    acceptance = float(gi["acceptance_rate"])
    completion = float(gi["completion_rate"])
    hist = gi.get("historical_points_per_hour", {})
    pv = f"policy_v:{policy.version}"

    ok_acc = acceptance >= policy.bonus_min_acceptance
    ok_comp = completion >= policy.bonus_min_completion
    rate_reasons = []
    if not ok_acc:
        rate_reasons.append(f"tỷ lệ nhận {acceptance:.2f} < ngưỡng {policy.bonus_min_acceptance:.2f} "
                            "→ mất toàn bộ thưởng dù đủ điểm")
    if not ok_comp:
        rate_reasons.append(f"tỷ lệ hoàn thành {completion:.2f} < ngưỡng {policy.bonus_min_completion:.2f}")

    inputs_used = [{"view_id": f"bonus_gap_input:{gi['driver_id']}",
                    "version": gi["view_version"], "freshness": t_now}]

    # đã đạt mốc cao nhất? — AUDIT S1-1: vẫn PHẢI kiểm ràng buộc tỷ lệ, nếu không
    # solver báo "có thưởng" trong khi chính sách sẽ trả 0.
    if not gi["next_tiers"]:
        bonus = policy.bonus_at(points_now)
        at_risk = not (ok_acc and ok_comp)
        digest = f"Tài xế {gi['driver_id']}: {points_now}đ — đã đạt mốc thưởng cao nhất."
        if at_risk:
            digest += (" NHƯNG tỷ lệ đang dưới ngưỡng — thưởng sẽ KHÔNG được trả"
                       " nếu giữ nguyên đến cuối ngày.")
        return {
            "schema_version": "1.0.0", "solver": "bonus_feasibility",
            "problem_digest": digest,
            "inputs_used": inputs_used,
            # C2 (UPDATE-076): trả LUÔN `constraints` như nhánh thường. Thiếu nó thì consumer
            # (templates/bridge/UI adapter) biết "không khả thi" nhưng không biết nghẽn ở ĐÂU,
            # nên không nói được với tài xế điều duy nhất còn cứu được.
            "solution": {"already_maxed": True, "feasible": not at_risk, "gap_points": 0,
                         "constraints": {"ok_acceptance": ok_acc, "ok_completion": ok_comp,
                                         "enough_hours": True}},
            "numbers": [_num(bonus, "vnd", pv)],
            "sensitivity": [], "confidence": 0.95 if not at_risk else 0.85,
            "caveats": (["thưởng chỉ được trả khi tỷ lệ nhận/hoàn thành giữ trên ngưỡng đến cuối ngày"]
                        if at_risk else []),
            "infeasible_reason": "; ".join(rate_reasons) if at_risk else None,
        }

    tier_pts, tier_vnd = gi["next_tiers"][0]
    gap_pts = tier_pts - points_now

    # ⭐ P1a (2026-08-07) — PHẦN KIẾM THÊM, không phải TỔNG MỐC.
    #
    # `day_bonus_tiers` là thang **THAY THẾ**, không cộng dồn: `bonus_at` ghi đè
    # `bonus = tier_vnd` chứ không `+=` (`gsm_core/policy.py:104-110`). Nên phần tài xế thật sự
    # đổi được bằng CÔNG SỨC THÊM là `tier_vnd − (đã chốt)`, không phải `tier_vnd`.
    #
    # Trước bản này, tầng sản phẩm đặt `tier_vnd` ngay cạnh *"khoảng X giờ chạy nữa"* ⇒ một tài
    # xế đã chốt mốc 30.000đ đọc *"còn với được 60.000đ — 2 giờ nữa"* và hiểu 2 giờ đó đổi được
    # 60.000đ; sự thật là **30.000đ**. ĐO trên mock (990 lượt, chỉ đội bike):
    # **131/426 thẻ `feasible_gap` = 30,75%**, tổng tiền bị thổi **4.440.000đ**, bội số **2,00×**.
    #
    # ⚠ An toàn của phép trừ: thẻ này CHỈ hiện khi `feasible`, mà
    # `feasible = enough_hours and ok_acc and ok_comp` (dưới) ⇒ tài xế ĐỦ ĐIỀU KIỆN ⇒ `bonus_at`
    # đúng là phần họ **thật sự sẽ nhận**. Với người KHÔNG đủ điều kiện, `day_bonus` trả 0 và
    # thẻ đi nhánh infeasible — nên ở đây không có ca "trừ đi một khoản họ không được nhận".
    bonus_now = int(policy.bonus_at(points_now))
    tier_delta = int(tier_vnd) - bonus_now

    numbers: list[dict] = [_num(gap_pts, "points", pv), _num(tier_vnd, "vnd", pv)]
    if bonus_now > 0:
        # chỉ khai khi KHÁC tổng — tài xế chưa chốt mốc nào thì hai số bằng nhau, thêm một số
        # trùng lặp vào thẻ chỉ làm rối (và làm `numbers` của v2 dài ra vô ích)
        numbers.append(_num(tier_delta, "vnd", pv))

    # AUDIT S1-2/3/5: walk từng giờ còn lại — giờ ngoài khung điểm đóng góp 0
    walk = _walk(policy, hist, start_h, gap_pts)
    hours_needed = walk["hours_to_gap"]
    trips_needed = math.ceil(walk["trips_to_gap"]) if walk["trips_to_gap"] is not None else None
    pts_in_budget = _points_possible(walk["checkpoints"], hours_budget)

    if walk["sources"]:
        rate_source = "+".join(sorted(walk["sources"])) if len(walk["sources"]) > 1 \
            else next(iter(walk["sources"]))
        confidence = 0.85 if walk["sources"] == {"historical:self"} else 0.5
    else:
        rate_source = "dp:policy_theoretical"
        confidence = 0.5
    # rate hiển thị = tốc độ TRUNG BÌNH thực dùng (điểm kiếm được / giờ) trên đoạn tới gap
    # (hoặc trên quỹ giờ nếu không tới) — không còn là hằng của bucket hiện tại
    if not math.isinf(hours_needed) and hours_needed > 0:
        shown_rate = gap_pts / hours_needed
    elif hours_budget > 0:
        shown_rate = pts_in_budget / hours_budget
    else:
        shown_rate = 0.0
    numbers.append(_num(shown_rate, "points_per_hour", rate_source))
    numbers.append(_num(hours_needed, "hours", rate_source))
    if trips_needed is not None:
        numbers.append(_num(trips_needed, "trips", pv))

    enough_hours = hours_needed <= hours_budget + 1e-6
    feasible = enough_hours and ok_acc and ok_comp

    reasons = []
    if not enough_hours:
        if pts_in_budget <= 1e-9:
            reasons.append("quỹ giờ còn lại nằm ngoài khung giờ tính điểm — không kiếm thêm được điểm hôm nay")
        elif math.isinf(hours_needed):
            reasons.append(f"từ giờ đến hết khung điểm chỉ kiếm thêm được ~{walk['checkpoints'][-1][1]:.0f}đ "
                           f"< {gap_pts}đ còn thiếu")
        else:
            reasons.append(f"cần ~{hours_needed:.1f} giờ nhưng quỹ chỉ còn {hours_budget:.1f} giờ")
    reasons.extend(rate_reasons)
    infeasible_reason = None if feasible else "; ".join(reasons)

    # sensitivity — rewalk với rate scale xuống (giữ ngữ nghĩa cũ: −20/40%)
    sensitivity = []
    for pct in (0.20, 0.40):
        w2 = _walk(policy, hist, start_h, gap_pts, scale=1 - pct)
        h2 = w2["hours_to_gap"]
        sensitivity.append({
            "param": f"rate_-{int(pct * 100)}%",
            "new_hours_needed": round(h2, 2) if not math.isinf(h2) else None,
            "flips_feasible": bool(feasible and (math.isinf(h2) or h2 > hours_budget)),
        })
    if len(gi["next_tiers"]) > 1:
        hp, hv = gi["next_tiers"][1]
        wh = _walk(policy, hist, start_h, hp - points_now)
        h_hi = wh["hours_to_gap"]
        sensitivity.append({
            "param": "next_higher_tier",
            "tier_points": hp, "tier_vnd": hv,
            "hours_needed": round(h_hi, 2) if not math.isinf(h_hi) else None,
            "extra_hours_vs_current": (round(h_hi - hours_needed, 2)
                                       if not (math.isinf(h_hi) or math.isinf(hours_needed)) else None),
        })
    if policy.bonus_min_acceptance <= acceptance < policy.bonus_min_acceptance + CLIFF_MARGIN:
        sensitivity.append({
            "param": "acceptance_cliff",
            "note": f"tỷ lệ nhận {acceptance:.2f} sát ngưỡng {policy.bonus_min_acceptance:.2f} — "
                    "vài lần từ chối nữa có thể mất TOÀN BỘ thưởng dù đủ điểm",
        })

    caveats = []
    if "dp:policy_theoretical" in walk["sources"] or not walk["sources"]:
        caveats.append("tốc độ điểm có phần dùng ước lượng lý thuyết (thiếu lịch sử cá nhân) — độ tin thấp")
    caveats.append("số cuốc thực nhận phụ thuộc nhu cầu (demand proxy) — không đảm bảo")

    hours_txt = f"{hours_needed:.1f} giờ" if not math.isinf(hours_needed) else "KHÔNG đạt được trong hôm nay"
    digest = (f"Tài xế {gi['driver_id']}: {points_now}đ, mốc kế {tier_pts}đ "
              f"(thưởng {tier_vnd:,}đ); thiếu {gap_pts}đ ≈ {hours_txt}; "
              f"quỹ {hours_budget:.1f} giờ; nhận {acceptance:.2f}/hoàn thành {completion:.2f}.")

    return {
        "schema_version": "1.0.0", "solver": "bonus_feasibility",
        "problem_digest": digest, "inputs_used": inputs_used,
        "solution": {
            "feasible": feasible, "gap_points": gap_pts,
            "trips_needed": trips_needed,
            "hours_needed": round(hours_needed, 2) if not math.isinf(hours_needed) else None,
            "tier_points": tier_pts, "tier_vnd": tier_vnd,
            # P1a: `tier_vnd` là TÊN/TỔNG của mốc; `tier_delta_vnd` là phần tài xế THẬT SỰ
            # đổi được bằng công sức thêm. Consumer nào đặt số cạnh "chạy thêm X giờ" thì
            # PHẢI dùng `tier_delta_vnd`.
            "bonus_now_vnd": bonus_now, "tier_delta_vnd": tier_delta,
            "constraints": {"enough_hours": enough_hours, "ok_acceptance": ok_acc,
                            "ok_completion": ok_comp},
        },
        "numbers": numbers, "sensitivity": sensitivity,
        "confidence": confidence, "caveats": caveats,
        "infeasible_reason": infeasible_reason,
    }

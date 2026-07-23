"""Solver S1 — BonusFeasibility. Thuần đại số, deterministic.

Bài toán: cho bonus_gap_input → cần thêm bao nhiêu cuốc/giờ để đạt mốc thưởng kế,
FEASIBLE không (đa ràng buộc: điểm ∧ acceptance ∧ completion). Trả SolverReport.
Trả lời US-F0-01, US-F1-03/04. Mọi số có source (traceability=1.0); không bịa số.
"""

from __future__ import annotations

import math

from gsm_core.policy import PolicyBundle

DEFAULT_TRIPS_PER_HOUR = 3.0  # giả định lý thuyết khi thiếu lịch sử (fallback)
CLIFF_MARGIN = 0.03           # acceptance trong [ngưỡng, ngưỡng+margin] → cảnh báo cliff


def _hour(iso: str) -> int:
    return int(iso[11:13])


def _num(value, unit, source):
    return {"value": round(float(value), 3), "unit": unit, "source": source}


def solve(gi: dict, policy: PolicyBundle) -> dict:
    """gi = bonus_gap_input record. Trả solver_report record."""
    points_now = int(gi["points_now"])
    t_now = gi["t_now"]
    hour = _hour(t_now)
    bucket = "peak" if policy.is_peak(hour) else "offpeak"
    hours_budget = float(gi["hours_budget_remaining"])
    acceptance = float(gi["acceptance_rate"])
    completion = float(gi["completion_rate"])
    hist = gi.get("historical_points_per_hour", {})
    pv = f"policy_v:{policy.version}"

    numbers: list[dict] = []
    inputs_used = [{"view_id": f"bonus_gap_input:{gi['driver_id']}",
                    "version": gi["view_version"], "freshness": t_now}]

    # đã đạt mốc cao nhất?
    if not gi["next_tiers"]:
        return {
            "schema_version": "1.0.0", "solver": "bonus_feasibility",
            "problem_digest": f"Tài xế {gi['driver_id']}: {points_now}đ — đã đạt mốc thưởng cao nhất.",
            "inputs_used": inputs_used,
            "solution": {"already_maxed": True, "feasible": True, "gap_points": 0},
            "numbers": [_num(policy.bonus_at(points_now), "vnd", pv)],
            "sensitivity": [], "confidence": 0.95, "caveats": [], "infeasible_reason": None,
        }

    tier_pts, tier_vnd = gi["next_tiers"][0]
    gap_pts = tier_pts - points_now
    numbers.append(_num(gap_pts, "points", pv))
    numbers.append(_num(tier_vnd, "vnd", pv))

    # rate điểm/giờ: historical cá nhân (nếu có) else policy_theoretical
    if bucket in hist and hist[bucket] > 0:
        rate = float(hist[bucket])
        rate_source = "historical:self"
        confidence = 0.85
    else:
        rate = policy.points_per_trip_estimate(hour) * DEFAULT_TRIPS_PER_HOUR
        rate_source = "dp:policy_theoretical"
        confidence = 0.5
    numbers.append(_num(rate, "points_per_hour", rate_source))

    ppt = policy.points_per_trip_estimate(hour)
    hours_needed = gap_pts / rate if rate > 0 else math.inf
    trips_needed = math.ceil(gap_pts / ppt) if ppt > 0 else None
    numbers.append(_num(hours_needed, "hours", rate_source))
    if trips_needed is not None:
        numbers.append(_num(trips_needed, "trips", pv))

    # feasibility đa ràng buộc (tolerance nhỏ để biên float không lật ngẫu nhiên)
    enough_hours = hours_needed <= hours_budget + 1e-6
    ok_acc = acceptance >= policy.bonus_min_acceptance
    ok_comp = completion >= policy.bonus_min_completion
    feasible = enough_hours and ok_acc and ok_comp

    reasons = []
    if not enough_hours:
        reasons.append(f"cần ~{hours_needed:.1f} giờ nhưng quỹ chỉ còn {hours_budget:.1f} giờ")
    if not ok_acc:
        reasons.append(f"tỷ lệ nhận {acceptance:.2f} < ngưỡng {policy.bonus_min_acceptance:.2f} "
                       "→ mất toàn bộ thưởng dù đủ điểm")
    if not ok_comp:
        reasons.append(f"tỷ lệ hoàn thành {completion:.2f} < ngưỡng {policy.bonus_min_completion:.2f}")
    infeasible_reason = None if feasible else "; ".join(reasons)

    # sensitivity
    sensitivity = []
    for pct in (0.20, 0.40):
        r2 = rate * (1 - pct)
        h2 = gap_pts / r2 if r2 > 0 else math.inf
        sensitivity.append({
            "param": f"rate_-{int(pct * 100)}%",
            "new_hours_needed": round(h2, 2),
            "flips_feasible": bool(feasible and h2 > hours_budget),
        })
    # mốc cao hơn kế tiếp — chi phí biên
    if len(gi["next_tiers"]) > 1:
        hp, hv = gi["next_tiers"][1]
        h_hi = (hp - points_now) / rate if rate > 0 else math.inf
        sensitivity.append({
            "param": "next_higher_tier",
            "tier_points": hp, "tier_vnd": hv,
            "hours_needed": round(h_hi, 2),
            "extra_hours_vs_current": round(h_hi - hours_needed, 2),
        })
    # acceptance cliff
    if policy.bonus_min_acceptance <= acceptance < policy.bonus_min_acceptance + CLIFF_MARGIN:
        sensitivity.append({
            "param": "acceptance_cliff",
            "note": f"tỷ lệ nhận {acceptance:.2f} sát ngưỡng {policy.bonus_min_acceptance:.2f} — "
                    "vài lần từ chối nữa có thể mất TOÀN BỘ thưởng dù đủ điểm",
        })

    caveats = []
    if rate_source.startswith("dp:"):
        caveats.append("tốc độ điểm dùng ước lượng lý thuyết (thiếu lịch sử cá nhân) — độ tin thấp")
    caveats.append("số cuốc thực nhận phụ thuộc nhu cầu (demand proxy) — không đảm bảo")

    digest = (f"Tài xế {gi['driver_id']}: {points_now}đ, mốc kế {tier_pts}đ "
              f"(thưởng {tier_vnd:,}đ); thiếu {gap_pts}đ ≈ {hours_needed:.1f} giờ; "
              f"quỹ {hours_budget:.1f} giờ; nhận {acceptance:.2f}/hoàn thành {completion:.2f}.")

    return {
        "schema_version": "1.0.0", "solver": "bonus_feasibility",
        "problem_digest": digest, "inputs_used": inputs_used,
        "solution": {
            "feasible": feasible, "gap_points": gap_pts,
            "trips_needed": trips_needed, "hours_needed": round(hours_needed, 2),
            "tier_points": tier_pts, "tier_vnd": tier_vnd,
            "constraints": {"enough_hours": enough_hours, "ok_acceptance": ok_acc,
                            "ok_completion": ok_comp},
        },
        "numbers": numbers, "sensitivity": sensitivity,
        "confidence": confidence, "caveats": caveats,
        "infeasible_reason": infeasible_reason,
    }

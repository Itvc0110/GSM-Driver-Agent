"""Solver S5 — WeeklyKhoanFeasibility. Thuần đại số, deterministic.

Bài toán (Vận Doanh 23/02/2026): tuần này còn thiếu bao nhiêu DOANH SỐ để đạt khoán,
nếu không đạt thì bị **truy thu** (clawback) bao nhiêu, và có KHẢ THI trong quỹ giờ
còn lại không. Trả lời UC3/UC4 (US-F1, US-F3).

BẤT BIẾN §5: **KHÔNG bịa số policy.** Nếu policy chưa có số khoán (`quota=None` —
image-locked, TBC-với-GSM) thì solver báo `quota_available=False` và CHỈ trả số ĐO
ĐƯỢC; tuyệt đối không đoán mốc khoán.

money_basis: `gross` (doanh số = total_fee) theo quyết định (d) 2026-07-24 — ASSUMPTION
chờ GSM xác nhận; ghi vào `source` của mỗi số để truy vết.
"""

from __future__ import annotations

import math

from gsm_core.policy import PolicyBundle
from gsm_core.vn_format import format_vnd

SOLVER = "weekly_khoan"


def _num(value, unit, source):
    return {"value": round(float(value), 3), "unit": unit, "source": source}


def solve(wi: dict, policy: PolicyBundle) -> dict:
    """wi = weekly_khoan_input record. Trả solver_report record."""
    drv = wi["driver_id"]
    revenue = int(wi["revenue_so_far_vnd"])
    days_active = int(wi["days_active"])
    days_remaining = int(wi["days_remaining"])
    hours_budget = float(wi.get("hours_budget_remaining") or 0.0)
    rate = wi.get("avg_revenue_per_hour")
    basis = wi.get("money_basis", "gross")
    pv = f"policy_v:{policy.version}|basis={basis}"
    measured = f"ledger:income_daily|basis={basis}"

    inputs_used = [{"view_id": f"weekly_khoan_input:{drv}",
                    "version": wi["view_version"], "freshness": wi["t_now"]}]
    numbers = [_num(revenue, "vnd", measured)]
    if rate:
        numbers.append(_num(rate, "vnd_per_hour", "historical:self"))

    quota = wi.get("quota") or {}
    quota_min = quota.get("min_revenue_vnd")

    # ---- Không có số khoán từ policy → KHÔNG đoán (§5) ----
    if quota_min is None:
        return {
            "schema_version": "1.0.0", "solver": SOLVER,
            "problem_digest": (f"Tài xế {drv} tuần {wi['week_key']}: doanh số {format_vnd(revenue)}, "
                               f"{days_active} ngày hoạt động. CHƯA có mốc khoán tuần trong "
                               "policy → không thể tính khoảng thiếu/truy thu."),
            "inputs_used": inputs_used,
            "solution": {"quota_available": False, "feasible": None,
                         "revenue_so_far_vnd": revenue, "days_active": days_active},
            "numbers": numbers, "sensitivity": [],
            "confidence": 0.3,
            "caveats": ["Thiếu số khoán tuần trong policy bundle (TBC-với-GSM) — "
                        "solver không suy đoán mốc; cần số chính thức từ GSM."],
            "infeasible_reason": "thiếu số khoán tuần từ policy (TBC-với-GSM)",
        }

    # ---- Có quota → tính gap + clawback ----
    quota_min = int(quota_min)
    clawback_rate = quota.get("clawback_rate")
    min_days = quota.get("min_active_days")
    numbers.append(_num(quota_min, "vnd", pv))

    gap = max(0, quota_min - revenue)
    numbers.append(_num(gap, "vnd", pv))

    clawback = int(round(gap * float(clawback_rate))) if (gap > 0 and clawback_rate) else 0
    if clawback_rate is not None:
        numbers.append(_num(clawback, "vnd", pv))

    if gap == 0:
        hours_needed = 0.0
    elif rate:
        hours_needed = gap / float(rate)
    else:
        hours_needed = math.inf
    if math.isfinite(hours_needed):
        numbers.append(_num(hours_needed, "hours", "historical:self" if rate else pv))

    enough_hours = math.isfinite(hours_needed) and hours_needed <= hours_budget + 1e-6
    days_ok = True if min_days is None else (days_active + days_remaining >= int(min_days))
    feasible = bool(gap == 0 or (enough_hours and days_ok))

    reasons = []
    if gap > 0 and not math.isfinite(hours_needed):
        reasons.append("chưa đủ lịch sử để ước tốc độ doanh số/giờ")
    elif gap > 0 and not enough_hours:
        reasons.append(f"cần ~{hours_needed:.1f} giờ nhưng quỹ tuần còn {hours_budget:.1f} giờ")
    if not days_ok:
        reasons.append(f"số ngày hoạt động tối đa đạt {days_active + days_remaining} "
                       f"< yêu cầu {min_days} ngày")
    infeasible_reason = None if feasible else "; ".join(reasons)

    sensitivity = []
    if gap > 0 and rate:
        for pct in (0.20, 0.40):
            r2 = float(rate) * (1 - pct)
            h2 = gap / r2 if r2 > 0 else math.inf
            sensitivity.append({"param": f"rate_-{int(pct * 100)}%",
                                "new_hours_needed": round(h2, 2),
                                "flips_feasible": bool(feasible and h2 > hours_budget)})
    if min_days is not None:
        sensitivity.append({"param": "min_active_days",
                            "days_active": days_active, "days_remaining": days_remaining,
                            "required": int(min_days), "satisfied": days_ok})

    caveats = [f"Khoán tính trên {basis} (doanh số) — ASSUMPTION chờ GSM xác nhận định nghĩa.",
               "Doanh số thực tế phụ thuộc nhu cầu — không đảm bảo."]
    if not rate:
        caveats.append("Thiếu lịch sử doanh số/giờ → không ước được số giờ cần.")

    digest = (f"Tài xế {drv} tuần {wi['week_key']}: doanh số {format_vnd(revenue)}/{format_vnd(quota_min)} khoán"
              + (f", thiếu {format_vnd(gap)}" if gap else " — ĐÃ ĐẠT")
              + (f" (≈{hours_needed:.1f} giờ)" if gap and math.isfinite(hours_needed) else "")
              + (f"; rủi ro truy thu {format_vnd(clawback)}" if clawback else "")
              + f"; {days_active} ngày hoạt động, còn {days_remaining} ngày.")

    return {
        "schema_version": "1.0.0", "solver": SOLVER,
        "problem_digest": digest, "inputs_used": inputs_used,
        "solution": {
            "quota_available": True, "feasible": feasible,
            "revenue_so_far_vnd": revenue, "quota_vnd": quota_min,
            "gap_revenue_vnd": gap, "clawback_risk_vnd": clawback,
            "hours_needed": None if not math.isfinite(hours_needed) else round(hours_needed, 2),
            "days_active": days_active, "days_remaining": days_remaining,
            "constraints": {"enough_hours": enough_hours, "ok_active_days": days_ok},
            "money_basis": basis,
        },
        "numbers": numbers, "sensitivity": sensitivity,
        "confidence": 0.8 if rate else 0.5,
        "caveats": caveats, "infeasible_reason": infeasible_reason,
    }

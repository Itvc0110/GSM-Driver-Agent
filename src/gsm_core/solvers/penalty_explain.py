"""Solver S8 — PenaltyExplain (UC6). Rule thuần, deterministic.

Bài toán: giải thích **vì sao bị trừ tiền / vì sao hiệu suất thấp** và **cách tuân thủ**
để kỳ sau không bị trừ nữa.

GUARDRAIL (CLAUDE.md §5):
  - **KHÔNG DẠY LÁCH**: chỉ nêu QUY TẮC + cách ĐẠT quy tắc. Tuyệt đối không gợi ý mẹo
    né phạt, không nêu ngưỡng/cách phát hiện của hệ thống.
  - **KHÔNG PHÁN XÉT**: nêu sự kiện + khoảng cách tới ngưỡng, không trách móc
    (research `pain-points`: tài xế đã thấy "bị phạt như nhân viên").
  - Số tiền trừ TỪ `driver_penalization_ATA` (đo được); ngưỡng TỪ `policy_bundle`.
    Không có khoản trừ → KHÔNG bịa rủi ro.
"""

from __future__ import annotations

from gsm_core.vn_format import format_vnd

SOLVER = "penalty_explain"

# nhãn tiếng Việt cho từng loại khoản trừ + quy tắc liên quan (giải thích, không né)
_TYPE_VN = {
    "clawback_khoan": ("truy thu do chưa đạt khoán tuần",
                       "đạt doanh số khoán tuần theo chính sách"),
    "conduct": ("trừ theo bộ quy tắc ứng xử", "tuân thủ bộ quy tắc ứng xử"),
    "late": ("trừ do trễ", "đến đón đúng giờ hơn"),
    "acceptance": ("trừ liên quan tỷ lệ nhận chuyến",
                   "giữ tỷ lệ nhận chuyến ở mức chính sách yêu cầu"),
    "other": ("khoản trừ khác", "xem chi tiết trong app hoặc liên hệ hỗ trợ"),
}
CLIFF_MARGIN = 0.03  # sát ngưỡng


def _num(value, unit, source):
    return {"value": round(float(value), 3), "unit": unit, "source": source}


def solve(pi: dict) -> dict:
    drv = pi["driver_id"]
    pens = [p for p in (pi.get("penalties") or []) if p.get("status") != "waived"]
    rates = pi.get("rates") or {}
    th = pi.get("thresholds") or {}
    khoan_gap = pi.get("khoan_gap_vnd")

    inputs_used = [{"view_id": f"penalty_explain_input:{drv}",
                    "version": pi["view_version"], "freshness": pi["t_now"]}]
    numbers, breakdown = [], {}
    total = 0
    for p in pens:
        amt = int(p["amount_vnd"])
        total += amt
        breakdown[p["penalty_type"]] = breakdown.get(p["penalty_type"], 0) + amt
        numbers.append(_num(amt, "vnd", f"penalization:{p['penalization_id']}"))
    if total:
        numbers.append(_num(total, "vnd", "penalization:total"))

    # rủi ro: metric đang DƯỚI hoặc SÁT ngưỡng chính sách (nêu khoảng cách cần cải thiện)
    risks = []
    for key, th_key, label in (("acceptance", "min_acceptance", "tỷ lệ nhận chuyến"),
                               ("fulfillment", "min_completion", "tỷ lệ hoàn thành")):
        val, lim = rates.get(key), th.get(th_key)
        if val is None or lim is None:
            continue
        numbers.append(_num(val, "ratio", "statistic_daily:measured"))
        if val < lim:
            risks.append({"metric": label, "value": val, "threshold": lim, "state": "below",
                          "gap": round(lim - val, 4)})
            numbers.append(_num(lim, "ratio", "policy_v:threshold"))
        elif val < lim + CLIFF_MARGIN:
            risks.append({"metric": label, "value": val, "threshold": lim, "state": "near",
                          "gap": round(val - lim, 4)})

    # Quyền giải trình trực tuyến (official 15/12/2025): BẮT BUỘC trong 48 GIỜ với cuốc
    # bị nghi vấn; quá hạn ảnh hưởng tài khoản. Chỉ NHẮC quyền + hạn — không xây quy
    # trình khiếu nại (D-007 = dự án khác).
    caveats = ["Số liệu lấy từ bản ghi của hệ thống; nếu anh/chị thấy chưa đúng, "
               "liên hệ bộ phận hỗ trợ để được rà soát.",
               "Với cuốc bị nghi vấn vi phạm, anh/chị có quyền GIẢI TRÌNH TRỰC TUYẾN trên "
               "app — hạn 48 giờ kể từ khi có thông báo.",
               "Thông tin mang tính giải thích quy định, không phải tư vấn pháp lý."]

    # KHÔNG có khoản trừ và KHÔNG có rủi ro → không bịa vấn đề
    if not pens and not risks:
        return {
            "schema_version": "1.0.0", "solver": SOLVER,
            "problem_digest": (f"Tài xế {drv}: kỳ này không ghi nhận khoản trừ nào và các "
                               "chỉ số đang đạt yêu cầu chính sách."),
            "inputs_used": inputs_used,
            "solution": {"notable": False, "total_deducted_vnd": 0, "breakdown": {},
                          "risks": [], "actions": []},
            "numbers": numbers, "sensitivity": [], "confidence": 0.8,
            "caveats": caveats, "infeasible_reason": None,
        }

    # hành động TUÂN THỦ (không phải mẹo né)
    actions = []
    for t in breakdown:
        _, how = _TYPE_VN.get(t, _TYPE_VN["other"])
        if how not in actions:
            actions.append(how)
    for r in risks:
        actions.append(f"nâng {r['metric']} lên mức tối thiểu {r['threshold']:.0%}")
    if khoan_gap:
        numbers.append(_num(khoan_gap, "vnd", "policy_v:weekly_quota"))
        actions.append("hoàn thành phần doanh số khoán tuần còn thiếu")

    parts = []
    if pens:
        detail = "; ".join(f"{_TYPE_VN.get(t, _TYPE_VN['other'])[0]}: {format_vnd(amt)}"
                           for t, amt in sorted(breakdown.items()))
        parts.append(f"kỳ này ghi nhận {len(pens)} khoản trừ, tổng {format_vnd(total)} ({detail})")
    for r in risks:
        state = "đang dưới" if r["state"] == "below" else "đang sát"
        parts.append(f"{r['metric']} {r['value']:.0%} {state} mức tối thiểu "
                     f"{r['threshold']:.0%} theo chính sách")
    digest = f"Tài xế {drv}: " + "; ".join(parts) + "."
    if actions:
        digest += " Cách cải thiện: " + ", ".join(actions[:3]) + "."

    return {
        "schema_version": "1.0.0", "solver": SOLVER,
        "problem_digest": digest, "inputs_used": inputs_used,
        "solution": {
            "notable": True, "total_deducted_vnd": total, "breakdown": breakdown,
            "penalty_count": len(pens), "risks": risks, "actions": actions,
        },
        "numbers": numbers,
        "sensitivity": [{"param": "threshold_margin", "cliff_margin": CLIFF_MARGIN}],
        "confidence": 0.8, "caveats": caveats, "infeasible_reason": None,
    }

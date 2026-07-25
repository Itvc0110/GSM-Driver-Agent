"""Solver S6 — MissionKnapsack. 0/1 knapsack DP, deterministic, TỐI ƯU chính xác.

Bài toán (UC8 mini-task): chọn tập nhiệm vụ để **tối đa tổng thưởng** trong quỹ giờ
còn lại. Chi phí mỗi mission = `remaining_count / trips_per_hour` (ASSUMPTION: effort
tuyến tính theo số cuốc). Giá trị = `reward_vnd` LẤY TỪ `mission_catalog` (không bịa).

DP trên quỹ giờ RỜI RẠC (slot 15 phút) → tối ưu chính xác trong lưới đó (test đối
chiếu brute-force). Tie-break theo `mission_id` → deterministic.

Guardrail §5: chỉ gợi ý mini-task; KHÔNG hứa thu nhập (reward là điều kiện policy,
vẫn phụ thuộc hoàn thành), KHÔNG khuyên nhận/từ chối đơn cụ thể.
"""

from __future__ import annotations

SOLVER = "mission_knapsack"
SLOT_MIN = 15  # lưới thời gian rời rạc


def _num(value, unit, source):
    return {"value": round(float(value), 3), "unit": unit, "source": source}


def _slots(hours: float) -> int:
    return int(round(hours * 60 / SLOT_MIN))


def solve(mi: dict) -> dict:
    """mi = mission_select_input record. Trả solver_report record."""
    drv = mi["driver_id"]
    tph = float(mi["trips_per_hour"])
    budget_h = float(mi["hours_budget_remaining"])
    cap = _slots(budget_h)
    src = "mission_catalog"

    inputs_used = [{"view_id": f"mission_select_input:{drv}",
                    "version": mi["view_version"], "freshness": mi["t_now"]}]

    # chuẩn hoá item + loại mission không khả thi
    items, skipped = [], []
    for m in sorted(mi["missions"], key=lambda x: x["mission_id"]):
        reward = int(m["reward_vnd"])
        remaining = int(m["remaining_count"])
        cost_h = remaining / tph
        cost = _slots(cost_h)
        if remaining <= 0:
            skipped.append({"mission_id": m["mission_id"], "reason": "đã đủ tiến độ"})
            continue
        if reward <= 0:
            skipped.append({"mission_id": m["mission_id"], "reason": "không có thưởng VND"})
            continue
        if cost > cap:
            skipped.append({"mission_id": m["mission_id"],
                            "reason": f"cần ~{cost_h:.1f} giờ > quỹ {budget_h:.1f} giờ"})
            continue
        items.append({"mission_id": m["mission_id"], "name": m.get("name"),
                      "reward": reward, "cost": cost, "cost_hours": round(cost_h, 2),
                      "remaining_count": remaining})

    # ---- 0/1 knapsack DP ----
    n = len(items)
    dp = [[0] * (cap + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        it = items[i - 1]
        c, v = it["cost"], it["reward"]
        row, prev = dp[i], dp[i - 1]
        for w in range(cap + 1):
            best = prev[w]
            if c <= w:
                alt = prev[w - c] + v
                if alt > best:
                    best = alt
            row[w] = best
    # truy vết (ưu tiên KHÔNG chọn khi hoà → tie-break ổn định)
    chosen, w = [], cap
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            it = items[i - 1]
            chosen.append(it)
            w -= it["cost"]
    chosen.reverse()

    total_reward = sum(it["reward"] for it in chosen)
    hours_used = round(sum(it["cost"] for it in chosen) * SLOT_MIN / 60, 2)

    numbers = [_num(total_reward, "vnd", src)]
    for it in chosen:
        numbers.append(_num(it["reward"], "vnd", f"{src}:{it['mission_id']}"))
    if chosen:
        numbers.append(_num(hours_used, "hours", "historical:self"))

    if chosen:
        names = ", ".join(f"{it['name'] or it['mission_id']} (còn {it['remaining_count']} cuốc)"
                          for it in chosen)
        digest = (f"Tài xế {drv}: chọn {len(chosen)} nhiệm vụ — {names}; "
                  f"tổng thưởng {total_reward:,}đ, ước {hours_used:.1f}/{budget_h:.1f} giờ.")
    else:
        digest = (f"Tài xế {drv}: không nhiệm vụ nào khả thi trong quỹ {budget_h:.1f} giờ "
                  f"({len(skipped)} nhiệm vụ bị loại).")

    # sensitivity: quỹ giờ ±, và mission cận biên
    sensitivity = []
    for extra in (1.0, 2.0):
        cap2 = _slots(budget_h + extra)
        if cap2 > cap and n:
            dp2 = [0] * (cap2 + 1)
            for it in items:
                c, v = it["cost"], it["reward"]
                for w in range(cap2, c - 1, -1):
                    dp2[w] = max(dp2[w], dp2[w - c] + v)
            gain = dp2[cap2] - total_reward
            if gain > 0:
                sensitivity.append({"param": f"hours_+{extra:g}",
                                    "extra_reward_vnd": gain,
                                    "note": "thêm giờ mở thêm nhiệm vụ"})

    caveats = ["Ước giờ theo tốc độ cuốc lịch sử (ASSUMPTION tuyến tính) — thực tế phụ thuộc nhu cầu.",
               "Thưởng chỉ nhận khi hoàn thành đủ điều kiện nhiệm vụ theo chính sách."]

    return {
        "schema_version": "1.0.0", "solver": SOLVER,
        "problem_digest": digest, "inputs_used": inputs_used,
        "solution": {
            "chosen_missions": [{"mission_id": it["mission_id"], "name": it["name"],
                                  "reward_vnd": it["reward"], "cost_hours": it["cost_hours"],
                                  "remaining_count": it["remaining_count"]} for it in chosen],
            "expected_reward_vnd": total_reward, "hours_used": hours_used,
            "hours_budget": budget_h, "skipped": skipped,
            "feasible": bool(chosen),
        },
        "numbers": numbers, "sensitivity": sensitivity,
        "confidence": 0.75 if chosen else 0.6,
        "caveats": caveats,
        "infeasible_reason": None if chosen else "không nhiệm vụ nào vừa quỹ giờ còn lại",
    }

"""Solver S3 — F3Patterns. Phát hiện hành vi chưa tối ưu sau ca (rule/stat thuần).

4 pattern: sạc/nghỉ giờ cao điểm, acceptance cliff, thiếu tiến độ mốc, idle giờ cao.
Mỗi pattern TÁCH: observed (đo được) + severity ordinal + heuristic_note (KHÔNG số
loss tuyệt đối — §5: không bịa số tài chính). US-F3-01/02/03. Không phán xét từng cuốc.
"""

from __future__ import annotations

from gsm_core.policy import PolicyBundle

SEVERITY_ORDER = {"HIGH": 3, "MED": 2, "LOW": 1}
DEFAULT = {
    "cliff_margin": 0.03,        # acceptance trong [min, min+margin] → cliff
    "bonus_gap_max_points": 30,  # thiếu ≤ này mới cảnh báo "gần mốc"
    "idle_min_dur": 25,          # idle_wait ≥ này giờ cao điểm → pattern
    "rest_min_dur": 20,
}


def _hour(iso: str) -> int:
    return int(iso[11:13])


def _dur_min(a: dict) -> float:
    return (_hour(a["t_end"]) * 60 + int(a["t_end"][14:16])
            - _hour(a["t_start"]) * 60 - int(a["t_start"][14:16]))


def _num(value, unit, source):
    return {"value": round(float(value), 3), "unit": unit, "source": source}


def solve(ss: dict, policy: PolicyBundle, params: dict | None = None) -> dict:
    p = {**DEFAULT, **(params or {})}
    pv = f"policy_v:{policy.version}"
    peak = policy.point_peak_hours
    dse = ss["day_state_end"]
    points_end = int(dse.get("points", 0))
    acceptance = float(dse.get("acceptance_rate", 1.0))
    completion = float(dse.get("completion_rate", 1.0))
    inferred = ss.get("inferred_activities", [])

    patterns: list[dict] = []
    numbers: list[dict] = []

    # 1. charge_rest_peak — sạc/nghỉ trong giờ cao điểm (từ L2i INFERRED)
    for a in inferred:
        if a["label"] not in ("charging_likely", "rest_likely"):
            continue
        h = _hour(a["t_start"])
        if h not in peak:
            continue
        dur = _dur_min(a)
        if a["label"] == "rest_likely" and dur < p["rest_min_dur"]:
            continue
        sev = "HIGH" if dur >= 40 else "MED"
        kind = "sạc/đổi pin" if a["label"] == "charging_likely" else "nghỉ"
        patterns.append({
            "type": "charge_rest_peak",
            "observed": {"activity": a["label"], "hour": h, "duration_min": round(dur),
                         "inferred": True, "confidence": a.get("confidence")},
            "severity": sev, "us_ref": "US-F3-02", "label": "HEURISTIC",
            "heuristic_note": (f"{kind} ~{dur:.0f} phút lúc {h:02d}h (khung điểm cao) — "
                               "có thể bỏ lỡ điểm/cuốc giờ vàng. Ước lượng định tính, "
                               "không phải số tiền chắc chắn."),
        })
        numbers.append(_num(dur, "minutes", "observed:inferred_activity"))
        numbers.append(_num(h, "hour", "observed:inferred_activity"))

    # 2. acceptance_cliff — tỷ lệ nhận sát ngưỡng (observable thuần)
    if acceptance < 0.5:
        patterns.append({
            "type": "acceptance_cliff",
            "observed": {"acceptance_rate": acceptance, "threshold_forced": 0.5},
            "severity": "HIGH", "us_ref": "US-F3-02", "label": "OBSERVED",
            "heuristic_note": (f"tỷ lệ nhận {acceptance:.2f} < 0.5 — hệ thống có thể ép "
                               "auto-accept; cân nhắc nhận nhiều hơn ca sau."),
        })
        numbers.append(_num(acceptance, "ratio", "observed:day_state_end"))
    elif policy.bonus_min_acceptance <= acceptance < policy.bonus_min_acceptance + p["cliff_margin"]:
        patterns.append({
            "type": "acceptance_cliff",
            "observed": {"acceptance_rate": acceptance,
                         "threshold_bonus": policy.bonus_min_acceptance},
            "severity": "MED", "us_ref": "US-F3-02", "label": "OBSERVED",
            "heuristic_note": (f"tỷ lệ nhận {acceptance:.2f} sát ngưỡng thưởng "
                               f"{policy.bonus_min_acceptance:.2f} — vài lần từ chối nữa "
                               "có thể mất toàn bộ thưởng ngày dù đủ điểm."),
        })
        numbers.append(_num(acceptance, "ratio", "observed:day_state_end"))
        numbers.append(_num(policy.bonus_min_acceptance, "ratio", pv))

    # 3. bonus_progress_gap — thiếu ít điểm đã bỏ lỡ mốc (nối S1)
    gap = policy.next_tier_gap(points_end)
    if gap is not None and gap[0] <= p["bonus_gap_max_points"]:
        gap_pts, tier_vnd = gap
        # ⭐ P1a (2026-08-07) — CÙNG lỗi ngữ nghĩa với đường v1, sửa luôn cho khỏi tái sinh.
        #
        # `day_bonus_tiers` là thang **THAY THẾ** (`bonus_at` ghi đè, không `+=`) ⇒ với người đã
        # chốt một mốc, `tier_vnd` là **TÊN mốc**, không phải phần đổi được bằng công sức thêm.
        # Câu dưới đặt số ngay cạnh *"chạy thêm ít cuốc là chốt được"* ⇒ dùng TỔNG là hứa gấp đôi.
        # Trên đường v1 lỗi này chiếm **131/426 thẻ = 30,75%** (`UPDATE-183`).
        # ⚠ S3 hiện **0 caller sản phẩm** — sửa ở đây là **phòng ngừa**, không phải vá bán kính.
        tang_them = int(tier_vnd) - int(policy.bonus_at(points_end))
        patterns.append({
            "type": "bonus_progress_gap",
            "observed": {"points_end": points_end, "gap_points": gap_pts},
            "severity": "MED" if gap_pts <= 15 else "LOW", "us_ref": "US-F3-02",
            "label": "OBSERVED",
            "heuristic_note": (f"kết ca với {points_end}đ — chỉ thiếu {gap_pts}đ nữa là đạt "
                               f"mốc thưởng {tier_vnd:,}đ (được thêm {tang_them:,}đ so với mức "
                               f"đã chốt). Ca sau chạy thêm ít cuốc là chốt được."),
        })
        numbers.append(_num(points_end, "points", "observed:day_state_end"))
        numbers.append(_num(gap_pts, "points", "observed:day_state_end"))
        numbers.append(_num(tier_vnd, "vnd", pv))
        if tang_them != int(tier_vnd):
            numbers.append(_num(tang_them, "vnd", pv))

    # 4. idle_peak — idle dài giờ cao điểm (cảnh báo, KHÔNG chỉ vùng — ranh giới F2-04)
    for a in inferred:
        if a["label"] != "idle_wait":
            continue
        h = _hour(a["t_start"])
        dur = _dur_min(a)
        if h in peak and dur >= p["idle_min_dur"]:
            patterns.append({
                "type": "idle_peak",
                "observed": {"hour": h, "duration_min": round(dur), "inferred": True},
                "severity": "MED", "us_ref": "US-F2-02", "label": "HEURISTIC",
                "heuristic_note": (f"đứng chờ ~{dur:.0f} phút lúc {h:02d}h (giờ cao điểm) — "
                                   "cân nhắc chủ động hơn. Không chỉ định khu vực cụ thể."),
            })
            numbers.append(_num(dur, "minutes", "observed:inferred_activity"))

    patterns.sort(key=lambda x: SEVERITY_ORDER[x["severity"]], reverse=True)
    top = patterns[0] if patterns else None

    pb = ss["payout_breakdown"]
    numbers.append(_num(pb["gross_vnd"], "vnd", "session:payout_breakdown"))
    numbers.append(_num(pb["driver_payout_vnd"], "vnd", "session:payout_breakdown"))

    n = len(patterns)
    if n == 0:
        digest = f"Tài xế {ss['driver_id']} ca {ss['session_date']}: không phát hiện pattern chưa tối ưu rõ rệt."
    else:
        digest = (f"Tài xế {ss['driver_id']} ca {ss['session_date']}: {n} pattern chưa tối ưu; "
                  f"nổi bật — {top['heuristic_note'][:60]}...")

    caveats = ["pattern từ hoạt động SUY DIỄN (nghỉ/sạc/idle) — độ tin theo confidence, "
               "không phải đo trực tiếp",
               "ước lượng thiệt hại là định tính (HEURISTIC), không phải số tiền chắc chắn",
               "không phán xét từng cuốc; không chỉ định khu vực"]

    confidence = 0.75 if inferred else 0.6

    return {
        "schema_version": "1.0.0", "solver": "f3_patterns",
        "problem_digest": digest,
        "inputs_used": [{"view_id": f"session_summary_input:{ss['driver_id']}",
                         "version": ss["view_version"], "freshness": f"{ss['session_date']}T23:59:00+07:00"}],
        "solution": {"patterns": patterns, "top_pattern": top, "n_patterns": n},
        "numbers": numbers, "sensitivity": [],
        "confidence": confidence, "caveats": caveats, "infeasible_reason": None,
    }

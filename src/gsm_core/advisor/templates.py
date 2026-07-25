"""Template fallback deterministic — đường LLM-off BẮT BUỘC (guardrail).

Render advice thuần code từ SolverReport + KB excerpt. Luôn chạy được.
"""

from __future__ import annotations

from gsm_core.advisor.context_pack import render_number_vn


def _fmt(reg: dict, nid: str) -> str:
    n = reg.get(nid)
    return render_number_vn(n["value"], n["unit"]) if n else ""


def _rep(solver_reports: list[dict], solver: str) -> dict | None:
    return next((r for r in solver_reports if r["solver"] == solver), None)


def _vn(reg: dict, value, unit: str) -> str:
    """Chuỗi số VN cho (value, unit) CHỈ KHI có trong numbers_registry.

    Bắt buộc tra registry (không tự format từ solution) → mọi số hiển thị đều trace
    được về `SolverReport.numbers[]`; verifier V1 (số trần) vì thế không bị vi phạm.
    """
    if value is None:
        return ""
    for n in reg.values():
        if n["unit"] == unit and abs(float(n["value"]) - float(value)) < 0.5:
            return render_number_vn(n["value"], n["unit"])
    return ""


def _khoan_sentence(solver_reports: list[dict], reg: dict) -> str:
    """Tiến độ khoán tuần + cảnh báo truy thu (ngôn ngữ ĐIỀU KIỆN, không doạ/hứa)."""
    r = _rep(solver_reports, "weekly_khoan")
    if not r:
        return ""
    sol = r.get("solution", {})
    if not sol.get("quota_available"):
        return " Hiện chưa có số khoán tuần chính thức để đối chiếu."
    # BUG-PI5a-02: TRƯỚC ĐÂY kiểm tra CHUỖI đã render ("0đ" là truthy!) ⇒ tài xế đã đạt
    # khoán vẫn bị nói "còn thiếu 0đ … có thể bị truy thu 0đ". Phải xét GIÁ TRỊ SỐ.
    gap_val = sol.get("gap_revenue_vnd") or 0
    claw_val = sol.get("clawback_risk_vnd") or 0
    if gap_val <= 0:
        return " Tuần này anh/chị đã đạt khoán doanh số."
    gap = _vn(reg, gap_val, "vnd")
    if not gap:
        return ""  # không trace được số → không nói (thà thiếu còn hơn bịa)
    s = f" Tuần này còn thiếu {gap} doanh số để đạt khoán."
    claw = _vn(reg, claw_val, "vnd") if claw_val > 0 else ""
    if claw:
        s += f" Nếu không đạt, phần chưa đạt có thể bị truy thu khoảng {claw}."
    return s


def _mission_sentence(solver_reports: list[dict], reg: dict) -> str:
    """Mini-task nên làm (UC8) — thưởng chỉ nhận khi hoàn thành đủ điều kiện."""
    r = _rep(solver_reports, "mission_knapsack")
    if not r:
        return ""
    chosen = (r.get("solution") or {}).get("chosen_missions") or []
    if not chosen:
        return ""
    reward = _vn(reg, (r["solution"] or {}).get("expected_reward_vnd"), "vnd")
    names = ", ".join(str(c.get("name") or c.get("mission_id")) for c in chosen)
    s = f" Nhiệm vụ nên làm: {names}"
    if reward:
        s += f" (thưởng tối đa {reward} nếu hoàn thành đủ điều kiện)"
    return s + "."


def _advice_spec(action: str | None, bucket: str | None) -> dict:
    """advice_spec hợp schema: action_type thường-hoá (adherence taxonomy), KHÔNG
    kèm `expiry` khi rỗng (schema: expiry là string date-time, không nullable)."""
    return {"action_type": (action or "online").lower(),
            "target_window": bucket, "target_zone_or_station": None}


def render_template(feature: str, solver_reports: list[dict], kb_excerpts: list[dict],
                    numbers_registry: dict) -> dict:
    reg = numbers_registry
    # BUG-PI5a-01: TRƯỚC ĐÂY n1/n2 lấy theo VỊ TRÍ trong registry (nids[0], nids[1]).
    # Khi thêm S5/S6, thứ tự đổi ⇒ render câu VÔ NGHĨA, vd "mốc thưởng 35585.2
    # vnd_per_hour" (tốc độ doanh số bị gán nhãn mốc thưởng). Nay CHỈ neo theo
    # GIÁ TRỊ của `bonus_feasibility`; không có solver đó ⇒ để RỖNG và bỏ câu,
    # KHÔNG lấy bừa số khác (thà thiếu còn hơn sai ngữ nghĩa).
    _s1 = _rep(solver_reports, "bonus_feasibility")
    _sol1 = (_s1 or {}).get("solution") or {}
    n1 = _vn(reg, _sol1.get("gap_points"), "points")
    n2 = _vn(reg, _sol1.get("tier_vnd"), "vnd")

    disclaimer = " Lưu ý: đây là ước tính theo dữ liệu lịch sử, không phải cam kết thu nhập."
    citations: list[str] = []
    advice_spec = None

    if feature == "F0":
        cite_txt = ""
        if kb_excerpts:
            citations = [e["source_url"] for e in kb_excerpts[:2]]
            cite_txt = f" Nguồn: {kb_excerpts[0]['title']}."
        msg = (f"Chào anh/chị! Theo chính sách hiện hành, anh/chị cần thêm {n1} "
               f"để đạt mốc thưởng {n2}.{cite_txt}{disclaimer}")
    elif feature == "F1":
        # digest S2 là câu dẫn (solver-authored, deterministic) nếu có
        dp = next((r for r in solver_reports if r["solver"] == "shift_dp"), None)
        plan = (dp["problem_digest"].strip() + " ") if dp else ""
        gap_txt = f"Anh/chị còn thiếu {n1} để chạm mốc thưởng {n2}." if (n1 and n2) else ""
        # UC3 khoán tuần + UC8 mini-task (PI-5a)
        msg = (f"{plan}{gap_txt}{_khoan_sentence(solver_reports, reg)}"
               f"{_mission_sentence(solver_reports, reg)}{disclaimer}")
        na = (dp or {}).get("solution", {}).get("next_action") if dp else None
        if na:
            advice_spec = _advice_spec(na.get("action"), na.get("bucket"))
    elif feature == "F2":
        dp = next((r for r in solver_reports if r["solver"] == "shift_dp"), None)
        na = (dp or {}).get("solution", {}).get("next_action") if dp else None
        act_vn = {"REST": "nghỉ một lúc", "SWAP": "đi đổi pin", "ONLINE": "tiếp tục chạy",
                  "END": "cân nhắc kết ca"}.get((na or {}).get("action", ""), "tiếp tục chạy")
        reason = (na or {}).get("reason", "")
        reason_txt = f" — {reason}" if reason else ""
        progress = f" Anh/chị còn thiếu {n1} để đạt mốc thưởng {n2}." if n1 and n2 else ""
        msg = (f"Gợi ý lúc này: anh/chị nên {act_vn}{reason_txt}.{progress}"
               f"{_mission_sentence(solver_reports, reg)}{disclaimer}")
        if na:
            advice_spec = _advice_spec(na.get("action"), na.get("bucket"))
    else:  # F3
        f3 = next((r for r in solver_reports if r["solver"] == "f3_patterns"), None)
        top = (f3 or {}).get("solution", {}).get("top_pattern") if f3 else None
        progress = f" Ca này anh/chị đạt thêm {n1}, hướng tới mốc {n2}." if n1 and n2 else ""
        khoan = _khoan_sentence(solver_reports, reg)  # UC3 tiến độ tuần (PI-5a)
        if top:
            msg = (f"Tổng kết ca: {top['heuristic_note']}{progress}{khoan} "
                   f"Ca sau anh/chị thử điều chỉnh điểm này nhé.{disclaimer}")
        else:
            msg = (f"Tổng kết ca:{(progress + ' ') if progress else ' '}"
                   f"không có điểm nào cần điều chỉnh rõ rệt "
                   f"— anh/chị chạy ổn định.{khoan}{disclaimer}")

    return {
        "message": msg.strip(),
        "citations": citations,
        "advice_spec": advice_spec,
        "caveats": ["template fallback (không dùng LLM)"],
        "fallback_used": True,
    }

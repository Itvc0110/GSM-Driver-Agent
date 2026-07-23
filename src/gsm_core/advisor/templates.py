"""Template fallback deterministic — đường LLM-off BẮT BUỘC (guardrail).

Render advice thuần code từ SolverReport + KB excerpt. Luôn chạy được.
"""

from __future__ import annotations

from gsm_core.advisor.context_pack import render_number_vn


def _fmt(reg: dict, nid: str) -> str:
    n = reg.get(nid)
    return render_number_vn(n["value"], n["unit"]) if n else ""


def _advice_spec(action: str | None, bucket: str | None) -> dict:
    """advice_spec hợp schema: action_type thường-hoá (adherence taxonomy), KHÔNG
    kèm `expiry` khi rỗng (schema: expiry là string date-time, không nullable)."""
    return {"action_type": (action or "online").lower(),
            "target_window": bucket, "target_zone_or_station": None}


def render_template(feature: str, solver_reports: list[dict], kb_excerpts: list[dict],
                    numbers_registry: dict) -> dict:
    reg = numbers_registry
    nids = list(reg.keys())
    n1 = _fmt(reg, nids[0]) if len(nids) > 0 else ""
    n2 = _fmt(reg, nids[1]) if len(nids) > 1 else ""

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
        msg = (f"{plan}Anh/chị còn thiếu {n1} để chạm mốc thưởng {n2}.{disclaimer}")
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
        msg = f"Gợi ý lúc này: anh/chị nên {act_vn}{reason_txt}.{progress}{disclaimer}"
        if na:
            advice_spec = _advice_spec(na.get("action"), na.get("bucket"))
    else:  # F3
        f3 = next((r for r in solver_reports if r["solver"] == "f3_patterns"), None)
        top = (f3 or {}).get("solution", {}).get("top_pattern") if f3 else None
        progress = f" Ca này anh/chị đạt thêm {n1}, hướng tới mốc {n2}." if n1 and n2 else ""
        if top:
            msg = (f"Tổng kết ca: {top['heuristic_note']}{progress} "
                   f"Ca sau anh/chị thử điều chỉnh điểm này nhé.{disclaimer}")
        else:
            msg = f"Tổng kết ca:{progress} không có điểm nào cần điều chỉnh rõ rệt — anh/chị chạy ổn định.{disclaimer}"

    return {
        "message": msg.strip(),
        "citations": citations,
        "advice_spec": advice_spec,
        "caveats": ["template fallback (không dùng LLM)"],
        "fallback_used": True,
    }

"""Router — direct mapping zero-ML (research đợt 7: <15 intents không cần classifier).

Feature từ AdviceRequest (UI trigger đã biết) → solver set. Free-text → keyword
layer tiếng Việt xác nhận; không match → out_of_taxonomy (R5, từ chối lịch sự).
"""

from __future__ import annotations

from gsm_core.advisor._text import normalize_vi as _norm

FEATURE_SOLVERS = {
    "F0": {"solvers": ["bonus_feasibility"], "use_kb": True},
    "F1": {"solvers": ["bonus_feasibility", "shift_dp"], "use_kb": False},
    "F2": {"solvers": ["shift_dp", "capacity_alloc"], "use_kb": False},
    "F3": {"solvers": ["f3_patterns"], "use_kb": False},
}

# keyword tiếng Việt (đã bỏ dấu) per intent — dict viết tay, fixture test
_INTENT_KEYWORDS = {
    "policy_bonus": ["thuong", "moc", "diem", "chinh sach", "chuyen", "cuoc",
                     "thu nhap", "phi", "pin", "doi pin", "tai khoan", "quyen loi"],
    "shift_plan": ["ca", "lich", "gio", "nghi", "sac", "chay luc nao", "khung gio"],
    "session_review": ["tong ket", "ca vua", "sao thu nhap", "toi uu",
                       "thu nhap hom nay", "ket qua ca"],
}


def route(feature: str, free_text_query: str | None) -> dict:
    base = FEATURE_SOLVERS.get(feature)
    if base is None:
        return {"intent": "out_of_taxonomy", "solvers": [], "use_kb": False,
                "feature": feature}
    out = {"feature": feature, "solvers": list(base["solvers"]),
           "use_kb": base["use_kb"], "intent": f"{feature}_default"}
    if base["use_kb"]:
        out["solvers"] = out["solvers"] + ["policy_kb"]
    if free_text_query:
        q = _norm(free_text_query)
        matched = None
        for intent, kws in _INTENT_KEYWORDS.items():
            if any(kw in q for kw in kws):
                matched = intent
                break
        if matched is None:
            return {"intent": "out_of_taxonomy", "solvers": [], "use_kb": False,
                    "feature": feature}
        out["intent"] = matched
    return out

"""Router advice: gọi solver S1 thật qua adapter — contract `ui/contracts/advice.json`.

UX-CARDS (DIRECTIVES §12, UPDATE-067): thêm vòng đo adherence EXPLICIT —
POST /action ghi nút bấm (Làm theo/Bỏ qua/Vì sao); GET /actions đọc lại cho khối
"Nhật ký làm-theo" ở màn Cài đặt. Đường đo IMPLICIT (hành vi đổi sau advice) vẫn
nằm ở sim/A-B — hai đường bổ trợ.

ĐA-05 Cycle W: store CANONICAL của action là AdviceEventLog (SQLite append-only,
cùng luật projection với sim — verdict Cường "một luật, một database"); JSONL
`advice_actions.jsonl` GIỮ như debug export song song (quyết định duyệt: "JSONL chỉ
debug/export"). GET /actions đọc từ event log — hàng ghi vào JSONL trước Cycle W
không tự chuyển (mock-only, gitignored — chấp nhận, ghi ở UPDATE-091).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.adapters import advisor, mockdata
from gsm_core.lifecycle.event_log import AdviceEventLog

router = APIRouter()

TELEMETRY_DIR = mockdata.REPO_ROOT / "data" / "ui-telemetry"
ACTIONS_FILE = TELEMETRY_DIR / "advice_actions.jsonl"

# nút UI → event_type lifecycle ("Vì sao"/expanded = một lần card được XEM KỸ → displayed)
_ACTION_TO_EVENT = {"followed": "followed", "dismissed": "dismissed",
                    "expanded": "displayed"}


def _lifecycle_db() -> Path:
    """Đọc TELEMETRY_DIR tại call-time để monkeypatch của tests có hiệu lực."""
    return TELEMETRY_DIR / "advice_lifecycle.db"


@router.get("")
def get_advice(driver_id: str | None = Query(None), date: str | None = Query(None),
               now_min: int = Query(14 * 60, ge=0, le=24 * 60),
               shift_end_min: int = Query(advisor.DEFAULT_SHIFT_END_MIN, ge=0, le=24 * 60)):
    dv = mockdata.default_view()
    return advisor.advice(driver_id or dv["driver_id"], date or dv["date"],
                          now_min, shift_end_min)


class AdviceAction(BaseModel):
    advice_id: str
    driver_id: str
    # `date` được ghép thành `occurred_at` ISO ⇒ phải đúng dạng NGAY TỪ ĐẦU. Không
    # validate ở đây thì store canonical từ chối SAU khi JSONL đã ghi ⇒ HTTP 500 và hai
    # store lệch nhau vĩnh viễn (review đối kháng reproduce với date='hom-nay').
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    action: str = Field(pattern="^(followed|dismissed|expanded)$")
    card_kind: str = Field(pattern="^(brief|nudge|recap)$")
    # le=1439: 1440 sinh "T24:00:00" — lọt regex schema (`\d{2}`) nhưng `fromisoformat`
    # nổ ⇒ MỘT record độc giết toàn bộ `decision_state` của store đó.
    at_min: int | None = Field(default=None, ge=0, le=1439)


@router.post("/action")
def post_action(body: AdviceAction):
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).isoformat()
    rec = {**body.model_dump(), "client_ts": now_iso, "is_mock": True}
    occurred = (f"{body.date}T{body.at_min // 60:02d}:{body.at_min % 60:02d}:00+07:00"
                if body.at_min is not None else now_iso)
    # Store CANONICAL ghi TRƯỚC, JSONL debug ghi SAU: nếu canonical từ chối thì không có
    # gì được ghi cả. Thứ tự ngược lại từng làm "debug export" có dữ liệu mà store thật
    # thì không — ngược đúng chiều tin cậy mà ĐA-05 tuyên bố.
    #
    # Idempotency key = (advice, action, GIÂY quan sát). Bản đầu khoá theo `at_min` —
    # nhưng frontend gửi at_min là HẰNG SỐ theo loại card (`cards.js`), nên cửa sổ dedupe
    # là CẢ NGÀY: "Làm theo → đổi ý Bỏ qua → Làm theo lại" bị nuốt còn 2 event và nhật ký
    # hiện NGƯỢC hành động cuối. Theo giây: double-click là một, đổi ý là hai.
    with AdviceEventLog(_lifecycle_db()) as log:
        log.append({
            "event_id": f"ui-{body.advice_id}-{body.action}-{now_iso[:19]}",
            "decision_id": body.advice_id,       # namespace s1-… của adapter (deterministic)
            "display_id": None,
            "driver_id": body.driver_id,
            "run_id": None,
            "event_type": _ACTION_TO_EVENT[body.action],
            "reason_code": "dismissed_for_window" if body.action == "dismissed" else None,
            "occurred_at": occurred,
            "observed_at": now_iso,
            "actor": "driver",
            "origin": "ui",
            "source": "MOCK",
            "context_revision": None,
            "payload": {"action": body.action, "card_kind": body.card_kind,
                        "date": body.date, "at_min": body.at_min},
            "schema_version": "1.0.0",
        })
    # JSONL: debug export song song (ĐA-05 — không còn là store canonical)
    with ACTIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"ok": True, "logged": rec}


@router.get("/actions")
def get_actions(driver_id: str | None = Query(None), limit: int = Query(50, ge=1, le=500)):
    """Đọc từ event log canonical (ĐA-05) — giữ NGUYÊN hình dạng row của contract
    `advice_action.json` để web "Nhật ký làm-theo" không đổi."""
    db = _lifecycle_db()
    if not db.exists():
        return {"is_mock": True, "actions": []}
    with AdviceEventLog(db) as log:
        events = [e for e in log.events() if e["origin"] == "ui"]
    rows = []
    for e in sorted(events, key=lambda e: (e["observed_at"], e["event_id"])):
        p = e["payload"]
        if driver_id and e["driver_id"] != driver_id:
            continue
        rows.append({"advice_id": e["decision_id"], "driver_id": e["driver_id"],
                     "date": p.get("date"), "action": p.get("action"),
                     "card_kind": p.get("card_kind"), "at_min": p.get("at_min"),
                     "client_ts": e["observed_at"], "is_mock": True})
    return {"is_mock": True, "actions": rows[-limit:][::-1]}

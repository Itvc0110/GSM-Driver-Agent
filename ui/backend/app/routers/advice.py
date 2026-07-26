"""Router advice: gọi solver S1 thật qua adapter — contract `ui/contracts/advice.json`.

UX-CARDS (DIRECTIVES §12, UPDATE-067): thêm vòng đo adherence EXPLICIT —
POST /action ghi nút bấm (Làm theo/Bỏ qua/Vì sao) vào jsonl local (gitignored,
nhãn mock); GET /actions đọc lại cho khối "Nhật ký làm-theo" ở màn Cài đặt.
Đường đo IMPLICIT (hành vi đổi sau advice) vẫn nằm ở sim/A-B — hai đường bổ trợ.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.adapters import advisor, mockdata

router = APIRouter()

TELEMETRY_DIR = mockdata.REPO_ROOT / "data" / "ui-telemetry"
ACTIONS_FILE = TELEMETRY_DIR / "advice_actions.jsonl"


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
    date: str
    action: str = Field(pattern="^(followed|dismissed|expanded)$")
    card_kind: str = Field(pattern="^(brief|nudge|recap)$")
    at_min: int | None = Field(default=None, ge=0, le=1440)


@router.post("/action")
def post_action(body: AdviceAction):
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    rec = {**body.model_dump(),
           "client_ts": datetime.now(timezone.utc).isoformat(),
           "is_mock": True}
    with ACTIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"ok": True, "logged": rec}


@router.get("/actions")
def get_actions(driver_id: str | None = Query(None), limit: int = Query(50, ge=1, le=500)):
    if not ACTIONS_FILE.exists():
        return {"is_mock": True, "actions": []}
    rows = []
    for line in ACTIONS_FILE.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if driver_id and r.get("driver_id") != driver_id:
            continue
        rows.append(r)
    return {"is_mock": True, "actions": rows[-limit:][::-1]}

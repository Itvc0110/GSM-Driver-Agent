"""Router advice: gọi solver S1 thật qua adapter — contract `ui/contracts/advice.json`."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.adapters import advisor, mockdata

router = APIRouter()


@router.get("")
def get_advice(driver_id: str | None = Query(None), date: str | None = Query(None),
               now_min: int = Query(14 * 60, ge=0, le=24 * 60),
               shift_end_min: int = Query(advisor.DEFAULT_SHIFT_END_MIN, ge=0, le=24 * 60)):
    dv = mockdata.default_view()
    return advisor.advice(driver_id or dv["driver_id"], date or dv["date"],
                          now_min, shift_end_min)

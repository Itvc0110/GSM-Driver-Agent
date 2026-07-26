"""Router driver-data: state / history / catalog — đọc bộ mock 90 ngày qua adapter.

Trả dict thẳng theo contract `ui/contracts/driver_state.json` v1.1 (schema được
test ở `ui/backend/tests/test_contracts.py`) — không khai Pydantic trùng lặp để
tránh HAI nguồn sự thật về shape.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.adapters import mockdata

router = APIRouter()


@router.get("/catalog")
def get_catalog():
    return mockdata.catalog()


@router.get("/default-view")
def get_default_view():
    return mockdata.default_view()


@router.get("/state")
def get_state(driver_id: str | None = Query(None), date: str | None = Query(None)):
    dv = mockdata.default_view()
    driver_id = driver_id or dv["driver_id"]
    date = date or dv["date"]
    try:
        return mockdata.driver_state(driver_id, date)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/history")
def get_history(driver_id: str | None = Query(None), date: str | None = Query(None),
                days: int = Query(14, ge=1, le=90)):
    dv = mockdata.default_view()
    return mockdata.driver_history(driver_id or dv["driver_id"], date or dv["date"], days)

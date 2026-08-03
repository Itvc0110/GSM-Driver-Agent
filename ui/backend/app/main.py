"""GSM Driver UI Gateway — FastAPI backend chung cho web (ui/web) + Flutter (ui/driver_app).

Tiến hoá từ gateway của Khánh (T-009): giữ nguyên OSRM routing proxy + trip/step demo;
map-context và driver/state nay đọc **bộ mock 90 ngày** (`data/mock/realdata-v1`) qua
adapter thay vì synthetic random — `scenario_id="synthetic"` giữ generator cũ của Khánh
cho mục đích demo. Route fare là quote MOCK từ `gsm_sim.PolicyBundle`; `/trip/step`
chỉ mô tả lifecycle và không tự tính fare. Contract shapes: `ui/contracts/*.json`.

Chạy (từ repo root):
    uv run uvicorn app.main:app --app-dir ui/backend --port 8000
Web app: http://localhost:8000/app/
"""

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.models import MapContextResponse, DriverStateResponse, TripStepResponse
from app.simulator import (
    generate_synthetic_map_context,
    generate_synthetic_driver_state,
    generate_synthetic_trip_step,
)
from app.adapters import mockdata
from app.routers.routing import router as routing_router
from app.routers.driver import router as driver_router
from app.routers.advice import router as advice_router
from app.routers.advice_v2 import router as advice_v2_router
from app.routers.sim import router as sim_router

app = FastAPI(
    title="GSM Driver UI Gateway",
    description="Backend chung web + Flutter — data mock 90 ngày + advisor solver + OSRM proxy",
    version="2.0.0",
)

app.include_router(routing_router, prefix="/api/v1/routing", tags=["Routing"])
app.include_router(driver_router, prefix="/api/v1/driver", tags=["Driver"])
app.include_router(advice_router, prefix="/api/v1/advice", tags=["Advice"])
app.include_router(advice_v2_router, prefix="/api/v2/advice", tags=["Advice v2"])
app.include_router(sim_router, prefix="/api/v1/sim", tags=["Simulation"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = Path(__file__).resolve().parents[2] / "web"
if WEB_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


@app.get("/")
def read_root():
    return RedirectResponse(url="/app/")


@app.get("/api/v1/map-context")
def get_map_context(
    scenario_id: str = Query("mock-realdata", description="'synthetic' = generator demo của Khánh"),
    seed: int = Query(42),
    date: str | None = Query(None),
    hour: int = Query(18, ge=0, le=23),
    driver_id: str | None = Query(None),
):
    if scenario_id == "synthetic":
        return generate_synthetic_map_context(scenario_id=scenario_id, seed=seed)
    dv = mockdata.default_view()
    return mockdata.map_context(date or dv["date"], hour, driver_id)


@app.get("/api/v1/driver/state-synthetic", response_model=DriverStateResponse,
         deprecated=True, tags=["Legacy"])
def get_driver_state_synthetic(scenario_id: str = Query("default_hanoi"), seed: int = Query(42)):
    """Generator synthetic gốc của Khánh — giữ cho demo/đối chiếu."""
    return generate_synthetic_driver_state(scenario_id=scenario_id, seed=seed)


@app.get("/api/v1/trip/step", response_model=TripStepResponse)
def get_trip_step(
    trip_index: int = Query(0, description="Trip index (0, 1, 2...)"),
    step: str = Query("INCOMING", description="INCOMING, PICKING_UP, IN_PROGRESS, COMPLETED"),
):
    """Vòng đời cuốc DEMO (3 cuốc mẫu của Khánh) — mô phỏng interaction, không phải data."""
    return generate_synthetic_trip_step(trip_index=trip_index, step=step)

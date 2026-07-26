from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from app.models import MapContextResponse, DriverStateResponse, TripStepResponse
from app.simulator import (
    generate_synthetic_map_context,
    generate_synthetic_driver_state,
    generate_synthetic_trip_step
)
from app.routers.routing import router as routing_router

app = FastAPI(
    title="GSM Driver Map Context API Gateway",
    description="Synthetic data API gateway for GSM Driver Mobile App & Leafmap Simulator",
    version="1.0.0"
)

app.include_router(routing_router, prefix="/api/v1/routing", tags=["Routing"])


# Enable CORS for Flutter Web / Localhost / Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "GSM Driver Map Context Gateway",
        "docs": "/docs"
    }

@app.get("/api/v1/map-context", response_model=MapContextResponse)
def get_map_context(
    scenario_id: str = Query("default_hanoi", description="Synthetic scenario ID"),
    seed: int = Query(42, description="Random seed for synthetic generation")
):
    return generate_synthetic_map_context(scenario_id=scenario_id, seed=seed)

@app.get("/api/v1/driver/state", response_model=DriverStateResponse)
def get_driver_state(
    scenario_id: str = Query("default_hanoi", description="Synthetic scenario ID"),
    seed: int = Query(42, description="Random seed for synthetic generation")
):
    return generate_synthetic_driver_state(scenario_id=scenario_id, seed=seed)

@app.get("/api/v1/trip/step", response_model=TripStepResponse)
def get_trip_step(
    trip_index: int = Query(0, description="Trip index (0, 1, 2...)"),
    step: str = Query("INCOMING", description="Trip step stage: INCOMING, PICKING_UP, IN_PROGRESS, COMPLETED")
):
    return generate_synthetic_trip_step(trip_index=trip_index, step=step)

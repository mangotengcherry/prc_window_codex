"""FastAPI entry point for the Process Window prototype.

Run after installing backend requirements:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ModuleNotFoundError as exc:  # pragma: no cover - exercised only without deps
    raise ModuleNotFoundError(
        "FastAPI is not installed. Install backend/requirements.txt before running the API."
    ) from exc

from app.analysis.interaction_2d import build_interaction_heatmap
from app.analysis.ranking import rank_l3_features
from app.analysis.window_1d import analyze_single_window
from app.repository import SyntheticRepository
from app.schemas import GenericResponse, InteractionRequest, RankRequest, SingleAnalysisRequest
from app.synthetic_data import make_synthetic_frame


app = FastAPI(title="Process Window Prototype")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
repository = SyntheticRepository(make_synthetic_frame())


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/catalog")
def catalog() -> GenericResponse:
    return GenericResponse(data=repository.get_catalog())


@app.post("/api/rank")
def rank(request: RankRequest) -> GenericResponse:
    data = rank_l3_features(
        repository.load_frame(),
        product_id=request.product_id,
        l3_items=request.selected_l3_items,
        l1_features=request.selected_l1_features,
        min_wafer_count=request.min_wafer_count,
    )
    return GenericResponse(data=data)


@app.post("/api/analyze/single")
def analyze_single(request: SingleAnalysisRequest) -> GenericResponse:
    data = analyze_single_window(
        repository.load_frame(),
        product_id=request.product_id,
        l1_feature_name=request.l1_feature_name,
        l3_item_name=request.l3_item_name,
        bin_count=request.bin_count,
        min_wafer_count=request.min_wafer_count,
        max_allowed_loss_rate=request.max_allowed_loss_rate,
    )
    return GenericResponse(data=data)


@app.post("/api/analyze/interaction")
def analyze_interaction(request: InteractionRequest) -> GenericResponse:
    data = build_interaction_heatmap(
        repository.load_frame(),
        product_id=request.product_id,
        l1_feature_x=request.l1_feature_x,
        l1_feature_y=request.l1_feature_y,
        l3_item_name=request.l3_item_name,
        x_bins=request.x_bins,
        y_bins=request.y_bins,
        min_wafer_count=request.min_wafer_count,
    )
    return GenericResponse(data=data)

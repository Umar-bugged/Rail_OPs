from __future__ import annotations

from fastapi import APIRouter

from backend.src.api.schemas import HealthResponse, ModelInfoResponse, PredictionRequest, PredictionResponse
from backend.src.core.config import get_settings
from backend.src.models.predictor import get_prediction_engine
from backend.src.services.analytics_repository import get_analytics_repository

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    analytics = get_analytics_repository()
    engine = get_prediction_engine()
    model_status = "trained" if engine.bundle else "baseline"
    return HealthResponse(
        api_status="online",
        model_status=model_status,
        environment=settings.environment,
        dataset_size=int(analytics.snapshot().get("dataset_size", 0)),
    )


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> dict[str, object]:
    return get_prediction_engine().model_info()


@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> dict[str, object]:
    return get_prediction_engine().predict(
        train_number=request.train_number,
        station_code=request.station_code,
        current_delay=request.current_delay,
    )


@router.get("/analytics/overview")
def overview() -> dict[str, object]:
    snapshot = get_analytics_repository().snapshot()
    return {"overview": snapshot["overview"], "trends": snapshot["trends"]}


@router.get("/analytics/network")
def network_analytics() -> dict[str, object]:
    snapshot = get_analytics_repository().snapshot()
    return {
        "network": snapshot["network"],
        "heatmap": snapshot["heatmap"],
        "zone_performance": snapshot["zone_performance"],
        "route_congestion": snapshot["route_congestion"],
        "train_type_analysis": snapshot["train_type_analysis"],
    }


@router.get("/analytics/stations/{station_code}")
def station_profile(station_code: str) -> dict[str, object]:
    return get_analytics_repository().station_profile(station_code)


@router.get("/analytics/trains/{train_number}")
def train_profile(train_number: int) -> dict[str, object]:
    return get_analytics_repository().train_profile(train_number)


@router.get("/search/stations")
def station_search(q: str, limit: int = 8) -> list[dict[str, object]]:
    return get_analytics_repository().search_stations(q, limit=min(max(limit, 1), 20))


@router.get("/search/trains")
def train_search(q: str, limit: int = 8) -> list[dict[str, object]]:
    return get_analytics_repository().search_trains(q, limit=min(max(limit, 1), 20))

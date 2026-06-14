from __future__ import annotations

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    train_number: int = Field(..., examples=[12627])
    station_code: str = Field(..., min_length=2, max_length=8, examples=["NGP"])
    current_delay: float = Field(..., ge=0, le=720, examples=[15])


class PredictionResponse(BaseModel):
    predicted_delay: float
    confidence_score: float
    delay_category: str
    model_source: str


class HealthResponse(BaseModel):
    api_status: str
    model_status: str
    environment: str
    dataset_size: int


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    trained_at: str | None
    metrics: dict[str, float | None]
    candidate_metrics: dict[str, dict[str, float]]
    dataset_size: int
    feature_importance: list[dict[str, float | str]]

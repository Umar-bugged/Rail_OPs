from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from backend.src.core.config import Settings, get_settings
from backend.src.features.build_features import build_prediction_features
from backend.src.services.analytics_repository import AnalyticsRepository, get_analytics_repository

LOGGER = logging.getLogger(__name__)


def delay_category(delay_minutes: float) -> str:
    if delay_minutes < 10:
        return "On Time"
    if delay_minutes < 30:
        return "Minor Delay"
    if delay_minutes < 60:
        return "Moderate Delay"
    return "Severe Delay"


@dataclass
class PredictionEngine:
    settings: Settings
    analytics: AnalyticsRepository

    def __post_init__(self) -> None:
        self.model_path = self.settings.model_dir / "train_delay_model.pkl"
        self.metadata_path = self.settings.model_dir / "metrics.json"
        self.bundle: dict[str, Any] | None = self._load_bundle()
        self.metadata: dict[str, Any] | None = self._load_metadata()

    def _load_bundle(self) -> dict[str, Any] | None:
        LOGGER.info("Model file path: %s", self.model_path)
        if not self.model_path.exists():
            LOGGER.warning("Model bundle not found at %s. Using baseline predictor.", self.model_path)
            return None
        try:
            bundle = joblib.load(self.model_path)
        except Exception:
            LOGGER.exception("Failed to load model bundle from %s. Using baseline predictor.", self.model_path)
            return None

        if not isinstance(bundle, dict) or "model" not in bundle:
            LOGGER.error("Model bundle at %s is invalid or missing the trained estimator. Using baseline predictor.", self.model_path)
            return None

        LOGGER.info(
            "Loaded model bundle from %s: name=%s version=%s",
            self.model_path,
            bundle.get("model_name", "unknown"),
            bundle.get("model_version", "unknown"),
        )
        return bundle

    @property
    def has_trained_model(self) -> bool:
        return bool(self.bundle and "model" in self.bundle)

    def _metadata_from_bundle(self) -> dict[str, Any] | None:
        if not self.bundle:
            return None
        return {key: value for key, value in self.bundle.items() if key != "model"}

    def _metadata_matches_bundle(self, metadata: dict[str, Any]) -> bool:
        if not self.bundle:
            return True

        for key in ("model_name", "model_version", "trained_at"):
            bundle_value = self.bundle.get(key)
            if bundle_value is not None and metadata.get(key) != bundle_value:
                LOGGER.warning(
                    "Model metadata at %s does not match loaded bundle for %s: metadata=%s bundle=%s",
                    self.metadata_path,
                    key,
                    metadata.get(key),
                    bundle_value,
                )
                return False
        return True

    def _write_generated_metadata(self, metadata: dict[str, Any]) -> None:
        try:
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            self.metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            LOGGER.info("Generated model metadata at %s from loaded model bundle.", self.metadata_path)
        except Exception:
            LOGGER.exception("Failed to write generated model metadata to %s.", self.metadata_path)

    def _load_metadata(self) -> dict[str, Any] | None:
        LOGGER.info("Model metadata file path: %s", self.metadata_path)
        if self.metadata_path.exists():
            try:
                metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            except Exception:
                LOGGER.exception("Failed to load model metadata from %s.", self.metadata_path)
            else:
                if self._metadata_matches_bundle(metadata):
                    LOGGER.info(
                        "Loaded model metadata from %s: name=%s version=%s",
                        self.metadata_path,
                        metadata.get("model_name", "unknown"),
                        metadata.get("model_version", "unknown"),
                    )
                    return metadata
                LOGGER.warning("Regenerating model metadata from the loaded model bundle.")
        else:
            LOGGER.warning("Model metadata not found at %s.", self.metadata_path)

        generated = self._metadata_from_bundle()
        if generated:
            LOGGER.warning("Using model metadata generated from the loaded model bundle.")
            self._write_generated_metadata(generated)
            LOGGER.info(
                "Loaded generated model metadata: name=%s version=%s",
                generated.get("model_name", "unknown"),
                generated.get("model_version", "unknown"),
            )
            return generated

        LOGGER.warning("No trained model metadata is available. Model info will use baseline metadata.")
        return None

    def predict(self, train_number: int, station_code: str, current_delay: float) -> dict[str, Any]:
        profile = self.analytics.prediction_profile(train_number, station_code, current_delay)

        if self.has_trained_model:
            features = build_prediction_features(train_number, station_code, current_delay, profile)
            prediction = float(np.clip(self.bundle["model"].predict(features)[0], 0, 720))
            confidence = self._model_confidence(prediction, current_delay)
            source = "trained_model"
        else:
            prediction = self._baseline_prediction(profile, current_delay)
            confidence = self._baseline_confidence(profile, current_delay)
            source = "baseline"

        return {
            "predicted_delay": round(prediction, 2),
            "confidence_score": round(confidence, 2),
            "delay_category": delay_category(prediction),
            "model_source": source,
        }

    def model_info(self) -> dict[str, Any]:
        if self.metadata:
            return self.metadata

        snapshot = self.analytics.snapshot()
        return {
            "model_name": "Baseline Operations Predictor",
            "model_version": "baseline",
            "trained_at": None,
            "metrics": {"mae": None, "rmse": None, "r2": None},
            "candidate_metrics": {},
            "dataset_size": snapshot.get("dataset_size", 0),
            "feature_importance": [
                {"feature": "current_delay", "importance": 0.42},
                {"feature": "station_average_delay", "importance": 0.24},
                {"feature": "train_average_delay", "importance": 0.18},
                {"feature": "distance_from_source", "importance": 0.08},
                {"feature": "hour_of_day", "importance": 0.08},
            ],
        }

    def _baseline_prediction(self, profile: dict[str, object], current_delay: float) -> float:
        station_average = float(profile.get("station_average_delay", current_delay) or current_delay)
        train_average = float(profile.get("train_average_delay", station_average) or station_average)
        recent_average = float(profile.get("average_delay_last_7_days", train_average) or train_average)
        distance_factor = min(float(profile.get("distance_from_source", 0) or 0) / 1500, 1.5)
        predicted = (current_delay * 0.58) + (station_average * 0.18) + (train_average * 0.14) + (recent_average * 0.1)
        return float(np.clip(predicted + distance_factor * 4, 0, 720))

    def _baseline_confidence(self, profile: dict[str, object], current_delay: float) -> float:
        station_average = float(profile.get("station_average_delay", 0) or 0)
        train_average = float(profile.get("train_average_delay", 0) or 0)
        has_history = station_average > 0 and train_average > 0
        volatility = abs(station_average - current_delay) / max(station_average, current_delay, 1)
        return float(np.clip((0.74 if has_history else 0.58) - volatility * 0.18, 0.35, 0.86))

    def _model_confidence(self, prediction: float, current_delay: float) -> float:
        metrics = self.bundle.get("metrics", {}) if self.bundle else {}
        rmse = metrics.get("rmse") or 20
        error_ratio = min(float(rmse) / max(prediction, current_delay, 15), 1.0)
        return float(np.clip(0.92 - error_ratio * 0.28, 0.5, 0.93))


@lru_cache
def get_prediction_engine() -> PredictionEngine:
    return PredictionEngine(settings=get_settings(), analytics=get_analytics_repository())

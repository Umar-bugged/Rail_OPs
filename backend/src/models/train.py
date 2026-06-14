from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from backend.src.core.config import get_settings
from backend.src.core.logging import configure_logging
from backend.src.data.loader import load_delay_sample, load_reference_data, resolve_data_paths
from backend.src.features.build_features import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    prepare_training_frame,
)

LOGGER = logging.getLogger(__name__)
MODEL_VERSION = "2026.06.13"


def _preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(handle_unknown="ignore", min_frequency=5), CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def _candidate_models(random_state: int = 42) -> dict[str, Pipeline]:
    candidates: dict[str, Pipeline] = {
        "Linear Regression": Pipeline([("preprocessor", _preprocessor()), ("model", LinearRegression())]),
        "Random Forest": Pipeline(
            [
                ("preprocessor", _preprocessor()),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=140,
                        max_depth=18,
                        min_samples_leaf=3,
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }

    try:
        from xgboost import XGBRegressor

        candidates["XGBoost"] = Pipeline(
            [
                ("preprocessor", _preprocessor()),
                (
                    "model",
                    XGBRegressor(
                        n_estimators=320,
                        max_depth=6,
                        learning_rate=0.055,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        objective="reg:squarederror",
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
    except ImportError:
        LOGGER.warning("xgboost is not installed. Skipping XGBoost candidate.")

    return candidates


def _evaluate(y_true: pd.Series, predictions: np.ndarray) -> dict[str, float]:
    mse = mean_squared_error(y_true, predictions)
    return {
        "mae": round(float(mean_absolute_error(y_true, predictions)), 4),
        "rmse": round(float(np.sqrt(mse)), 4),
        "r2": round(float(r2_score(y_true, predictions)), 4),
    }


def _feature_importance(model: Pipeline) -> list[dict[str, float | str]]:
    preprocessor: ColumnTransformer = model.named_steps["preprocessor"]
    estimator = model.named_steps["model"]

    try:
        feature_names = preprocessor.get_feature_names_out()
    except ValueError:
        feature_names = np.array(FEATURE_COLUMNS)

    if hasattr(estimator, "feature_importances_"):
        values = np.asarray(estimator.feature_importances_)
    elif hasattr(estimator, "coef_"):
        values = np.abs(np.asarray(estimator.coef_)).reshape(-1)
    else:
        return []

    importance_by_base: dict[str, float] = {}
    for name, value in zip(feature_names, values, strict=False):
        clean_name = str(name).split("__", maxsplit=1)[-1]
        base = next((feature for feature in FEATURE_COLUMNS if clean_name == feature or clean_name.startswith(f"{feature}_")), clean_name)
        importance_by_base[base] = importance_by_base.get(base, 0.0) + float(value)

    total = sum(importance_by_base.values()) or 1.0
    return [
        {"feature": feature, "importance": round(value / total, 4)}
        for feature, value in sorted(importance_by_base.items(), key=lambda item: item[1], reverse=True)[:15]
    ]


def train_model(max_rows: int | None = None) -> dict[str, Any]:
    settings = get_settings()
    paths = resolve_data_paths(settings)
    max_rows = max_rows or settings.max_training_rows

    LOGGER.info("Loading reference data from %s", paths.as_dict())
    trains, stations, schedule = load_reference_data(paths)
    delay = load_delay_sample(paths, max_rows=max_rows)
    frame = prepare_training_frame(delay=delay, schedule=schedule, stations=stations, trains=trains)

    if len(frame) < 30:
        raise ValueError("At least 30 cleaned rows are required for training.")

    x = frame[FEATURE_COLUMNS]
    y = frame[TARGET_COLUMN]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    metrics: dict[str, dict[str, float]] = {}
    fitted_models: dict[str, Pipeline] = {}
    for name, pipeline in _candidate_models().items():
        LOGGER.info("Training %s", name)
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        metrics[name] = _evaluate(y_test, predictions)
        fitted_models[name] = pipeline

    best_name = min(metrics, key=lambda item: metrics[item]["rmse"])
    best_model = fitted_models[best_name]
    feature_importance = _feature_importance(best_model)

    bundle = {
        "model": best_model,
        "model_name": best_name,
        "model_version": MODEL_VERSION,
        "trained_at": datetime.now(UTC).isoformat(),
        "metrics": metrics[best_name],
        "candidate_metrics": metrics,
        "dataset_size": int(len(frame)),
        "feature_columns": FEATURE_COLUMNS,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "feature_importance": feature_importance,
        "data_paths": paths.as_dict(),
    }

    model_path = settings.model_dir / "train_delay_model.pkl"
    metrics_path = settings.model_dir / "metrics.json"
    joblib.dump(bundle, model_path)
    metrics_path.write_text(json.dumps({key: value for key, value in bundle.items() if key != "model"}, indent=2), encoding="utf-8")
    LOGGER.info("Saved best model %s to %s", best_name, model_path)
    return bundle


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Train railway delay prediction models.")
    parser.add_argument("--max-rows", type=int, default=None, help="Maximum delay rows to load for training.")
    args = parser.parse_args()
    train_model(max_rows=args.max_rows)


if __name__ == "__main__":
    main()

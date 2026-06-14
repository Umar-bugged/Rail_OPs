from __future__ import annotations

import argparse
import logging

import joblib
import matplotlib
import pandas as pd

from backend.src.core.config import get_settings
from backend.src.core.logging import configure_logging
from backend.src.data.loader import load_delay_sample, load_reference_data, resolve_data_paths
from backend.src.features.build_features import FEATURE_COLUMNS, prepare_training_frame

matplotlib.use("Agg")

LOGGER = logging.getLogger(__name__)


def generate_shap_artifacts(sample_size: int = 300) -> list[str]:
    import matplotlib.pyplot as plt
    import shap

    settings = get_settings()
    model_path = settings.model_dir / "train_delay_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model bundle not found: {model_path}")

    bundle = joblib.load(model_path)
    pipeline = bundle["model"]
    paths = resolve_data_paths(settings)
    trains, stations, schedule = load_reference_data(paths)
    delay = load_delay_sample(paths, max_rows=max(sample_size * 4, 1000))
    frame = prepare_training_frame(delay=delay, schedule=schedule, stations=stations, trains=trains)
    sample = frame[FEATURE_COLUMNS].sample(min(sample_size, len(frame)), random_state=42)

    preprocessor = pipeline.named_steps["preprocessor"]
    estimator = pipeline.named_steps["model"]
    transformed = preprocessor.transform(sample)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    feature_names = preprocessor.get_feature_names_out()

    if hasattr(estimator, "predict"):
        explainer = shap.Explainer(estimator, transformed, feature_names=feature_names)
        values = explainer(transformed)
    else:
        raise TypeError("The fitted estimator does not support prediction.")

    output_dir = settings.model_dir / "explanations"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "shap_summary.png"
    bar_path = output_dir / "shap_bar.png"

    shap.summary_plot(values, transformed, feature_names=feature_names, show=False, max_display=16)
    plt.tight_layout()
    plt.savefig(summary_path, dpi=160)
    plt.close()

    shap.plots.bar(values, show=False, max_display=16)
    plt.tight_layout()
    plt.savefig(bar_path, dpi=160)
    plt.close()

    LOGGER.info("Saved SHAP artifacts to %s", output_dir)
    return [str(summary_path), str(bar_path)]


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Generate SHAP artifacts for the trained railway delay model.")
    parser.add_argument("--sample-size", type=int, default=300)
    args = parser.parse_args()
    generate_shap_artifacts(sample_size=args.sample_size)


if __name__ == "__main__":
    main()

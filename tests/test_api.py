from fastapi.testclient import TestClient
import joblib


class _StaticModel:
    def predict(self, features):
        return [12.0]


def _reset_runtime_caches() -> None:
    from backend.src.core.config import get_settings
    from backend.src.models.predictor import get_prediction_engine
    from backend.src.services.analytics_repository import get_analytics_repository

    get_settings.cache_clear()
    get_analytics_repository.cache_clear()
    get_prediction_engine.cache_clear()


def test_health_endpoint_uses_baseline_when_model_is_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("FALLBACK_DATA_DIR", str(tmp_path / "missing"))
    monkeypatch.setenv("MODEL_DIR", str(tmp_path / "models"))
    monkeypatch.setenv("PROCESSED_DATA_DIR", str(tmp_path / "processed"))
    _reset_runtime_caches()

    from backend.src.main import create_app

    client = TestClient(create_app())
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["api_status"] == "online"
    assert response.json()["model_status"] == "baseline"


def test_predict_endpoint_returns_operational_category(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("FALLBACK_DATA_DIR", str(tmp_path / "missing"))
    monkeypatch.setenv("MODEL_DIR", str(tmp_path / "models"))
    monkeypatch.setenv("PROCESSED_DATA_DIR", str(tmp_path / "processed"))
    _reset_runtime_caches()

    from backend.src.main import create_app

    client = TestClient(create_app())
    response = client.post("/api/predict", json={"train_number": 12627, "station_code": "NGP", "current_delay": 15})

    assert response.status_code == 200
    payload = response.json()
    assert payload["predicted_delay"] >= 0
    assert payload["delay_category"] in {"On Time", "Minor Delay", "Moderate Delay", "Severe Delay"}


def test_model_info_uses_loaded_bundle_metadata_when_metrics_file_is_missing(monkeypatch, tmp_path) -> None:
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    metadata_path = model_dir / "metrics.json"
    bundle = {
        "model": _StaticModel(),
        "model_name": "Test Trained Model",
        "model_version": "test-version",
        "trained_at": "2026-06-20T00:00:00+00:00",
        "metrics": {"mae": 1.0, "rmse": 2.0, "r2": 0.9},
        "candidate_metrics": {"Test Trained Model": {"mae": 1.0, "rmse": 2.0, "r2": 0.9}},
        "dataset_size": 123,
        "feature_importance": [{"feature": "current_delay", "importance": 1.0}],
    }
    joblib.dump(bundle, model_dir / "train_delay_model.pkl")

    monkeypatch.setenv("DATA_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("FALLBACK_DATA_DIR", str(tmp_path / "missing"))
    monkeypatch.setenv("MODEL_DIR", str(model_dir))
    monkeypatch.setenv("PROCESSED_DATA_DIR", str(tmp_path / "processed"))
    _reset_runtime_caches()

    from backend.src.main import create_app

    client = TestClient(create_app())
    health_response = client.get("/api/health")
    model_info_response = client.get("/api/model-info")

    assert health_response.status_code == 200
    assert health_response.json()["model_status"] == "trained"
    assert model_info_response.status_code == 200
    assert model_info_response.json()["model_name"] == "Test Trained Model"
    assert model_info_response.json()["model_version"] == "test-version"
    assert model_info_response.json()["trained_at"] == "2026-06-20T00:00:00+00:00"
    assert metadata_path.exists()

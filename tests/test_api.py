from fastapi.testclient import TestClient


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

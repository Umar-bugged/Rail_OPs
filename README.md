# Train Delay Predictor

A production-style Indian Railways delay prediction system with a FastAPI backend, a training pipeline, model explainability hooks, and a React operations interface.

## What It Builds

- Predicts upcoming station arrival delay in minutes.
- Loads train, station, schedule, and delay CSVs with schema validation.
- Cleans duplicates, missing values, and delay outliers.
- Engineers time, train, route, station, and historical delay features.
- Trains Linear Regression, Random Forest, and XGBoost models, then selects the lowest-RMSE candidate.
- Serves `/health`, `/model-info`, and `/predict` through FastAPI.
- Provides railway-control-center screens for overview, prediction, network analytics, station insights, model insights, and system health.

## Dataset Assumptions

The app expects these CSVs:

| File | Required columns |
| --- | --- |
| `train_details.csv` | `train_number`, `train_name`, `train_type` |
| `station_full_names.csv` | `station_code`, `station_name`, `railway_zone`, `address` |
| `combined_schedule.csv` | `train_number`, `station_code`, `arrival_time`, `departure_time`, `arrival_day`, `station_sequence`, `distance_from_source` |
| `combined_delay.csv` | `train_number`, `station_code`, `date`, `delay_minutes` |

Joins are performed on `train_number` and `station_code`. Delay records are merged with schedule rows first, then station metadata, then train metadata. The source data does not include latitude and longitude, so the railway map uses known positions for major stations and deterministic fallback placement for all other station codes.

Your CSVs are currently in the parent `projects` folder. The backend checks both `train-delay-predictor/data/raw` and the parent folder, so you do not need to duplicate the 1 GB delay file.

## Project Structure

```text
train-delay-predictor/
  backend/src/
    api/
    core/
    data/
    features/
    models/
    services/
  data/
    raw/
    processed/
  docker/
  frontend/src/
    assets/
    components/
    hooks/
    pages/
    services/
  models/
  tests/
```

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

npm install --prefix frontend
```

Run the backend:

```bash
npm run backend:dev
```

Run the frontend:

```bash
npm run frontend:dev
```

Open `http://localhost:5173`.

## Training

The first API run works with a conservative baseline predictor. Train a production model when you are ready:

```bash
npm run train -- --max-rows 500000
```

The selected model is saved to:

```text
models/train_delay_model.pkl
```

Metrics and model registry details are saved to:

```text
models/metrics.json
```

## Explainability

After training, generate SHAP artifacts:

```bash
npm run explain -- --sample-size 300
```

Outputs are written to `models/explanations`.

## API

```http
GET /api/health
GET /api/model-info
POST /api/predict
```

Prediction input:

```json
{
  "train_number": 12627,
  "station_code": "NGP",
  "current_delay": 15
}
```

Prediction output:

```json
{
  "predicted_delay": 38,
  "confidence_score": 0.84,
  "delay_category": "Moderate Delay",
  "model_source": "trained_model"
}
```

## Docker

```bash
docker compose up --build
```

The compose file mounts the CSVs from the parent `projects` folder into the backend container.

## Tests

```bash
pytest
```

The tests use built-in sample data, so they do not need the large delay CSV.

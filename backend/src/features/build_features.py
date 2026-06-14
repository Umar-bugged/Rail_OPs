from __future__ import annotations

import pandas as pd

from backend.src.data.cleaning import (
    clean_delay_data,
    clean_schedule_data,
    clean_station_data,
    clean_train_data,
)

TARGET_COLUMN = "delay_minutes"

CATEGORICAL_FEATURES = ["station_code", "railway_zone", "train_type"]
NUMERIC_FEATURES = [
    "train_number",
    "current_delay",
    "month",
    "day_of_week",
    "weekend_flag",
    "hour_of_day",
    "station_sequence",
    "distance_from_source",
    "previous_station_delay",
    "average_delay_last_7_days",
    "average_delay_last_30_days",
    "station_average_delay",
    "train_average_delay",
    "scheduled_arrival_hour",
    "scheduled_departure_hour",
    "arrival_day",
]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def extract_hour(value: object) -> int:
    if pd.isna(value):
        return 0
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(text.split(":")[0]) % 24
    except (ValueError, TypeError):
        return 0


def _merge_sources(
    delay: pd.DataFrame,
    schedule: pd.DataFrame,
    stations: pd.DataFrame,
    trains: pd.DataFrame,
) -> pd.DataFrame:
    delay = clean_delay_data(delay)
    schedule = clean_schedule_data(schedule)
    stations = clean_station_data(stations)
    trains = clean_train_data(trains)

    merged = delay.merge(schedule, on=["train_number", "station_code"], how="left")
    merged = merged.merge(stations, on="station_code", how="left")
    merged = merged.merge(trains, on="train_number", how="left")
    return merged


def prepare_training_frame(
    delay: pd.DataFrame,
    schedule: pd.DataFrame,
    stations: pd.DataFrame,
    trains: pd.DataFrame,
) -> pd.DataFrame:
    frame = _merge_sources(delay, schedule, stations, trains)
    frame = frame.sort_values(["train_number", "date", "station_sequence"], na_position="last")

    frame["month"] = frame["date"].dt.month
    frame["day_of_week"] = frame["date"].dt.dayofweek
    frame["weekend_flag"] = frame["day_of_week"].isin([5, 6]).astype(int)
    frame["scheduled_arrival_hour"] = frame["arrival_time"].map(extract_hour)
    frame["scheduled_departure_hour"] = frame["departure_time"].map(extract_hour)
    frame["hour_of_day"] = frame["scheduled_arrival_hour"]

    frame["previous_station_delay"] = frame.groupby(["train_number", "date"], observed=True)[TARGET_COLUMN].shift(1)
    frame["average_delay_last_7_days"] = frame.groupby("train_number", observed=True)[TARGET_COLUMN].transform(
        lambda series: series.shift().rolling(7, min_periods=1).mean()
    )
    frame["average_delay_last_30_days"] = frame.groupby("train_number", observed=True)[TARGET_COLUMN].transform(
        lambda series: series.shift().rolling(30, min_periods=1).mean()
    )
    frame["station_average_delay"] = frame.groupby("station_code", observed=True)[TARGET_COLUMN].transform(
        lambda series: series.shift().expanding(min_periods=1).mean()
    )
    frame["train_average_delay"] = frame.groupby("train_number", observed=True)[TARGET_COLUMN].transform(
        lambda series: series.shift().expanding(min_periods=1).mean()
    )

    global_delay = float(frame[TARGET_COLUMN].mean()) if not frame.empty else 0.0
    fill_values = {
        "current_delay": frame["previous_station_delay"],
        "previous_station_delay": global_delay,
        "average_delay_last_7_days": global_delay,
        "average_delay_last_30_days": global_delay,
        "station_average_delay": global_delay,
        "train_average_delay": global_delay,
        "station_sequence": frame["station_sequence"].median(),
        "distance_from_source": frame["distance_from_source"].median(),
        "arrival_day": 1,
        "railway_zone": "UNKNOWN",
        "train_type": "Unknown",
    }

    frame["current_delay"] = frame["previous_station_delay"]
    for column, value in fill_values.items():
        frame[column] = frame[column].fillna(value)

    for column in CATEGORICAL_FEATURES:
        frame[column] = frame[column].fillna("UNKNOWN").astype(str)
    for column in NUMERIC_FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)

    return frame[FEATURE_COLUMNS + [TARGET_COLUMN]].dropna(subset=[TARGET_COLUMN])


def build_prediction_features(
    train_number: int,
    station_code: str,
    current_delay: float,
    profile: dict[str, object],
) -> pd.DataFrame:
    month = int(profile.get("month", pd.Timestamp.utcnow().month))
    day_of_week = int(profile.get("day_of_week", pd.Timestamp.utcnow().dayofweek))
    scheduled_arrival_hour = int(profile.get("scheduled_arrival_hour", profile.get("hour_of_day", 0)))
    scheduled_departure_hour = int(profile.get("scheduled_departure_hour", scheduled_arrival_hour))

    row = {
        "train_number": train_number,
        "current_delay": current_delay,
        "month": month,
        "day_of_week": day_of_week,
        "weekend_flag": int(day_of_week in [5, 6]),
        "hour_of_day": scheduled_arrival_hour,
        "station_sequence": float(profile.get("station_sequence", 0)),
        "distance_from_source": float(profile.get("distance_from_source", 0)),
        "previous_station_delay": float(profile.get("previous_station_delay", current_delay)),
        "average_delay_last_7_days": float(profile.get("average_delay_last_7_days", current_delay)),
        "average_delay_last_30_days": float(profile.get("average_delay_last_30_days", current_delay)),
        "station_average_delay": float(profile.get("station_average_delay", current_delay)),
        "train_average_delay": float(profile.get("train_average_delay", current_delay)),
        "scheduled_arrival_hour": scheduled_arrival_hour,
        "scheduled_departure_hour": scheduled_departure_hour,
        "arrival_day": int(profile.get("arrival_day", 1)),
        "station_code": station_code.upper(),
        "railway_zone": str(profile.get("railway_zone", "UNKNOWN")),
        "train_type": str(profile.get("train_type", "Unknown")),
    }
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)

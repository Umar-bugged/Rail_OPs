from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from backend.src.core.config import Settings, get_settings
from backend.src.data import sample_data

LOGGER = logging.getLogger(__name__)

REQUIRED_SCHEMAS: dict[str, set[str]] = {
    "train_details.csv": {"train_number", "train_name", "train_type"},
    "station_full_names.csv": {"station_code", "station_name", "railway_zone", "address"},
    "combined_schedule.csv": {
        "train_number",
        "station_code",
        "arrival_time",
        "departure_time",
        "arrival_day",
        "station_sequence",
        "distance_from_source",
    },
    "combined_delay.csv": {"train_number", "station_code", "date", "delay_minutes"},
}

COLUMN_ALIASES: dict[str, dict[str, str]] = {
    "train_details.csv": {
        "train_no": "train_number",
        "type_code": "train_type",
    },
    "station_full_names.csv": {
        "station_name": "station_code",
        "station_full_name": "station_name",
        "station_zone": "railway_zone",
        "station_address": "address",
    },
    "combined_schedule.csv": {
        "train_no": "train_number",
        "station_name": "station_code",
        "station_no": "station_sequence",
        "distance_from_origin": "distance_from_source",
    },
    "combined_delay.csv": {
        "train_no": "train_number",
        "station_name": "station_code",
        "delay": "delay_minutes",
    },
}


@dataclass(frozen=True)
class DataPaths:
    train_details: Path | None
    stations: Path | None
    schedule: Path | None
    delay: Path | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "train_details": str(self.train_details) if self.train_details else None,
            "stations": str(self.stations) if self.stations else None,
            "schedule": str(self.schedule) if self.schedule else None,
            "delay": str(self.delay) if self.delay else None,
        }


def _candidate_roots(settings: Settings) -> list[Path]:
    return [settings.data_dir, settings.fallback_data_dir, settings.fallback_data_dir / "data" / "raw"]


def _find_file(filename: str, settings: Settings) -> Path | None:
    for root in _candidate_roots(settings):
        candidate = root / filename
        if candidate.exists():
            return candidate
    return None


def resolve_data_paths(settings: Settings | None = None) -> DataPaths:
    settings = settings or get_settings()
    return DataPaths(
        train_details=_find_file("train_details.csv", settings),
        stations=_find_file("station_full_names.csv", settings),
        schedule=_find_file("combined_schedule.csv", settings),
        delay=_find_file("combined_delay.csv", settings),
    )


def validate_schema(frame: pd.DataFrame, filename: str) -> None:
    required = REQUIRED_SCHEMAS[filename]
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{filename} is missing required columns: {sorted(missing)}")


def normalize_columns(frame: pd.DataFrame, filename: str) -> pd.DataFrame:
    aliases = COLUMN_ALIASES.get(filename, {})
    normalized = frame.rename(columns={source: target for source, target in aliases.items() if source in frame.columns})
    validate_schema(normalized, filename)
    return normalized


def _read_csv_or_sample(path: Path | None, filename: str) -> pd.DataFrame:
    if path is None:
        LOGGER.warning("%s not found. Using built-in sample data.", filename)
        if filename == "train_details.csv":
            return sample_data.sample_trains()
        if filename == "station_full_names.csv":
            return sample_data.sample_stations()
        if filename == "combined_schedule.csv":
            return sample_data.sample_schedule()
        if filename == "combined_delay.csv":
            return sample_data.sample_delay()
        raise FileNotFoundError(filename)

    frame = pd.read_csv(path)
    return normalize_columns(frame, filename)


def load_reference_data(paths: DataPaths | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paths = paths or resolve_data_paths()
    trains = _read_csv_or_sample(paths.train_details, "train_details.csv")
    stations = _read_csv_or_sample(paths.stations, "station_full_names.csv")
    schedule = _read_csv_or_sample(paths.schedule, "combined_schedule.csv")
    return trains, stations, schedule


def iter_delay_chunks(
    paths: DataPaths | None = None,
    chunk_size: int | None = None,
    max_rows: int | None = None,
) -> Iterable[pd.DataFrame]:
    settings = get_settings()
    paths = paths or resolve_data_paths(settings)
    chunk_size = chunk_size or settings.delay_chunk_size

    if paths.delay is None:
        yield sample_data.sample_delay()
        return

    rows_read = 0
    for chunk in pd.read_csv(paths.delay, chunksize=chunk_size):
        chunk = normalize_columns(chunk, "combined_delay.csv")
        if max_rows is not None:
            remaining = max_rows - rows_read
            if remaining <= 0:
                break
            chunk = chunk.head(remaining)
        rows_read += len(chunk)
        yield chunk
        if max_rows is not None and rows_read >= max_rows:
            break


def load_delay_sample(paths: DataPaths | None = None, max_rows: int | None = None) -> pd.DataFrame:
    settings = get_settings()
    max_rows = max_rows or settings.max_analytics_rows
    chunks = list(iter_delay_chunks(paths=paths, chunk_size=settings.delay_chunk_size, max_rows=max_rows))
    if not chunks:
        return sample_data.sample_delay()
    return pd.concat(chunks, ignore_index=True)

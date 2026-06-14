from __future__ import annotations

import pandas as pd

TRAIN_TYPE_MAP = {
    "PASS": "Passenger",
    "PAS": "Passenger",
    "EMU": "Passenger",
    "MEMU": "Passenger",
    "DEMU": "Passenger",
    "EXP": "Express",
    "MEX": "Express",
    "MAIL": "Express",
    "SF": "Superfast",
    "SUF": "Superfast",
    "RAJ": "Rajdhani",
    "RAJDHANI": "Rajdhani",
    "SHT": "Shatabdi",
    "SHATABDI": "Shatabdi",
    "VB": "Vande Bharat",
    "VANDE": "Vande Bharat",
    "SF-TRAINS": "Superfast",
    "MAIL/EXP": "Express",
    "EXPRESS": "Express",
    "PASSENGER": "Passenger",
}


def normalize_station_codes(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper()


def normalize_train_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def clean_delay_data(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned["train_number"] = normalize_train_number(cleaned["train_number"])
    cleaned["station_code"] = normalize_station_codes(cleaned["station_code"])
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    cleaned["delay_minutes"] = pd.to_numeric(cleaned["delay_minutes"], errors="coerce")
    cleaned = cleaned.dropna(subset=["train_number", "station_code", "date", "delay_minutes"])
    cleaned = cleaned.drop_duplicates(subset=["train_number", "station_code", "date"])

    if not cleaned.empty:
        high_clip = cleaned["delay_minutes"].quantile(0.995)
        cleaned["delay_minutes"] = cleaned["delay_minutes"].clip(lower=0, upper=max(120, high_clip))

    return cleaned


def clean_schedule_data(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned["train_number"] = normalize_train_number(cleaned["train_number"])
    cleaned["station_code"] = normalize_station_codes(cleaned["station_code"])
    cleaned["station_sequence"] = pd.to_numeric(cleaned["station_sequence"], errors="coerce")
    cleaned["distance_from_source"] = pd.to_numeric(cleaned["distance_from_source"], errors="coerce")
    cleaned["arrival_day"] = pd.to_numeric(cleaned["arrival_day"], errors="coerce").fillna(1)
    cleaned = cleaned.dropna(subset=["train_number", "station_code", "station_sequence"])
    cleaned = cleaned.drop_duplicates(subset=["train_number", "station_code", "station_sequence"])
    return cleaned


def clean_station_data(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned["station_code"] = normalize_station_codes(cleaned["station_code"])
    cleaned["station_name"] = cleaned["station_name"].fillna(cleaned["station_code"]).astype(str)
    cleaned["railway_zone"] = cleaned["railway_zone"].fillna("UNKNOWN").astype(str).str.upper()
    cleaned["address"] = cleaned["address"].fillna("").astype(str)
    return cleaned.drop_duplicates(subset=["station_code"])


def clean_train_data(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned["train_number"] = normalize_train_number(cleaned["train_number"])
    cleaned["train_name"] = cleaned["train_name"].fillna("Unknown Train").astype(str)
    type_code = cleaned["train_type"].fillna("Unknown").astype(str).str.strip()
    normalized_type = type_code.str.upper()
    cleaned["train_type"] = normalized_type.map(TRAIN_TYPE_MAP).fillna(type_code)
    cleaned.loc[normalized_type.str.contains("VANDE|VB", regex=True, na=False), "train_type"] = "Vande Bharat"
    cleaned.loc[normalized_type.str.contains("RAJ", regex=True, na=False), "train_type"] = "Rajdhani"
    cleaned.loc[normalized_type.str.contains("SHATABDI|SHT", regex=True, na=False), "train_type"] = "Shatabdi"
    cleaned.loc[normalized_type.str.contains("SUPER|\\bSF\\b", regex=True, na=False), "train_type"] = "Superfast"
    cleaned.loc[normalized_type.str.contains("EXP|MAIL", regex=True, na=False), "train_type"] = "Express"
    cleaned.loc[normalized_type.str.contains("PASS|MEMU|DEMU|EMU", regex=True, na=False), "train_type"] = "Passenger"
    return cleaned.dropna(subset=["train_number"]).drop_duplicates(subset=["train_number"])

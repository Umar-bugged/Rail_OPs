from __future__ import annotations

import pandas as pd


def sample_trains() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"train_number": 12627, "train_name": "Karnataka Express", "train_type": "Express"},
            {"train_number": 12951, "train_name": "Mumbai Rajdhani", "train_type": "Rajdhani"},
            {"train_number": 12002, "train_name": "Shatabdi Express", "train_type": "Shatabdi"},
            {"train_number": 22435, "train_name": "Vande Bharat Express", "train_type": "Vande Bharat"},
            {"train_number": 11013, "train_name": "Coimbatore Express", "train_type": "Superfast"},
        ]
    )


def sample_stations() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"station_code": "NDLS", "station_name": "New Delhi", "railway_zone": "NR", "address": "Delhi"},
            {"station_code": "NGP", "station_name": "Nagpur", "railway_zone": "CR", "address": "Maharashtra"},
            {"station_code": "BPL", "station_name": "Bhopal", "railway_zone": "WCR", "address": "Madhya Pradesh"},
            {"station_code": "CSMT", "station_name": "Mumbai CSMT", "railway_zone": "CR", "address": "Maharashtra"},
            {"station_code": "SBC", "station_name": "KSR Bengaluru", "railway_zone": "SWR", "address": "Karnataka"},
            {"station_code": "MAS", "station_name": "Chennai Central", "railway_zone": "SR", "address": "Tamil Nadu"},
            {"station_code": "HWH", "station_name": "Howrah", "railway_zone": "ER", "address": "West Bengal"},
        ]
    )


def sample_schedule() -> pd.DataFrame:
    rows = []
    routes = {
        12627: ["SBC", "MAS", "NGP", "BPL", "NDLS"],
        12951: ["CSMT", "BPL", "NDLS"],
        12002: ["NDLS", "BPL", "NGP"],
        22435: ["NDLS", "BPL", "NGP", "MAS"],
        11013: ["CSMT", "NGP", "MAS", "SBC"],
    }
    for train_number, stations in routes.items():
        for index, station_code in enumerate(stations, start=1):
            rows.append(
                {
                    "train_number": train_number,
                    "station_code": station_code,
                    "arrival_time": f"{6 + index:02d}:15",
                    "departure_time": f"{6 + index:02d}:25",
                    "arrival_day": 1 if index < 4 else 2,
                    "station_sequence": index,
                    "distance_from_source": (index - 1) * 345,
                }
            )
    return pd.DataFrame(rows)


def sample_delay() -> pd.DataFrame:
    rows = []
    dates = pd.date_range("2026-04-01", periods=35, freq="D")
    base = {"NDLS": 18, "NGP": 32, "BPL": 24, "CSMT": 14, "SBC": 11, "MAS": 21, "HWH": 28}
    for day_index, date in enumerate(dates):
        for train_number in [12627, 12951, 12002, 22435, 11013]:
            for station_code, station_base in base.items():
                if (train_number + day_index + len(station_code)) % 3 == 0:
                    delay = station_base + ((train_number % 17) - 6) + (day_index % 9)
                    rows.append(
                        {
                            "train_number": train_number,
                            "station_code": station_code,
                            "date": date.date().isoformat(),
                            "delay_minutes": max(0, delay),
                        }
                    )
    return pd.DataFrame(rows)

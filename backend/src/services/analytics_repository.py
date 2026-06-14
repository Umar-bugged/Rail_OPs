from __future__ import annotations

import json
from pathlib import Path

import logging
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from backend.src.core.config import Settings, get_settings
from backend.src.data.cleaning import (
    clean_delay_data,
    clean_schedule_data,
    clean_station_data,
    clean_train_data,
)
from backend.src.data.loader import load_delay_sample, load_reference_data, resolve_data_paths
from backend.src.features.build_features import extract_hour

LOGGER = logging.getLogger(__name__)

KNOWN_STATION_POSITIONS: dict[str, tuple[float, float]] = {
    "NDLS": (39, 27),
    "DLI": (39, 28),
    "JP": (32, 38),
    "ADI": (25, 50),
    "BPL": (42, 51),
    "NGP": (51, 58),
    "CSMT": (31, 67),
    "BCT": (30, 65),
    "PUNE": (34, 69),
    "SBC": (43, 82),
    "MAS": (57, 82),
    "BZA": (61, 70),
    "SC": (47, 69),
    "HWH": (72, 52),
    "SDAH": (72, 52),
    "LKO": (49, 36),
    "CNB": (48, 40),
    "PRYJ": (54, 43),
    "ALD": (54, 43),
    "GHY": (86, 39),
    "TVC": (45, 93),
}


@dataclass
class AnalyticsRepository:
    settings: Settings

    def __post_init__(self) -> None:
        self._snapshot: dict[str, object] | None = None

    def snapshot(self) -> dict[str, object]:
        if self._snapshot is None:
            self._snapshot = self._build_snapshot()
        return self._snapshot

    def station_profile(self, station_code: str) -> dict[str, object]:
        station_code = station_code.upper()
        snapshot = self.snapshot()
        station_index = snapshot["station_index"]
        if isinstance(station_index, dict) and station_code in station_index:
            return station_index[station_code]

        return {
            "station_code": station_code,
            "station_name": station_code,
            "railway_zone": "UNKNOWN",
            "address": "",
            "historical_average_delay": 0,
            "delay_trends": [],
            "top_delayed_trains": [],
        }

    def train_profile(self, train_number: int) -> dict[str, object]:
        snapshot = self.snapshot()
        train_index = snapshot.get("train_index", {})
        route_index = snapshot.get("train_route_index", {})
        key = str(train_number)
        if isinstance(train_index, dict) and key in train_index:
            train = train_index[key]
            route = route_index.get(key, []) if isinstance(route_index, dict) else []
            top_delayed_stations = sorted(
                [station for station in route if float(station.get("average_delay", 0) or 0) > 0],
                key=lambda station: float(station.get("average_delay", 0) or 0),
                reverse=True,
            )[:8]
            return {
                "train_number": train_number,
                "train_name": train.get("train_name", "Unknown Train"),
                "train_type": train.get("train_type", "Unknown"),
                "train_average_delay": train.get("train_average_delay", 0),
                "average_delay_last_7_days": train.get("average_delay_last_7_days", 0),
                "average_delay_last_30_days": train.get("average_delay_last_30_days", 0),
                "route_stations": route,
                "top_delayed_stations": top_delayed_stations,
            }

        return {
            "train_number": train_number,
            "train_name": "Unknown Train",
            "train_type": "Unknown",
            "train_average_delay": 0,
            "average_delay_last_7_days": 0,
            "average_delay_last_30_days": 0,
            "route_stations": [],
            "top_delayed_stations": [],
        }

    def search_stations(self, query: str, limit: int = 8) -> list[dict[str, object]]:
        query = query.strip().upper()

        if not query:
            return []

        lookup_file = Path("data/lookups/stations.json")

        if not lookup_file.exists():
            LOGGER.warning("stations.json not found at %s", lookup_file)
            return []

        try:
            stations = json.loads(lookup_file.read_text(encoding="utf-8"))
        except Exception as exc:
            LOGGER.error("Failed to load stations lookup file: %s", exc)
            return []

        matches = []

        for station in stations:
            code = str(station.get("station_name", "")).upper()
            name = str(station.get("station_full_name", "")).upper()

            if query in code or query in name:
                score = 0 if code.startswith(query) else 1 if name.startswith(query) else 2

                matches.append(
                    (
                        score,
                        code,
                        {
                            "station_code": station.get("station_name"),
                            "station_name": station.get("station_full_name"),
                            "railway_zone": "",
                            "historical_average_delay": 0,
                        },
                    )
                )

        return [
            station
            for _, _, station in sorted(matches, key=lambda item: (item[0], item[1]))[:limit]
        ]

    def search_trains(self, query: str, limit: int = 8) -> list[dict[str, object]]:
        query = query.strip().upper()

        if not query:
            return []

        lookup_file = Path("data/lookups/trains.json")

        if not lookup_file.exists():
            LOGGER.warning("trains.json not found at %s", lookup_file)
            return []

        try:
            trains = json.loads(lookup_file.read_text(encoding="utf-8"))
        except Exception as exc:
            LOGGER.error("Failed to load trains lookup file: %s", exc)
            return []

        matches = []

        for train in trains:
            number = str(train.get("train_no", ""))
            name = str(train.get("train_name", "")).upper()

            if query in number or query in name:
                score = 0 if number.startswith(query) else 1 if name.startswith(query) else 2

                matches.append(
                    (
                        score,
                        number,
                        {
                            "train_number": int(train.get("train_no", 0)),
                            "train_name": train.get("train_name", "Unknown Train"),
                            "train_type": "",
                            "train_average_delay": 0,
                        },
                    )
                )

        return [
            train
            for _, _, train in sorted(matches, key=lambda item: (item[0], item[1]))[:limit]
        ]

    def prediction_profile(self, train_number: int, station_code: str, current_delay: float) -> dict[str, object]:
        snapshot = self.snapshot()
        station = self.station_profile(station_code)
        schedule_index = snapshot.get("schedule_index", {})
        train_index = snapshot.get("train_index", {})
        key = f"{train_number}:{station_code.upper()}"
        schedule_row = schedule_index.get(key, {}) if isinstance(schedule_index, dict) else {}
        train_row = train_index.get(str(train_number), {}) if isinstance(train_index, dict) else {}

        station_avg = float(station.get("historical_average_delay", current_delay))
        train_avg = float(train_row.get("train_average_delay", station_avg))
        return {
            "railway_zone": station.get("railway_zone", "UNKNOWN"),
            "train_type": train_row.get("train_type", "Unknown"),
            "station_sequence": schedule_row.get("station_sequence", 0),
            "distance_from_source": schedule_row.get("distance_from_source", 0),
            "scheduled_arrival_hour": schedule_row.get("scheduled_arrival_hour", 0),
            "scheduled_departure_hour": schedule_row.get("scheduled_departure_hour", 0),
            "arrival_day": schedule_row.get("arrival_day", 1),
            "previous_station_delay": current_delay,
            "average_delay_last_7_days": train_row.get("average_delay_last_7_days", train_avg),
            "average_delay_last_30_days": train_row.get("average_delay_last_30_days", train_avg),
            "station_average_delay": station_avg,
            "train_average_delay": train_avg,
        }

    def _build_snapshot(self) -> dict[str, object]:
        paths = resolve_data_paths(self.settings)
        trains_raw, stations_raw, schedule_raw = load_reference_data(paths)
        delay_raw = load_delay_sample(paths, max_rows=self.settings.max_analytics_rows)

        trains = clean_train_data(trains_raw)
        stations = clean_station_data(stations_raw)
        schedule = clean_schedule_data(schedule_raw)
        delay = clean_delay_data(delay_raw)

        merged = delay.merge(schedule, on=["train_number", "station_code"], how="left")
        merged = merged.merge(stations, on="station_code", how="left")
        merged = merged.merge(trains, on="train_number", how="left")
        merged["date"] = pd.to_datetime(merged["date"], errors="coerce")
        merged["railway_zone"] = merged["railway_zone"].fillna("UNKNOWN")
        merged["train_type"] = merged["train_type"].fillna("Unknown")

        return {
            "overview": self._overview(trains, stations, merged),
            "network": self._network(stations, schedule, merged),
            "trends": self._trends(merged),
            "heatmap": self._heatmap(merged),
            "zone_performance": self._zone_performance(merged),
            "route_congestion": self._route_congestion(schedule, merged),
            "train_type_analysis": self._train_type_analysis(merged),
            "station_index": self._station_index(stations, merged),
            "schedule_index": self._schedule_index(schedule),
            "train_index": self._train_index(trains, merged),
            "train_route_index": self._train_route_index(schedule, stations, merged),
            "data_paths": paths.as_dict(),
            "dataset_size": int(len(delay)),
        }

    def _overview(self, trains: pd.DataFrame, stations: pd.DataFrame, merged: pd.DataFrame) -> dict[str, object]:
        zone_delay = merged.groupby("railway_zone", dropna=False)["delay_minutes"].mean().sort_values(ascending=False)
        return {
            "total_trains": int(trains["train_number"].nunique()),
            "total_stations": int(stations["station_code"].nunique()),
            "average_delay": round(float(merged["delay_minutes"].mean()), 2) if not merged.empty else 0,
            "most_delayed_zone": str(zone_delay.index[0]) if len(zone_delay) else "UNKNOWN",
        }

    def _trends(self, merged: pd.DataFrame) -> list[dict[str, object]]:
        if merged.empty:
            return []
        daily = (
            merged.dropna(subset=["date"])
            .groupby(pd.Grouper(key="date", freq="D"))["delay_minutes"]
            .mean()
            .tail(45)
            .reset_index()
        )
        daily["weekly_average_delay"] = daily["delay_minutes"].rolling(7, min_periods=1).mean()
        return [
            {
                "date": row["date"].date().isoformat(),
                "daily_average_delay": round(float(row["delay_minutes"]), 2),
                "weekly_average_delay": round(float(row["weekly_average_delay"]), 2),
            }
            for _, row in daily.iterrows()
        ]

    def _network(self, stations: pd.DataFrame, schedule: pd.DataFrame, merged: pd.DataFrame) -> dict[str, object]:
        station_delay = merged.groupby("station_code")["delay_minutes"].mean().to_dict()
        active_stations = stations[stations["station_code"].isin(set(schedule["station_code"].dropna()))].head(90)
        nodes = []
        for _, row in active_stations.iterrows():
            code = str(row["station_code"])
            x, y = self._station_position(code)
            nodes.append(
                {
                    "id": code,
                    "name": row["station_name"],
                    "zone": row["railway_zone"],
                    "x": x,
                    "y": y,
                    "average_delay": round(float(station_delay.get(code, 0)), 2),
                }
            )

        edge_counts: dict[tuple[str, str], int] = {}
        ordered = schedule.sort_values(["train_number", "station_sequence"])
        ordered["next_station"] = ordered.groupby("train_number", observed=True)["station_code"].shift(-1)
        for _, row in ordered.dropna(subset=["next_station"]).head(6000).iterrows():
            source = str(row["station_code"])
            target = str(row["next_station"])
            if source != target:
                edge_counts[(source, target)] = edge_counts.get((source, target), 0) + 1

        edges = [
            {"source": source, "target": target, "trains": count}
            for (source, target), count in sorted(edge_counts.items(), key=lambda item: item[1], reverse=True)[:130]
        ]
        return {"nodes": nodes, "edges": edges}

    def _station_position(self, station_code: str) -> tuple[float, float]:
        if station_code in KNOWN_STATION_POSITIONS:
            return KNOWN_STATION_POSITIONS[station_code]
        seed = sum((index + 1) * ord(char) for index, char in enumerate(station_code))
        return 22 + (seed % 58), 24 + ((seed // 7) % 66)

    def _heatmap(self, merged: pd.DataFrame) -> list[dict[str, object]]:
        if merged.empty:
            return []
        top_stations = (
            merged.groupby("station_code")["delay_minutes"].mean().sort_values(ascending=False).head(18).index.tolist()
        )
        working = merged[merged["station_code"].isin(top_stations)].copy()
        working["day"] = working["date"].dt.day_name().str.slice(0, 3)
        heatmap = working.groupby(["station_code", "day"])["delay_minutes"].mean().reset_index()
        return [
            {"station": row["station_code"], "day": row["day"], "delay": round(float(row["delay_minutes"]), 1)}
            for _, row in heatmap.iterrows()
        ]

    def _zone_performance(self, merged: pd.DataFrame) -> list[dict[str, object]]:
        zone = (
            merged.groupby("railway_zone")["delay_minutes"]
            .agg(["mean", "count"])
            .sort_values("mean", ascending=False)
            .head(16)
            .reset_index()
        )
        return [
            {
                "zone": row["railway_zone"],
                "average_delay": round(float(row["mean"]), 2),
                "records": int(row["count"]),
            }
            for _, row in zone.iterrows()
        ]

    def _route_congestion(self, schedule: pd.DataFrame, merged: pd.DataFrame) -> list[dict[str, object]]:
        ordered = schedule.sort_values(["train_number", "station_sequence"]).copy()
        ordered["next_station"] = ordered.groupby("train_number", observed=True)["station_code"].shift(-1)
        route_rows = ordered.dropna(subset=["next_station"])[["train_number", "station_code", "next_station"]]
        route_delay = merged.groupby(["train_number", "station_code"])["delay_minutes"].mean().reset_index()
        route_rows = route_rows.merge(route_delay, on=["train_number", "station_code"], how="left")
        summary = (
            route_rows.groupby(["station_code", "next_station"])["delay_minutes"]
            .agg(["mean", "count"])
            .dropna()
            .sort_values("mean", ascending=False)
            .head(12)
            .reset_index()
        )
        return [
            {
                "source": row["station_code"],
                "target": row["next_station"],
                "average_delay": round(float(row["mean"]), 2),
                "train_count": int(row["count"]),
            }
            for _, row in summary.iterrows()
        ]

    def _train_type_analysis(self, merged: pd.DataFrame) -> list[dict[str, object]]:
        order = ["Passenger", "Express", "Superfast", "Rajdhani", "Shatabdi", "Vande Bharat"]
        grouped = merged.groupby("train_type")["delay_minutes"].agg(["mean", "count"]).reset_index()
        rows = []
        for train_type in order:
            match = grouped[grouped["train_type"].str.contains(train_type, case=False, na=False)]
            if match.empty:
                rows.append({"train_type": train_type, "average_delay": 0, "records": 0})
            else:
                rows.append(
                    {
                        "train_type": train_type,
                        "average_delay": round(float(match["mean"].mean()), 2),
                        "records": int(match["count"].sum()),
                    }
                )
        return rows

    def _station_index(self, stations: pd.DataFrame, merged: pd.DataFrame) -> dict[str, dict[str, object]]:
        delay_by_station = merged.groupby("station_code")["delay_minutes"].mean().to_dict()
        trend_by_station: dict[str, list[dict[str, object]]] = {}
        if not merged.empty:
            trend_source = (
                merged.dropna(subset=["date"])
                .groupby(["station_code", pd.Grouper(key="date", freq="D")])["delay_minutes"]
                .mean()
                .reset_index()
                .sort_values(["station_code", "date"])
            )
            for code, rows in trend_source.groupby("station_code", observed=True):
                trend_by_station[str(code)] = [
                    {
                        "date": row["date"].date().isoformat(),
                        "average_delay": round(float(row["delay_minutes"]), 2),
                    }
                    for _, row in rows.tail(18).iterrows()
                ]

        top_by_station: dict[str, list[dict[str, object]]] = {}
        if not merged.empty:
            top_source = (
                merged.assign(train_name=merged["train_name"].fillna("Unknown Train"))
                .groupby(["station_code", "train_number", "train_name"])["delay_minutes"]
                .mean()
                .reset_index()
                .sort_values(["station_code", "delay_minutes"], ascending=[True, False])
            )
            for code, rows in top_source.groupby("station_code", observed=True):
                top_by_station[str(code)] = [
                    {
                        "train_number": int(row["train_number"]),
                        "train_name": row["train_name"],
                        "average_delay": round(float(row["delay_minutes"]), 2),
                    }
                    for _, row in rows.head(8).iterrows()
                ]

        result: dict[str, dict[str, object]] = {}
        for _, station in stations.iterrows():
            code = str(station["station_code"])
            result[code] = {
                "station_code": code,
                "station_name": station["station_name"],
                "railway_zone": station["railway_zone"],
                "address": station["address"],
                "historical_average_delay": round(float(delay_by_station.get(code, 0)), 2),
                "delay_trends": trend_by_station.get(code, []),
                "top_delayed_trains": top_by_station.get(code, []),
            }
        return result

    def _schedule_index(self, schedule: pd.DataFrame) -> dict[str, dict[str, object]]:
        result = {}
        for _, row in schedule.iterrows():
            key = f"{int(row['train_number'])}:{row['station_code']}"
            result[key] = {
                "station_sequence": float(row.get("station_sequence", 0)),
                "distance_from_source": float(row.get("distance_from_source", 0)),
                "scheduled_arrival_hour": extract_hour(row.get("arrival_time")),
                "scheduled_departure_hour": extract_hour(row.get("departure_time")),
                "arrival_day": int(row.get("arrival_day", 1) or 1),
            }
        return result

    def _train_index(self, trains: pd.DataFrame, merged: pd.DataFrame) -> dict[str, dict[str, object]]:
        train_avg = merged.groupby("train_number")["delay_minutes"].mean().to_dict()
        ordered = merged.sort_values("date")
        train_7 = (
            ordered.groupby("train_number", observed=True).tail(7).groupby("train_number")["delay_minutes"].mean().to_dict()
            if not merged.empty
            else {}
        )
        train_30 = (
            ordered.groupby("train_number", observed=True).tail(30).groupby("train_number")["delay_minutes"].mean().to_dict()
            if not merged.empty
            else {}
        )
        result = {}
        for _, row in trains.iterrows():
            train_number = int(row["train_number"])
            result[str(train_number)] = {
                "train_name": row["train_name"],
                "train_type": row["train_type"],
                "train_average_delay": round(float(train_avg.get(train_number, 0)), 2),
                "average_delay_last_7_days": round(float(train_7.get(train_number, train_avg.get(train_number, 0))), 2),
                "average_delay_last_30_days": round(float(train_30.get(train_number, train_avg.get(train_number, 0))), 2),
            }
        return result

    def _train_route_index(
        self,
        schedule: pd.DataFrame,
        stations: pd.DataFrame,
        merged: pd.DataFrame,
    ) -> dict[str, list[dict[str, object]]]:
        station_lookup = stations.set_index("station_code")[["station_name", "railway_zone"]].to_dict(orient="index")
        delay_lookup = merged.groupby(["train_number", "station_code"])["delay_minutes"].mean().to_dict()
        route_index: dict[str, list[dict[str, object]]] = {}

        ordered = schedule.sort_values(["train_number", "station_sequence"])
        for train_number, rows in ordered.groupby("train_number", observed=True):
            route = []
            for _, row in rows.iterrows():
                station_code = str(row["station_code"])
                station = station_lookup.get(station_code, {})
                sequence = row.get("station_sequence", 0)
                distance = row.get("distance_from_source", 0)
                route.append(
                    {
                        "station_code": station_code,
                        "station_name": station.get("station_name", station_code),
                        "railway_zone": station.get("railway_zone", "UNKNOWN"),
                        "station_sequence": int(sequence) if pd.notna(sequence) else 0,
                        "distance_from_source": float(distance) if pd.notna(distance) else 0,
                        "average_delay": round(float(delay_lookup.get((train_number, station_code), 0)), 2),
                    }
                )
            route_index[str(int(train_number))] = route

        return route_index


@lru_cache
def get_analytics_repository() -> AnalyticsRepository:
    return AnalyticsRepository(settings=get_settings())

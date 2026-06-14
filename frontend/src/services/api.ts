import axios from "axios";

import * as mock from "./mockData";
import type {
  Health,
  HeatmapPoint,
  ModelInfo,
  NetworkEdge,
  NetworkNode,
  Overview,
  PredictionResponse,
  RouteCongestion,
  StationProfile,
  StationSuggestion,
  TrainTypeAnalysis,
  TrainProfile,
  TrainSuggestion,
  TrendPoint,
  ZonePerformance
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api",
  timeout: 7000
});

async function withFallback<T>(request: Promise<{ data: T }>, fallback: T): Promise<T> {
  try {
    const response = await request;
    return response.data;
  } catch {
    return fallback;
  }
}

export function getOverview(): Promise<{ overview: Overview; trends: TrendPoint[] }> {
  return withFallback(api.get("/analytics/overview"), { overview: mock.overview, trends: mock.trends });
}

export function predictDelay(payload: {
  train_number: number;
  station_code: string;
  current_delay: number;
}): Promise<PredictionResponse> {
  return withFallback(api.post("/predict", payload), {
    predicted_delay: Math.round(payload.current_delay * 0.72 + 18),
    confidence_score: 0.68,
    delay_category: payload.current_delay > 45 ? "Severe Delay" : payload.current_delay > 20 ? "Moderate Delay" : "Minor Delay",
    model_source: "frontend_baseline"
  });
}

export function getStationProfile(stationCode: string): Promise<StationProfile> {
  return withFallback(api.get(`/analytics/stations/${stationCode.toUpperCase()}`), {
    ...mock.stationProfile,
    station_code: stationCode.toUpperCase()
  });
}

export function getTrainProfile(trainNumber: string | number): Promise<TrainProfile> {
  return withFallback(api.get(`/analytics/trains/${trainNumber}`), {
    ...mock.trainProfile,
    train_number: Number(trainNumber) || mock.trainProfile.train_number
  });
}

export function searchStations(query: string): Promise<StationSuggestion[]> {
  const normalized = query.trim();
  if (!normalized) {
    return Promise.resolve([]);
  }
  const fallback = mock.stationSuggestions.filter((station) => {
    const searchable = `${station.station_code} ${station.station_name}`.toUpperCase();
    return searchable.includes(normalized.toUpperCase());
  });
  return withFallback(api.get(`/search/stations`, { params: { q: normalized, limit: 8 } }), fallback);
}

export function searchTrains(query: string): Promise<TrainSuggestion[]> {
  const normalized = query.trim();
  if (!normalized) {
    return Promise.resolve([]);
  }
  const fallback = mock.trainSuggestions.filter((train) => {
    const searchable = `${train.train_number} ${train.train_name}`.toUpperCase();
    return searchable.includes(normalized.toUpperCase());
  });
  return withFallback(api.get(`/search/trains`, { params: { q: normalized, limit: 8 } }), fallback);
}

export function getModelInfo(): Promise<ModelInfo> {
  return withFallback(api.get("/model-info"), mock.modelInfo);
}

export function getHealth(): Promise<Health> {
  return withFallback(api.get("/health"), mock.health);
}

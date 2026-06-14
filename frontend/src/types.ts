export type Overview = {
  total_trains: number;
  total_stations: number;
  average_delay: number;
  most_delayed_zone: string;
};

export type TrendPoint = {
  date: string;
  daily_average_delay: number;
  weekly_average_delay: number;
};

export type NetworkNode = {
  id: string;
  name: string;
  zone: string;
  x: number;
  y: number;
  average_delay: number;
};

export type NetworkEdge = {
  source: string;
  target: string;
  trains: number;
};

export type HeatmapPoint = {
  station: string;
  day: string;
  delay: number;
};

export type ZonePerformance = {
  zone: string;
  average_delay: number;
  records: number;
};

export type RouteCongestion = {
  source: string;
  target: string;
  average_delay: number;
  train_count: number;
};

export type TrainTypeAnalysis = {
  train_type: string;
  average_delay: number;
  records: number;
};

export type PredictionResponse = {
  predicted_delay: number;
  confidence_score: number;
  delay_category: string;
  model_source: string;
};

export type StationSuggestion = {
  station_code: string;
  station_name: string;
  railway_zone: string;
  historical_average_delay: number;
};

export type TrainSuggestion = {
  train_number: number;
  train_name: string;
  train_type: string;
  train_average_delay: number;
};

export type StationProfile = {
  station_code: string;
  station_name: string;
  railway_zone: string;
  address: string;
  historical_average_delay: number;
  delay_trends: { date: string; average_delay: number }[];
  top_delayed_trains: { train_number: number; train_name: string; average_delay: number }[];
};

export type TrainProfile = {
  train_number: number;
  train_name: string;
  train_type: string;
  train_average_delay: number;
  average_delay_last_7_days: number;
  average_delay_last_30_days: number;
  route_stations: {
    station_code: string;
    station_name: string;
    railway_zone: string;
    station_sequence: number;
    distance_from_source: number;
    average_delay: number;
  }[];
  top_delayed_stations: {
    station_code: string;
    station_name: string;
    railway_zone: string;
    station_sequence: number;
    distance_from_source: number;
    average_delay: number;
  }[];
};

export type ModelInfo = {
  model_name: string;
  model_version: string;
  trained_at: string | null;
  metrics: { mae: number | null; rmse: number | null; r2: number | null };
  candidate_metrics: Record<string, { mae: number; rmse: number; r2: number }>;
  dataset_size: number;
  feature_importance: { feature: string; importance: number }[];
};

export type Health = {
  api_status: string;
  model_status: string;
  environment: string;
  dataset_size: number;
};

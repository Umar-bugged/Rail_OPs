import type {
  Health,
  HeatmapPoint,
  ModelInfo,
  NetworkEdge,
  NetworkNode,
  Overview,
  RouteCongestion,
  StationProfile,
  StationSuggestion,
  TrainTypeAnalysis,
  TrainProfile,
  TrainSuggestion,
  TrendPoint,
  ZonePerformance
} from "../types";

export const overview: Overview = {
  total_trains: 5,
  total_stations: 7,
  average_delay: 23.4,
  most_delayed_zone: "CR"
};

export const trends: TrendPoint[] = Array.from({ length: 28 }, (_, index) => ({
  date: `2026-04-${String(index + 1).padStart(2, "0")}`,
  daily_average_delay: 16 + ((index * 7) % 19),
  weekly_average_delay: 20 + ((index * 3) % 11)
}));

export const nodes: NetworkNode[] = [
  { id: "NDLS", name: "New Delhi", zone: "NR", x: 39, y: 27, average_delay: 18 },
  { id: "BPL", name: "Bhopal", zone: "WCR", x: 42, y: 51, average_delay: 24 },
  { id: "NGP", name: "Nagpur", zone: "CR", x: 51, y: 58, average_delay: 32 },
  { id: "CSMT", name: "Mumbai CSMT", zone: "CR", x: 31, y: 67, average_delay: 14 },
  { id: "SBC", name: "KSR Bengaluru", zone: "SWR", x: 43, y: 82, average_delay: 11 },
  { id: "MAS", name: "Chennai Central", zone: "SR", x: 57, y: 82, average_delay: 21 },
  { id: "HWH", name: "Howrah", zone: "ER", x: 72, y: 52, average_delay: 28 }
];

export const edges: NetworkEdge[] = [
  { source: "NDLS", target: "BPL", trains: 28 },
  { source: "BPL", target: "NGP", trains: 22 },
  { source: "NGP", target: "MAS", trains: 18 },
  { source: "CSMT", target: "NGP", trains: 24 },
  { source: "MAS", target: "SBC", trains: 16 },
  { source: "HWH", target: "NGP", trains: 14 }
];

export const heatmap: HeatmapPoint[] = nodes.flatMap((node, nodeIndex) =>
  ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, dayIndex) => ({
    station: node.id,
    day,
    delay: Math.max(4, Math.round(node.average_delay + ((nodeIndex + dayIndex) % 8) - 3))
  }))
);

export const zonePerformance: ZonePerformance[] = [
  { zone: "CR", average_delay: 31.2, records: 8420 },
  { zone: "ER", average_delay: 27.9, records: 5100 },
  { zone: "WCR", average_delay: 23.8, records: 4380 },
  { zone: "NR", average_delay: 18.2, records: 7650 },
  { zone: "SR", average_delay: 17.4, records: 4820 },
  { zone: "SWR", average_delay: 12.1, records: 3360 }
];

export const routeCongestion: RouteCongestion[] = [
  { source: "BPL", target: "NGP", average_delay: 34.1, train_count: 44 },
  { source: "CSMT", target: "NGP", average_delay: 29.8, train_count: 37 },
  { source: "NGP", target: "MAS", average_delay: 27.2, train_count: 31 },
  { source: "NDLS", target: "BPL", average_delay: 21.4, train_count: 52 }
];

export const trainTypeAnalysis: TrainTypeAnalysis[] = [
  { train_type: "Passenger", average_delay: 38, records: 1450 },
  { train_type: "Express", average_delay: 26, records: 6200 },
  { train_type: "Superfast", average_delay: 21, records: 5400 },
  { train_type: "Rajdhani", average_delay: 12, records: 920 },
  { train_type: "Shatabdi", average_delay: 9, records: 820 },
  { train_type: "Vande Bharat", average_delay: 7, records: 740 }
];

export const stationProfile: StationProfile = {
  station_code: "NGP",
  station_name: "Nagpur",
  railway_zone: "CR",
  address: "Maharashtra",
  historical_average_delay: 32,
  delay_trends: trends.slice(-18).map((point) => ({
    date: point.date,
    average_delay: point.daily_average_delay + 3
  })),
  top_delayed_trains: [
    { train_number: 12627, train_name: "Karnataka Express", average_delay: 38 },
    { train_number: 11013, train_name: "Coimbatore Express", average_delay: 31 },
    { train_number: 22435, train_name: "Vande Bharat Express", average_delay: 16 }
  ]
};

export const stationSuggestions: StationSuggestion[] = [
  { station_code: "NGP", station_name: "Nagpur", railway_zone: "CR", historical_average_delay: 32 },
  { station_code: "NDLS", station_name: "New Delhi", railway_zone: "NR", historical_average_delay: 18 },
  { station_code: "BPL", station_name: "Bhopal", railway_zone: "WCR", historical_average_delay: 24 },
  { station_code: "MAS", station_name: "Chennai Central", railway_zone: "SR", historical_average_delay: 21 }
];

export const trainSuggestions: TrainSuggestion[] = [
  { train_number: 12627, train_name: "Karnataka Express", train_type: "Express", train_average_delay: 24 },
  { train_number: 12951, train_name: "Mumbai Rajdhani", train_type: "Rajdhani", train_average_delay: 12 },
  { train_number: 22435, train_name: "Vande Bharat Express", train_type: "Vande Bharat", train_average_delay: 7 }
];

export const trainProfile: TrainProfile = {
  train_number: 12627,
  train_name: "Karnataka Express",
  train_type: "Express",
  train_average_delay: 24,
  average_delay_last_7_days: 22,
  average_delay_last_30_days: 25,
  route_stations: [
    { station_code: "SBC", station_name: "KSR Bengaluru", railway_zone: "SWR", station_sequence: 1, distance_from_source: 0, average_delay: 11 },
    { station_code: "MAS", station_name: "Chennai Central", railway_zone: "SR", station_sequence: 2, distance_from_source: 345, average_delay: 21 },
    { station_code: "NGP", station_name: "Nagpur", railway_zone: "CR", station_sequence: 3, distance_from_source: 690, average_delay: 32 },
    { station_code: "BPL", station_name: "Bhopal", railway_zone: "WCR", station_sequence: 4, distance_from_source: 1035, average_delay: 24 },
    { station_code: "NDLS", station_name: "New Delhi", railway_zone: "NR", station_sequence: 5, distance_from_source: 1380, average_delay: 18 }
  ],
  top_delayed_stations: [
    { station_code: "NGP", station_name: "Nagpur", railway_zone: "CR", station_sequence: 3, distance_from_source: 690, average_delay: 32 },
    { station_code: "BPL", station_name: "Bhopal", railway_zone: "WCR", station_sequence: 4, distance_from_source: 1035, average_delay: 24 },
    { station_code: "MAS", station_name: "Chennai Central", railway_zone: "SR", station_sequence: 2, distance_from_source: 345, average_delay: 21 }
  ]
};

export const modelInfo: ModelInfo = {
  model_name: "Baseline Operations Predictor",
  model_version: "baseline",
  trained_at: null,
  metrics: { mae: null, rmse: null, r2: null },
  candidate_metrics: {},
  dataset_size: 200000,
  feature_importance: [
    { feature: "current_delay", importance: 0.42 },
    { feature: "station_average_delay", importance: 0.24 },
    { feature: "train_average_delay", importance: 0.18 },
    { feature: "distance_from_source", importance: 0.08 },
    { feature: "hour_of_day", importance: 0.08 }
  ]
};

export const health: Health = {
  api_status: "offline demo",
  model_status: "baseline",
  environment: "local",
  dataset_size: 200000
};

import { Radio, SendHorizontal } from "lucide-react";
import { FormEvent, useCallback, useState } from "react";

import { AutocompleteInput, AutocompleteOption } from "../components/AutocompleteInput";
import { PageHeader } from "../components/PageHeader";
import { predictDelay, searchStations, searchTrains } from "../services/api";
import { useDebouncedSuggestions } from "../hooks/useDebouncedSuggestions";
import type { PredictionResponse, StationSuggestion, TrainSuggestion } from "../types";

export function DelayPrediction() {
  const [trainNumber, setTrainNumber] = useState("12627");
  const [stationCode, setStationCode] = useState("NGP");
  const [currentDelay, setCurrentDelay] = useState("15");
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [selectedTrain, setSelectedTrain] = useState<TrainSuggestion | null>(null);
  const [selectedStation, setSelectedStation] = useState<StationSuggestion | null>(null);

  const loadTrainSuggestions = useCallback((query: string) => searchTrains(query), []);
  const loadStationSuggestions = useCallback((query: string) => searchStations(query), []);
  const trains = useDebouncedSuggestions(trainNumber, loadTrainSuggestions, 2);
  const stations = useDebouncedSuggestions(stationCode, loadStationSuggestions, 2);

  const trainOptions: AutocompleteOption[] = trains.suggestions.map((train) => ({
    id: String(train.train_number),
    value: String(train.train_number),
    title: `${train.train_number} - ${train.train_name}`,
    meta: train.train_type,
    detail: `${train.train_average_delay} min avg delay`
  }));

  const stationOptions: AutocompleteOption[] = stations.suggestions.map((station) => ({
    id: station.station_code,
    value: station.station_code,
    title: `${station.station_code} - ${station.station_name}`,
    meta: station.railway_zone,
    detail: `${station.historical_average_delay} min avg delay`
  }));

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setIsPredicting(true);
    const response = await predictDelay({
      train_number: Number(trainNumber),
      station_code: stationCode.trim().toUpperCase(),
      current_delay: Number(currentDelay)
    });
    setResult(response);
    setIsPredicting(false);
  }

  return (
    <section className="page">
      <PageHeader eyebrow="Prediction Terminal" title="Delay Prediction" />
      <div className="terminal-grid">
        <form className="ops-panel terminal-form" onSubmit={handleSubmit}>
          <div className="section-heading">
            <h2>Input Register</h2>
            <span>Type to search train or station</span>
          </div>
          <AutocompleteInput
            label="Train Number"
            value={trainNumber}
            onChange={(value) => {
              setTrainNumber(value);
              setSelectedTrain(null);
            }}
            options={trainOptions}
            onSelect={(option) => {
              setTrainNumber(option.value);
              const match = trains.suggestions.find((train) => String(train.train_number) === option.value);
              setSelectedTrain(match ?? null);
            }}
            placeholder="Start typing train number"
            inputMode="numeric"
            isLoading={trains.isLoading}
            emptyText="No train matches"
          />
          <AutocompleteInput
            label="Station"
            value={stationCode}
            onChange={(value) => {
              setStationCode(value.toUpperCase());
              setSelectedStation(null);
            }}
            options={stationOptions}
            onSelect={(option) => {
              setStationCode(option.value);
              const match = stations.suggestions.find((station) => station.station_code === option.value);
              setSelectedStation(match ?? null);
            }}
            placeholder="Start typing station code or name"
            isLoading={stations.isLoading}
            emptyText="No station matches"
          />
          <label>
            Current Delay
            <input value={currentDelay} onChange={(event) => setCurrentDelay(event.target.value)} inputMode="decimal" />
          </label>
          {(selectedTrain || selectedStation) && (
            <div className="selection-summary">
              {selectedTrain && (
                <span>
                  {selectedTrain.train_name} | {selectedTrain.train_type}
                </span>
              )}
              {selectedStation && (
                <span>
                  {selectedStation.station_name} | {selectedStation.railway_zone}
                </span>
              )}
            </div>
          )}
          <button className="primary-button" type="submit" disabled={isPredicting}>
            <SendHorizontal size={18} />
            {isPredicting ? "Predicting" : "Predict Arrival Delay"}
          </button>
        </form>

        <section className="result-console">
          <div className="console-topline">
            <Radio size={18} />
            <span>Prediction Result Console</span>
          </div>
          <div className="console-readout">
            <span>Predicted Delay</span>
            <strong>{result ? `${result.predicted_delay} min` : "--"}</strong>
          </div>
          <div className="console-grid">
            <div>
              <span>Confidence</span>
              <strong>{result ? `${Math.round(result.confidence_score * 100)}%` : "--"}</strong>
            </div>
            <div>
              <span>Category</span>
              <strong>{result?.delay_category ?? "--"}</strong>
            </div>
            <div>
              <span>Source</span>
              <strong>{result?.model_source ?? "--"}</strong>
            </div>
          </div>
        </section>
      </div>
    </section>
  );
}

import { Search, TrainFront } from "lucide-react";
import { FormEvent, useCallback, useState } from "react";

import { AutocompleteInput, AutocompleteOption } from "../components/AutocompleteInput";
import { OperationsTable } from "../components/OperationsTable";
import { PageHeader } from "../components/PageHeader";
import { TrendChart } from "../components/TrendChart";
import { getStationProfile, getTrainProfile, searchStations, searchTrains } from "../services/api";
import { useApi } from "../hooks/useApi";
import { useDebouncedSuggestions } from "../hooks/useDebouncedSuggestions";
import type { StationSuggestion, TrainSuggestion } from "../types";

export function StationInsights() {
  const [stationCode, setStationCode] = useState("NGP");
  const [submittedCode, setSubmittedCode] = useState("NGP");
  const [trainNumber, setTrainNumber] = useState("12627");
  const [submittedTrain, setSubmittedTrain] = useState("12627");
  const [selectedStation, setSelectedStation] = useState<StationSuggestion | null>(null);
  const [selectedTrain, setSelectedTrain] = useState<TrainSuggestion | null>(null);

  const stationProfile = useApi(() => getStationProfile(submittedCode), [submittedCode]);
  const trainProfile = useApi(() => getTrainProfile(submittedTrain), [submittedTrain]);

  const loadStationSuggestions = useCallback((query: string) => searchStations(query), []);
  const loadTrainSuggestions = useCallback((query: string) => searchTrains(query), []);
  const stationSuggestions = useDebouncedSuggestions(stationCode, loadStationSuggestions, 2);
  const trainSuggestions = useDebouncedSuggestions(trainNumber, loadTrainSuggestions, 2);

  const stationOptions: AutocompleteOption[] = stationSuggestions.suggestions.map((station) => ({
    id: station.station_code,
    value: station.station_code,
    title: `${station.station_code} - ${station.station_name}`,
    meta: station.railway_zone,
    detail: `${station.historical_average_delay} min avg delay`
  }));

  const trainOptions: AutocompleteOption[] = trainSuggestions.suggestions.map((train) => ({
    id: String(train.train_number),
    value: String(train.train_number),
    title: `${train.train_number} - ${train.train_name}`,
    meta: train.train_type,
    detail: `${train.train_average_delay} min avg delay`
  }));

  function handleStationSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmittedCode(stationCode.trim().toUpperCase());
  }

  function handleTrainSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmittedTrain(trainNumber.trim());
  }

  const station = stationProfile.data;
  const train = trainProfile.data;

  return (
    <section className="page">
      <PageHeader eyebrow="Operations Lookup" title="Station & Train Insights" />
      <div className="lookup-grid">
        <form className="lookup-form ops-panel" onSubmit={handleStationSubmit}>
          <div className="section-heading">
            <h2>Station Search</h2>
            <span>Code or station name</span>
          </div>
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
              const match = stationSuggestions.suggestions.find((item) => item.station_code === option.value);
              setSelectedStation(match ?? null);
            }}
            placeholder="Try NGP or Nagpur"
            isLoading={stationSuggestions.isLoading}
          />
          {selectedStation && <span className="lookup-hint">{`${selectedStation.station_name} | ${selectedStation.railway_zone}`}</span>}
          <button className="primary-button" type="submit">
            <Search size={18} />
            Search Station
          </button>
        </form>

        <form className="lookup-form ops-panel" onSubmit={handleTrainSubmit}>
          <div className="section-heading">
            <h2>Train Search</h2>
            <span>Number or train name</span>
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
              const match = trainSuggestions.suggestions.find((item) => String(item.train_number) === option.value);
              setSelectedTrain(match ?? null);
            }}
            placeholder="Try 12627"
            inputMode="numeric"
            isLoading={trainSuggestions.isLoading}
          />
          {selectedTrain && <span className="lookup-hint">{`${selectedTrain.train_name} | ${selectedTrain.train_type}`}</span>}
          <button className="primary-button" type="submit">
            <TrainFront size={18} />
            Search Train
          </button>
        </form>
      </div>

      <div className="two-column">
        <div className="station-profile ops-panel">
          <div className="station-title">
            <div>
              <span>{station?.station_code ?? "--"}</span>
              <h2>{station?.station_name ?? "Station"}</h2>
            </div>
            <strong>{station?.railway_zone ?? "--"}</strong>
          </div>
          <div className="station-details">
            <span>{station?.address ?? "--"}</span>
            <strong>{station ? `${station.historical_average_delay} min avg delay` : "--"}</strong>
          </div>
        </div>

        <div className="station-profile ops-panel">
          <div className="station-title">
            <div>
              <span>{train?.train_number ?? "--"}</span>
              <h2>{train?.train_name ?? "Train"}</h2>
            </div>
            <strong>{train?.train_type ?? "--"}</strong>
          </div>
          <div className="train-kpis">
            <span>{train ? `${train.train_average_delay} min avg delay` : "--"}</span>
            <span>{train ? `${train.average_delay_last_7_days} min last 7` : "--"}</span>
            <span>{train ? `${train.route_stations.length} route stops` : "--"}</span>
          </div>
        </div>
      </div>

      <div className="two-column">
        <section className="ops-panel">
          <div className="section-heading">
            <h2>Delay Trends</h2>
            <span>Recent station averages</span>
          </div>
          <TrendChart
            data={(station?.delay_trends ?? []).map((point) => ({
              date: point.date,
              daily_average_delay: point.average_delay,
              weekly_average_delay: point.average_delay
            }))}
          />
        </section>
        <section className="ops-panel">
          <div className="section-heading">
            <h2>Top Delayed Trains</h2>
            <span>Station-level ranking</span>
          </div>
          <OperationsTable
            columns={["Train", "Name", "Avg Delay"]}
            rows={(station?.top_delayed_trains ?? []).map((item) => [
              item.train_number,
              item.train_name,
              `${item.average_delay} min`
            ])}
          />
        </section>
      </div>

      <div className="two-column">
        <section className="ops-panel">
          <div className="section-heading">
            <h2>Train Route</h2>
            <span>First route stops</span>
          </div>
          <OperationsTable
            columns={["Seq", "Station", "Zone", "Avg Delay"]}
            rows={(train?.route_stations ?? []).slice(0, 14).map((stationRow) => [
              stationRow.station_sequence,
              `${stationRow.station_code} - ${stationRow.station_name}`,
              stationRow.railway_zone,
              `${stationRow.average_delay} min`
            ])}
          />
        </section>
        <section className="ops-panel">
          <div className="section-heading">
            <h2>Delayed Stations</h2>
            <span>Train-level hotspots</span>
          </div>
          <OperationsTable
            columns={["Station", "Distance", "Avg Delay"]}
            rows={(train?.top_delayed_stations ?? []).map((stationRow) => [
              `${stationRow.station_code} - ${stationRow.station_name}`,
              `${Math.round(stationRow.distance_from_source)} km`,
              `${stationRow.average_delay} min`
            ])}
          />
        </section>
      </div>
    </section>
  );
}

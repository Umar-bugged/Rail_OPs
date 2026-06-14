import { Building2, Clock3, MapPinned, Train } from "lucide-react";

import { InfoStrip } from "../components/InfoStrip";
import { PageHeader } from "../components/PageHeader";
import { TrendChart } from "../components/TrendChart";
import { getOverview } from "../services/api";
import { useApi } from "../hooks/useApi";

export function Overview() {
  const overview = useApi(getOverview, []);

  const summary = overview.data?.overview;

  return (
    <section className="page">
      <PageHeader eyebrow="Railway Control Center" title="Live Railway Network Summary" />
      <div className="strip-grid">
        <InfoStrip label="Total Trains" value={summary?.total_trains ?? "..."} icon={Train} />
        <InfoStrip label="Total Stations" value={summary?.total_stations ?? "..."} icon={MapPinned} />
        <InfoStrip label="Average Delay" value={`${summary?.average_delay ?? "..."} min`} icon={Clock3} tone="warning" />
        <InfoStrip label="Most Delayed Zone" value={summary?.most_delayed_zone ?? "..."} icon={Building2} />
      </div>

      <div className="overview-grid">
        <section className="ops-panel">
          <div className="section-heading">
            <h2>Recent Delay Trends</h2>
            <span>Daily and rolling weekly averages</span>
          </div>
          <TrendChart data={overview.data?.trends ?? []} />
        </section>
        <section className="ops-panel operations-brief">
          <div className="section-heading">
            <h2>Operations Brief</h2>
            <span>Current summary</span>
          </div>
          <div className="brief-row">
            <strong>{summary?.most_delayed_zone ?? "--"}</strong>
            <span>zone currently has the highest sampled average delay.</span>
          </div>
          <div className="brief-row">
            <strong>{summary?.average_delay ?? "--"} min</strong>
            <span>network-wide average delay in the loaded analytics sample.</span>
          </div>
          <div className="brief-row">
            <strong>{summary?.total_trains ?? "--"}</strong>
            <span>trains indexed for search and prediction workflows.</span>
          </div>
        </section>
      </div>
    </section>
  );
}

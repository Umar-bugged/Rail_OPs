import type { HeatmapPoint } from "../types";
import { Fragment } from "react";

const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function heatClass(delay: number) {
  if (delay < 12) return "heat-low";
  if (delay < 28) return "heat-mid";
  if (delay < 55) return "heat-high";
  return "heat-severe";
}

export function HeatmapGrid({ data }: { data: HeatmapPoint[] }) {
  const stations = Array.from(new Set(data.map((point) => point.station))).slice(0, 16);
  const lookup = new Map(data.map((point) => [`${point.station}-${point.day}`, point.delay]));

  return (
    <div className="heatmap" style={{ gridTemplateColumns: `112px repeat(${days.length}, minmax(42px, 1fr))` }}>
      <div className="heat-head" />
      {days.map((day) => (
        <div className="heat-head" key={day}>
          {day}
        </div>
      ))}
      {stations.map((station) => (
        <Fragment key={station}>
          <div className="heat-station" key={`${station}-label`}>
            {station}
          </div>
          {days.map((day) => {
            const delay = lookup.get(`${station}-${day}`) ?? 0;
            return (
              <div className={`heat-cell ${heatClass(delay)}`} key={`${station}-${day}`}>
                {Math.round(delay)}
              </div>
            );
          })}
        </Fragment>
      ))}
    </div>
  );
}

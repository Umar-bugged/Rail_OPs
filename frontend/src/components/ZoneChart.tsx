import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { TrainTypeAnalysis, ZonePerformance } from "../types";

type Row = ZonePerformance | TrainTypeAnalysis;

export function ZoneChart({ data, dataKey }: { data: Row[]; dataKey: "zone" | "train_type" }) {
  return (
    <div className="chart-shell compact-chart">
      <ResponsiveContainer width="100%" height={270}>
        <BarChart data={data} margin={{ top: 12, right: 18, left: 0, bottom: 22 }}>
          <CartesianGrid stroke="#d8dee8" vertical={false} />
          <XAxis dataKey={dataKey} tick={{ fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={52} />
          <YAxis tick={{ fontSize: 11 }} width={38} />
          <Tooltip />
          <Bar dataKey="average_delay" name="Avg delay" fill="#1d4f7a" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

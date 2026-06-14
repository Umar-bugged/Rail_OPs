import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { TrendPoint } from "../types";

export function TrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <div className="chart-shell">
      <ResponsiveContainer width="100%" height={270}>
        <LineChart data={data} margin={{ top: 12, right: 18, left: 0, bottom: 6 }}>
          <CartesianGrid stroke="#d8dee8" vertical={false} />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={28} />
          <YAxis tick={{ fontSize: 11 }} width={38} />
          <Tooltip />
          <Line type="monotone" dataKey="daily_average_delay" name="Daily" stroke="#1d4f7a" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="weekly_average_delay" name="Weekly" stroke="#b7791f" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

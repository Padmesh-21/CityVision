import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { INK, SEQUENTIAL_BLUE } from "../../theme";

// A single series over ordinal hours-of-day -- one consistent hue, no
// legend needed (the "Traffic by hour" title already names the series).
export default function HourlyTrafficChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={INK.gridline} />
        <XAxis
          dataKey="hour"
          tickFormatter={(hour) => `${hour}`}
          tick={{ fill: INK.muted, fontSize: 12 }}
          axisLine={{ stroke: INK.baseline }}
          tickLine={false}
          interval={1}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: INK.muted, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={32}
        />
        <Tooltip
          formatter={(value) => [value, "Detections"]}
          labelFormatter={(hour) => `${hour}:00 - ${hour}:59`}
          contentStyle={{ borderRadius: 8, borderColor: INK.gridline, fontSize: 13 }}
        />
        <Bar dataKey="count" fill={SEQUENTIAL_BLUE} radius={[4, 4, 0, 0]} maxBarSize={22} />
      </BarChart>
    </ResponsiveContainer>
  );
}

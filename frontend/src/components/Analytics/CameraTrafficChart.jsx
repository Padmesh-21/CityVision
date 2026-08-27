import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { categoricalColor, INK } from "../../theme";

// Each bar is a distinct camera (categorical identity), so hues are
// assigned in the fixed categorical order rather than one flat color.
export default function CameraTrafficChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={INK.gridline} />
        <XAxis
          dataKey="camera"
          tick={{ fill: INK.muted, fontSize: 12 }}
          axisLine={{ stroke: INK.baseline }}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: INK.muted, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={32}
        />
        <Tooltip
          formatter={(value, _name, item) => [value, item.payload.location]}
          contentStyle={{ borderRadius: 8, borderColor: INK.gridline, fontSize: 13 }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={44}>
          {data.map((entry, index) => (
            <Cell key={entry.camera} fill={categoricalColor(index)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

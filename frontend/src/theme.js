// Validated default palette (light mode) -- see the dataviz skill's
// references/palette.md. Categorical hues are assigned in this fixed
// order and never cycled/reassigned when a filter changes the series
// count.
export const CATEGORICAL = [
  "#2a78d6", // 1 blue
  "#eb6834", // 2 orange
  "#1baf7a", // 3 aqua
  "#eda100", // 4 yellow
  "#e87ba4", // 5 magenta
  "#008300", // 6 green
  "#4a3aa7", // 7 violet
  "#e34948", // 8 red
];

export const SEQUENTIAL_BLUE = "#2a78d6";

export const STATUS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
};

export const INK = {
  primary: "#0b0b0b",
  secondary: "#52514e",
  muted: "#898781",
  gridline: "#e1e0d9",
  baseline: "#c3c2b7",
  surface: "#fcfcfb",
};

export function categoricalColor(index) {
  return CATEGORICAL[index % CATEGORICAL.length];
}

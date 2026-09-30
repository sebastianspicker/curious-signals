const modes = [
  { id: 1, name: "Acceleration", description: "Preview deterministic x, y, z, and magnitude values shaped like the acceleration experiment.", unit: "m/s²", series: ["x", "y", "z", "magnitude"], base: [0.2, -0.1, 9.72, 9.81], amp: [0.7, 0.45, 0.3, 0.25] },
  { id: 2, name: "Gyroscope", description: "Preview deterministic angular velocity values shaped like the gyroscope experiment.", unit: "rad/s", series: ["x", "y", "z", "magnitude"], base: [0.01, -0.02, 0.04, 0.08], amp: [0.12, 0.08, 0.14, 0.09] },
  { id: 3, name: "Magnetic field", description: "Preview deterministic local-field values shaped like the magnetometer experiment.", unit: "µT", series: ["x", "y", "z", "magnitude"], base: [21.4, -8.2, 42.6, 48.4], amp: [4.2, 3.3, 5.1, 2.7] },
  { id: 4, name: "Pressure", description: "Preview a deterministic fixture shaped like the real mode 4 pressure channel.", unit: "hPa", series: ["pressure"], base: [1013.2], amp: [0.8] },
  { id: 5, name: "Temperature & humidity", description: "Explore a deterministic fixture shaped like the real mode 5 data contract.", units: ["°C", "%"], series: ["temperature", "humidity"], base: [22.6, 46.8], amp: [0.55, 2.4] },
  { id: 6, name: "Light & RGB", description: "Preview deterministic ambient, red, green, and blue counts shaped like the light experiment.", unit: "a.u.", series: ["ambient", "red", "green", "blue"], base: [640, 225, 310, 180], amp: [85, 42, 58, 36] },
  { id: 9, name: "Analog input", description: "Preview deterministic A0, A1, and A2 values shaped like the analog input experiment.", unit: "ADC", series: ["A0", "A1", "A2"], base: [386, 612, 228], amp: [74, 46, 62] },
];

const pointCount = 121;

function fixtureValue(mode, seriesIndex, pointIndex) {
  const phase = seriesIndex * 0.87 + mode.id * 0.19;
  const wave = Math.sin(pointIndex * (0.09 + seriesIndex * 0.013) + phase);
  const detail = Math.sin(pointIndex * 0.31 + phase * 1.7) * 0.2;
  const drift = Math.cos(pointIndex * 0.035 + mode.id) * 0.28;
  return mode.base.at(seriesIndex) + mode.amp.at(seriesIndex) * (wave * 0.52 + detail + drift);
}

function modeUnit(mode, index) { return mode.units ? mode.units.at(index) : mode.unit; }
function precisionFor(mode) { return mode.id === 6 || mode.id === 9 ? 0 : mode.id === 4 ? 1 : 2; }

function paddedRange(values) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = Math.max((max - min) * 0.18, 0.1);
  return Object.freeze([min - padding, max + padding]);
}

// Fixtures and their plot ranges are calculated once, independent of playback.
const fixtures = new Map(modes.map((mode) => {
  const series = Object.freeze(mode.series.map((_, seriesIndex) => Object.freeze(
    Array.from({ length: pointCount }, (_, pointIndex) => fixtureValue(mode, seriesIndex, pointIndex))
  )));
  const range = paddedRange(series.flat());
  const ranges = Object.freeze(series.map((values) => mode.id === 5 ? paddedRange(values) : range));
  return [mode.id, Object.freeze({ series, ranges })];
}));

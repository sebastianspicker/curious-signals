// pens mirror each experiment's phyphox colours (yellow → ochre, white → ink on paper).
// wire.scale is what phyphox multiplies the transmitted value by to get the shown unit.
const modes = [
  { id: 1, name: "Acceleration", sensor: "LSM9DS1", experiment: "accelerometer_plot_v1-2.phyphox", description: "Three axes plus magnitude. Lying still and flat, the board reads about 9.8 m/s² on z: the accelerometer feels gravity even at rest.", unit: "m/s²", series: ["x", "y", "z", "magnitude"], pens: ["green", "blue", "ochre", "ink"], wire: { unit: "g", scale: 9.81, note: "phyphox multiplies by 9.81 to show m/s²." }, base: [0.2, -0.1, 9.72, 9.81], amp: [0.7, 0.45, 0.3, 0.25] },
  { id: 2, name: "Gyroscope", sensor: "LSM9DS1", experiment: "gyroscope_plot_v1-2.phyphox", description: "Angular velocity around three axes plus magnitude. Close to zero while the board is still; spin it flat on the table and z responds.", unit: "rad/s", series: ["x", "y", "z", "magnitude"], pens: ["green", "blue", "ochre", "ink"], wire: { unit: "°/s", scale: 3.14159 / 180, note: "phyphox multiplies by π/180 to show rad/s." }, base: [0.01, -0.02, 0.04, 0.08], amp: [0.12, 0.08, 0.14, 0.09] },
  { id: 3, name: "Magnetic field", sensor: "LSM9DS1", experiment: "magnetometer_plot_v1-2.phyphox", description: "The local field on three axes plus magnitude. Earth’s field is roughly 25–65 µT; a magnet or a steel table leg easily outweighs it.", unit: "µT", series: ["x", "y", "z", "magnitude"], pens: ["green", "blue", "ochre", "ink"], wire: { scale: 1, note: "phyphox shows these values unchanged." }, base: [21.4, -8.2, 42.6, 48.4], amp: [4.2, 3.3, 5.1, 2.7] },
  { id: 4, name: "Pressure", sensor: "LPS22HB", experiment: "pressure_plot_v1-2.phyphox", description: "Air pressure, sent in kPa and shown in hPa. Lift the board by one metre and the reading drops by about 0.12 hPa.", unit: "hPa", series: ["pressure"], pens: ["ink"], wire: { unit: "kPa", scale: 10, note: "phyphox multiplies by 10 to show hPa." }, base: [1013.2], amp: [0.8] },
  { id: 5, name: "Temperature & humidity", sensor: "HTS221", experiment: "temperature_plot_v1-2.phyphox", description: "Temperature and relative humidity, each on its own axis. Breathe on the sensor and humidity climbs within seconds.", units: ["°C", "%"], series: ["temperature", "humidity"], pens: ["orange", "blue"], wire: { scale: 1, note: "phyphox shows these values unchanged." }, base: [22.6, 46.8], amp: [0.55, 2.4] },
  { id: 6, name: "Light & RGB", sensor: "APDS9960", experiment: "light_plot_v1-2.phyphox", description: "Ambient (clear) light plus red, green, and blue counts. Relative units: compare colours and light sources, not lux.", unit: "a.u.", series: ["ambient", "red", "green", "blue"], pens: ["ink", "red", "green", "blue"], wire: { scale: 1, note: "Raw sensor counts; phyphox shows them unchanged." }, base: [640, 225, 310, 180], amp: [85, 42, 58, 36] },
  { id: 9, name: "Analog input", sensor: "Pins A0–A2", experiment: "analog_input_plot_v1-2.phyphox", description: "Raw 10-bit readings (0–1023) from pins A0, A1, and A2. Wire a potentiometer or a light-dependent resistor divider.", unit: "ADC", series: ["A0", "A1", "A2"], pens: ["green", "blue", "ochre"], wire: { scale: 1, note: "phyphox multiplies by 3.226 to show millivolts." }, base: [386, 612, 228], amp: [74, 46, 62] },
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
function wireUnit(mode, index) { return mode.wire.unit ?? modeUnit(mode, index); }
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

const SVG_NS = "http://www.w3.org/2000/svg";
const SERIES_COLORS = ["#4e9fff", "#73c72b", "#f2cb45", "#e9f0f1"];

const modes = [
  { id: 1, name: "Acceleration", description: "Preview deterministic x, y, z, and magnitude values shaped like the acceleration experiment.", unit: "m/s²", series: ["x", "y", "z", "magnitude"], base: [0.2, -0.1, 9.72, 9.81], amp: [0.7, 0.45, 0.3, 0.25] },
  { id: 2, name: "Gyroscope", description: "Preview deterministic angular velocity values shaped like the gyroscope experiment.", unit: "rad/s", series: ["x", "y", "z", "magnitude"], base: [0.01, -0.02, 0.04, 0.08], amp: [0.12, 0.08, 0.14, 0.09] },
  { id: 3, name: "Magnetic field", description: "Preview deterministic local-field values shaped like the magnetometer experiment.", unit: "µT", series: ["x", "y", "z", "magnitude"], base: [21.4, -8.2, 42.6, 48.4], amp: [4.2, 3.3, 5.1, 2.7] },
  { id: 4, name: "Pressure", description: "Preview a deterministic fixture shaped like the real mode 4 pressure channel.", unit: "hPa", series: ["pressure"], base: [1013.2], amp: [0.8] },
  { id: 5, name: "Temperature & humidity", description: "Explore a deterministic fixture shaped like the real mode 5 data contract.", units: ["°C", "%"], series: ["temperature", "humidity"], base: [22.6, 46.8], amp: [0.55, 2.4] },
  { id: 6, name: "Light & RGB", description: "Preview deterministic ambient, red, green, and blue counts shaped like the light experiment.", unit: "a.u.", series: ["ambient", "red", "green", "blue"], base: [640, 225, 310, 180], amp: [85, 42, 58, 36] },
  { id: 9, name: "Analog input", description: "Preview deterministic A0, A1, and A2 values shaped like the analog input experiment.", unit: "ADC", series: ["A0", "A1", "A2"], base: [386, 612, 228], amp: [74, 46, 62] },
];

const state = { modeId: 5, visiblePoints: 121, running: false, timer: null };
const pointCount = 121;
const modeList = document.querySelector("#mode-list");
const readouts = document.querySelector("#readouts");
const toggleButton = document.querySelector("#toggle-stream");
const resetButton = document.querySelector("#reset-fixture");

function fixtureValue(mode, seriesIndex, pointIndex) {
  const phase = seriesIndex * 0.87 + mode.id * 0.19;
  const wave = Math.sin(pointIndex * (0.09 + seriesIndex * 0.013) + phase);
  const detail = Math.sin(pointIndex * 0.31 + phase * 1.7) * 0.2;
  const drift = Math.cos(pointIndex * 0.035 + mode.id) * 0.28;
  const base = mode.base.at(seriesIndex) ?? 0;
  const amplitude = mode.amp.at(seriesIndex) ?? 0;
  return base + amplitude * (wave * 0.52 + detail + drift);
}

function modeUnit(mode, index) {
  return mode.units?.at(index) ?? mode.unit;
}

function seriesColor(index) {
  return SERIES_COLORS.at(index) ?? "#e9f0f1";
}

function precisionFor(mode) {
  return mode.id === 6 || mode.id === 9 ? 0 : mode.id === 4 ? 1 : 2;
}

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([attribute, value]) => {
    element.setAttribute(attribute, String(value));
  });
  return element;
}

function renderModes() {
  modeList.replaceChildren();
  modes.forEach((mode) => {
    const button = document.createElement("button");
    button.className = "mode-button";
    button.type = "button";
    button.dataset.mode = String(mode.id);
    button.setAttribute("aria-pressed", String(mode.id === state.modeId));

    const number = document.createElement("span");
    number.className = "mode-number";
    number.textContent = String(mode.id);

    const name = document.createElement("span");
    name.className = "mode-name";
    name.textContent = mode.name;

    button.append(number, name);
    modeList.append(button);
  });
}

function renderReadouts(mode) {
  const pointIndex = Math.max(0, state.visiblePoints - 1);
  readouts.replaceChildren();

  mode.series.forEach((series, seriesIndex) => {
    const readout = document.createElement("div");
    readout.className = "readout";
    readout.style.setProperty("--series-color", seriesColor(seriesIndex));

    const valueRow = document.createElement("div");
    valueRow.className = "readout-value";

    const output = document.createElement("output");
    const value = fixtureValue(mode, seriesIndex, pointIndex).toFixed(precisionFor(mode));
    output.textContent = `${value} ${modeUnit(mode, seriesIndex)}`;

    const label = document.createElement("span");
    label.textContent = series;

    const note = document.createElement("small");
    note.textContent = "Simulated fixture value";

    valueRow.append(output, label);
    readout.append(valueRow, note);
    readouts.append(readout);
  });
}

function chartRange(mode) {
  const values = mode.series.flatMap((unusedSeries, seriesIndex) =>
    Array.from({ length: pointCount }, (unusedPoint, pointIndex) => fixtureValue(mode, seriesIndex, pointIndex))
  );
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = Math.max((max - min) * 0.18, 0.1);
  return [min - padding, max + padding];
}

function chartSeriesRange(mode, seriesIndex) {
  if (mode.id !== 5) return chartRange(mode);
  const values = Array.from({ length: pointCount }, (unusedPoint, pointIndex) => fixtureValue(mode, seriesIndex, pointIndex));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = Math.max((max - min) * 0.18, 0.1);
  return [min - padding, max + padding];
}

function appendAxisLabel(parent, x, y, anchor, value, fill = null) {
  const label = svgElement("text", {
    class: "axis-label",
    x,
    y,
    "text-anchor": anchor,
  });
  if (fill) label.setAttribute("fill", fill);
  label.textContent = value;
  parent.append(label);
}

function renderChart(mode) {
  const width = 920;
  const height = 360;
  const margin = { left: 58, right: mode.id === 5 ? 58 : 24, top: 24, bottom: 45 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const [min, max] = chartSeriesRange(mode, 0);
  const grid = document.querySelector("#chart-grid");
  const lines = document.querySelector("#chart-lines");
  const labels = document.querySelector("#chart-labels");
  grid.replaceChildren();
  lines.replaceChildren();
  labels.replaceChildren();

  for (let index = 0; index <= 6; index += 1) {
    const x = margin.left + (plotWidth * index) / 6;
    grid.append(svgElement("line", {
      class: "grid-line",
      x1: x,
      y1: margin.top,
      x2: x,
      y2: height - margin.bottom,
    }));
    appendAxisLabel(labels, x, height - 18, "middle", `${(index * 4).toFixed(0)}s`);
  }

  for (let index = 0; index <= 4; index += 1) {
    const y = margin.top + (plotHeight * index) / 4;
    const value = max - ((max - min) * index) / 4;
    grid.append(svgElement("line", {
      class: "grid-line",
      x1: margin.left,
      y1: y,
      x2: width - margin.right,
      y2: y,
    }));
    appendAxisLabel(labels, margin.left - 10, y + 4, "end", value.toFixed(precisionFor(mode)));
    if (mode.id === 5) {
      const [rightMin, rightMax] = chartSeriesRange(mode, 1);
      const rightValue = rightMax - ((rightMax - rightMin) * index) / 4;
      appendAxisLabel(labels, width - margin.right + 8, y + 4, "start", rightValue.toFixed(1), seriesColor(1));
    }
  }

  mode.series.forEach((unusedSeries, seriesIndex) => {
    const [seriesMin, seriesMax] = chartSeriesRange(mode, seriesIndex);
    const points = Array.from({ length: state.visiblePoints }, (unusedPoint, pointIndex) => {
      const x = margin.left + (plotWidth * pointIndex) / (pointCount - 1);
      const value = fixtureValue(mode, seriesIndex, pointIndex);
      const y = margin.top + plotHeight - ((value - seriesMin) / (seriesMax - seriesMin)) * plotHeight;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    }).join(" ");
    lines.append(svgElement("polyline", {
      class: "series-line",
      stroke: seriesColor(seriesIndex),
      points,
    }));
  });

  document.querySelector("#chart-label").textContent = mode.name;
  document.querySelector("#chart-progress").textContent = `${((state.visiblePoints - 1) / 5).toFixed(1)} s fixture`;
  document.querySelector("#chart-title").textContent = `Simulated ${mode.name.toLowerCase()} traces`;
  document.querySelector("#chart-description").textContent = `A deterministic line chart that previews the structure of mode ${mode.id} measurements. It is not recorded sensor data.`;

  const legend = document.querySelector("#legend");
  legend.replaceChildren();
  mode.series.forEach((series, seriesIndex) => {
    const item = document.createElement("span");
    item.className = "legend-item";
    item.style.setProperty("--series-color", seriesColor(seriesIndex));

    const swatch = document.createElement("span");
    swatch.className = "legend-swatch";
    item.append(swatch, document.createTextNode(`${series} · ${modeUnit(mode, seriesIndex)}`));
    legend.append(item);
  });
}

function renderWorkspace() {
  const mode = modes.find((item) => item.id === state.modeId) ?? modes.at(0);
  document.querySelector("#experiment-title").textContent = mode.name;
  document.querySelector("#experiment-description").textContent = mode.description;
  renderModes();
  renderReadouts(mode);
  renderChart(mode);
}

function renderStreamButton(action, pathData) {
  const icon = svgElement("svg", { "aria-hidden": "true", viewBox: "0 0 24 24" });
  icon.append(svgElement("path", { d: pathData }));
  toggleButton.replaceChildren(icon, document.createTextNode(action));
}

function stopStream() {
  window.clearInterval(state.timer);
  state.timer = null;
  state.running = false;
  renderStreamButton("Start simulated stream", "m8 5 11 7-11 7V5Z");
}

function startStream() {
  if (state.visiblePoints >= pointCount) state.visiblePoints = 1;
  state.running = true;
  renderStreamButton("Pause simulated stream", "M7 5h4v14H7zM13 5h4v14h-4z");
  state.timer = window.setInterval(() => {
    state.visiblePoints += 1;
    renderWorkspace();
    if (state.visiblePoints >= pointCount) stopStream();
  }, 90);
}

modeList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-mode]");
  if (!button) return;
  stopStream();
  state.modeId = Number(button.dataset.mode);
  state.visiblePoints = pointCount;
  renderWorkspace();
});

toggleButton.addEventListener("click", () => state.running ? stopStream() : startStream());
resetButton.addEventListener("click", () => {
  stopStream();
  state.visiblePoints = pointCount;
  renderWorkspace();
});

renderWorkspace();

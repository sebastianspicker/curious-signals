const SERIES_COLORS = ["#4e9fff", "#73c72b", "#f2cb45", "#e9f0f1"];
const SVG_NAMESPACE = "http://www.w3.org/2000/svg";

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
  return mode.base.at(seriesIndex) + mode.amp.at(seriesIndex) * (wave * 0.52 + detail + drift);
}

function modeUnit(mode, index) { return mode.units ? mode.units.at(index) : mode.unit; }
function precisionFor(mode) { return mode.id === 6 || mode.id === 9 ? 0 : mode.id === 4 ? 1 : 2; }

function createElement(tagName, attributes = {}, content) {
  const element = document.createElement(tagName);
  for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, value);
  if (content !== undefined) element.textContent = content;
  return element;
}

function createSvgElement(tagName, attributes = {}, content) {
  const element = document.createElementNS(SVG_NAMESPACE, tagName);
  for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, value);
  if (content !== undefined) element.textContent = content;
  return element;
}

function setSeriesColor(element, color) {
  element.style.setProperty("--series-color", color);
}

function renderModes() {
  const buttons = modes.map((mode) => {
    const button = createElement("button", {
      class: "mode-button", type: "button", "data-mode": mode.id, "aria-pressed": mode.id === state.modeId,
    });
    button.append(
      createElement("span", { class: "mode-number" }, mode.id),
      createElement("span", { class: "mode-name" }, mode.name),
    );
    return button;
  });
  modeList.replaceChildren(...buttons);
}

function renderReadouts(mode) {
  const index = Math.max(0, state.visiblePoints - 1);
  const items = mode.series.map((series, seriesIndex) => {
    const value = fixtureValue(mode, seriesIndex, index).toFixed(precisionFor(mode));
    const readout = createElement("div", { class: "readout" });
    setSeriesColor(readout, SERIES_COLORS.at(seriesIndex));
    const valueRow = createElement("div", { class: "readout-value" });
    valueRow.append(
      createElement("output", {}, `${value} ${modeUnit(mode, seriesIndex)}`),
      createElement("span", {}, series),
    );
    readout.append(valueRow, createElement("small", {}, "Simulated fixture value"));
    return readout;
  });
  readouts.replaceChildren(...items);
}

function chartRange(mode) {
  const values = mode.series.flatMap((_, seriesIndex) =>
    Array.from({ length: pointCount }, (_, pointIndex) => fixtureValue(mode, seriesIndex, pointIndex))
  );
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = Math.max((max - min) * 0.18, 0.1);
  return [min - padding, max + padding];
}

function chartSeriesRange(mode, seriesIndex) {
  if (mode.id !== 5) return chartRange(mode);
  const values = Array.from({ length: pointCount }, (_, pointIndex) => fixtureValue(mode, seriesIndex, pointIndex));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = Math.max((max - min) * 0.18, 0.1);
  return [min - padding, max + padding];
}

function renderChart(mode) {
  const width = 920;
  const height = 360;
  const margin = { left: 58, right: mode.id === 5 ? 58 : 24, top: 24, bottom: 45 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const [min, max] = chartSeriesRange(mode, 0);

  const grid = [];
  const labels = [];
  for (let i = 0; i <= 6; i += 1) {
    const x = margin.left + (plotWidth * i) / 6;
    grid.push(createSvgElement("line", {
      class: "grid-line", x1: x, y1: margin.top, x2: x, y2: height - margin.bottom,
    }));
    labels.push(createSvgElement("text", {
      class: "axis-label", x: x, y: height - 18, "text-anchor": "middle",
    }, `${(i * 4).toFixed(0)}s`));
  }
  for (let i = 0; i <= 4; i += 1) {
    const y = margin.top + (plotHeight * i) / 4;
    const value = max - ((max - min) * i) / 4;
    grid.push(createSvgElement("line", {
      class: "grid-line", x1: margin.left, y1: y, x2: width - margin.right, y2: y,
    }));
    labels.push(createSvgElement("text", {
      class: "axis-label", x: margin.left - 10, y: y + 4, "text-anchor": "end",
    }, value.toFixed(precisionFor(mode))));
    if (mode.id === 5) {
      const [rightMin, rightMax] = chartSeriesRange(mode, 1);
      const rightValue = rightMax - ((rightMax - rightMin) * i) / 4;
      labels.push(createSvgElement("text", {
        class: "axis-label", fill: SERIES_COLORS.at(1), x: width - margin.right + 8, y: y + 4, "text-anchor": "start",
      }, rightValue.toFixed(1)));
    }
  }

  const lines = mode.series.map((_, seriesIndex) => {
    const [seriesMin, seriesMax] = chartSeriesRange(mode, seriesIndex);
    const points = Array.from({ length: state.visiblePoints }, (__, pointIndex) => {
      const x = margin.left + (plotWidth * pointIndex) / (pointCount - 1);
      const value = fixtureValue(mode, seriesIndex, pointIndex);
      const y = margin.top + plotHeight - ((value - seriesMin) / (seriesMax - seriesMin)) * plotHeight;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    }).join(" ");
    return createSvgElement("polyline", {
      class: "series-line", stroke: SERIES_COLORS.at(seriesIndex), points,
    });
  });

  document.querySelector("#chart-grid").replaceChildren(...grid);
  document.querySelector("#chart-lines").replaceChildren(...lines);
  document.querySelector("#chart-labels").replaceChildren(...labels);
  document.querySelector("#chart-label").textContent = mode.name;
  document.querySelector("#chart-progress").textContent = `${((state.visiblePoints - 1) / 5).toFixed(1)} s fixture`;
  document.querySelector("#chart-title").textContent = `Simulated ${mode.name.toLowerCase()} traces`;
  document.querySelector("#chart-description").textContent = `A deterministic line chart that previews the structure of mode ${mode.id} measurements. It is not recorded sensor data.`;
  const legendItems = mode.series.map((series, seriesIndex) => {
    const item = createElement("span", { class: "legend-item" });
    setSeriesColor(item, SERIES_COLORS.at(seriesIndex));
    item.append(
      createElement("span", { class: "legend-swatch" }),
      document.createTextNode(`${series} · ${modeUnit(mode, seriesIndex)}`),
    );
    return item;
  });
  document.querySelector("#legend").replaceChildren(...legendItems);
}

function renderWorkspace() {
  const mode = modes.find((item) => item.id === state.modeId);
  document.querySelector("#experiment-title").textContent = mode.name;
  document.querySelector("#experiment-description").textContent = mode.description;
  renderModes();
  renderReadouts(mode);
  renderChart(mode);
}

function stopStream() {
  window.clearInterval(state.timer);
  state.timer = null;
  state.running = false;
  renderToggleButton("m8 5 11 7-11 7V5Z", "Start simulated stream");
}

function renderToggleButton(path, label) {
  const icon = createSvgElement("svg", { "aria-hidden": "true", viewBox: "0 0 24 24" });
  icon.append(createSvgElement("path", { d: path }));
  toggleButton.replaceChildren(icon, document.createTextNode(label));
}

function startStream() {
  if (state.visiblePoints >= pointCount) state.visiblePoints = 1;
  state.running = true;
  renderToggleButton("M7 5h4v14H7zM13 5h4v14h-4z", "Pause simulated stream");
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
resetButton.addEventListener("click", () => { stopStream(); state.visiblePoints = pointCount; renderWorkspace(); });

renderWorkspace();

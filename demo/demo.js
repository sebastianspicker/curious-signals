const SVG_NAMESPACE = "http://www.w3.org/2000/svg";
const EXPERIMENT_BASE_URL = "https://github.com/sebastianspicker/curious-signals-phyphox/blob/main/experiments/";
const FIXTURE_SECONDS_PER_POINT = 0.2;
const FRAME_FIELDS = 5;

const state = { modeId: 5, visiblePoints: 121, running: false, timer: null };
const modeList = document.querySelector("#mode-list");
const readouts = document.querySelector("#readouts");
const chart = document.querySelector("#chart");
const toggleButton = document.querySelector("#toggle-stream");
const resetButton = document.querySelector("#reset-fixture");

const streamStatus = document.querySelector("#stream-status");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

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

function currentMode() {
  return modes.find((item) => item.id === state.modeId);
}

function penColor(mode, seriesIndex) {
  return `var(--pen-${mode.pens.at(seriesIndex)})`;
}

function setSeriesColor(element, color) {
  element.style.setProperty("--series-color", color);
}

function fixtureSeconds(points) {
  return ((points - 1) * FIXTURE_SECONDS_PER_POINT).toFixed(1);
}

function renderModes() {
  const items = [];
  for (const mode of modes) {
    if (mode.id === 9) {
      // Make the jump from 6 to 9 legible instead of looking like a missing button.
      const gap = createElement("p", { class: "mode-gap" });
      gap.append(createElement("span", { "aria-hidden": "true" }, "7·8"), createElement("span", {}, "Modes 7 and 8 are reserved"));
      items.push(gap);
    }
    const button = createElement("button", {
      class: "mode-button", type: "button", "data-mode": mode.id, "aria-pressed": mode.id === state.modeId,
    });
    button.append(
      createElement("span", { class: "mode-number" }, mode.id),
      createElement("span", { class: "mode-name" }, mode.name),
      createElement("span", { class: "mode-sensor" }, mode.sensor),
    );
    items.push(button);
  }
  modeList.replaceChildren(...items);
}

function renderReadouts(mode) {
  const index = Math.max(0, state.visiblePoints - 1);
  const items = mode.series.map((series, seriesIndex) => {
    const value = fixtures.get(mode.id).series.at(seriesIndex).at(index).toFixed(precisionFor(mode));
    const readout = createElement("div", { class: "readout" });
    setSeriesColor(readout, penColor(mode, seriesIndex));
    const label = createElement("span", { class: "readout-label", id: `readout-label-${seriesIndex}` });
    label.append(createElement("span", { class: "pen-swatch", "aria-hidden": "true" }), document.createTextNode(series));
    const output = createElement("output", { "aria-live": "off", "aria-labelledby": `readout-label-${seriesIndex}` }, value);
    output.append(createElement("span", { class: "unit" }, ` ${modeUnit(mode, seriesIndex)}`));
    readout.append(label, output);
    return readout;
  });
  readouts.replaceChildren(...items);
  readouts.dataset.count = items.length;
  document.querySelector("#readout-time").textContent = `At the pen · t = ${fixtureSeconds(state.visiblePoints)} s`;
}

function chartSeriesRange(mode, seriesIndex) {
  return fixtures.get(mode.id).ranges.at(seriesIndex);
}

function chartSize() {
  // Draw in real pixels so axis text stays legible on a phone instead of shrinking with a fixed viewBox.
  const box = chart.getBoundingClientRect();
  return { width: Math.round(box.width) || 920, height: Math.round(box.height) || 340 };
}

function renderChart(mode) {
  const { width, height } = chartSize();
  const dualAxis = mode.id === 5;
  const margin = { left: 54, right: dualAxis ? 46 : 18, top: 14, bottom: 30 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const [min, max] = chartSeriesRange(mode, 0);
  chart.setAttribute("viewBox", `0 0 ${width} ${height}`);

  // Millimetre paper: five minor divisions per labelled division.
  const grid = [];
  for (let i = 0; i <= 30; i += 1) {
    const x = margin.left + (plotWidth * i) / 30;
    grid.push(createSvgElement("line", {
      class: i % 5 === 0 ? "grid-line grid-line--major" : "grid-line", x1: x, y1: margin.top, x2: x, y2: height - margin.bottom,
    }));
  }
  for (let i = 0; i <= 20; i += 1) {
    const y = margin.top + (plotHeight * i) / 20;
    grid.push(createSvgElement("line", {
      class: i % 5 === 0 ? "grid-line grid-line--major" : "grid-line", x1: margin.left, y1: y, x2: width - margin.right, y2: y,
    }));
  }

  const labels = [];
  for (let i = 0; i <= 6; i += 1) {
    const x = margin.left + (plotWidth * i) / 6;
    labels.push(createSvgElement("text", {
      class: "axis-label", x: x, y: height - 10, "text-anchor": "middle",
    }, `${(i * 4).toFixed(0)}s`));
  }
  for (let i = 0; i <= 4; i += 1) {
    const y = margin.top + (plotHeight * i) / 4;
    const value = max - ((max - min) * i) / 4;
    labels.push(createSvgElement("text", {
      class: "axis-label", x: margin.left - 8, y: y + 4, "text-anchor": "end",
    }, value.toFixed(precisionFor(mode))));
    if (dualAxis) {
      const [rightMin, rightMax] = chartSeriesRange(mode, 1);
      const rightValue = rightMax - ((rightMax - rightMin) * i) / 4;
      labels.push(createSvgElement("text", {
        class: "axis-label", style: `fill: ${penColor(mode, 1)}`, x: width - margin.right + 8, y: y + 4, "text-anchor": "start",
      }, rightValue.toFixed(1)));
    }
  }

  const heads = [];
  const lines = mode.series.map((_, seriesIndex) => {
    const [seriesMin, seriesMax] = chartSeriesRange(mode, seriesIndex);
    const coordinates = Array.from({ length: state.visiblePoints }, (__, pointIndex) => {
      const x = margin.left + (plotWidth * pointIndex) / (pointCount - 1);
      const value = fixtures.get(mode.id).series.at(seriesIndex).at(pointIndex);
      const y = margin.top + plotHeight - ((value - seriesMin) / (seriesMax - seriesMin)) * plotHeight;
      return [x, y];
    });
    const [headX, headY] = coordinates.at(-1);
    heads.push(createSvgElement("circle", {
      class: "pen-head", cx: headX.toFixed(2), cy: headY.toFixed(2), r: 3.5, style: `stroke: ${penColor(mode, seriesIndex)}`,
    }));
    return createSvgElement("polyline", {
      class: "series-line",
      style: `stroke: ${penColor(mode, seriesIndex)}`,
      points: coordinates.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(" "),
    });
  });
  if (state.visiblePoints < pointCount) {
    const x = margin.left + (plotWidth * (state.visiblePoints - 1)) / (pointCount - 1);
    heads.unshift(createSvgElement("line", { class: "playhead", x1: x, y1: margin.top, x2: x, y2: height - margin.bottom }));
  }

  document.querySelector("#chart-grid").replaceChildren(...grid);
  document.querySelector("#chart-lines").replaceChildren(...lines);
  document.querySelector("#chart-pens").replaceChildren(...heads);
  document.querySelector("#chart-labels").replaceChildren(...labels);
  document.querySelector("#chart-label").textContent = mode.name;
  document.querySelector("#chart-progress").textContent = `${fixtureSeconds(state.visiblePoints)} s fixture`;
  document.querySelector("#chart-title").textContent = `Simulated ${mode.name.toLowerCase()} traces`;
  document.querySelector("#chart-description").textContent = `A deterministic line chart that previews the structure of mode ${mode.id} measurements. It is not recorded sensor data.`;
  const legendItems = mode.series.map((series, seriesIndex) => {
    const item = createElement("span", { class: "legend-item" });
    setSeriesColor(item, penColor(mode, seriesIndex));
    item.append(
      createElement("span", { class: "pen-swatch", "aria-hidden": "true" }),
      document.createTextNode(`${series} · ${modeUnit(mode, seriesIndex)}`),
    );
    return item;
  });
  document.querySelector("#legend").replaceChildren(...legendItems);
}

function renderFrame(mode) {
  // Encode the current sample exactly as the firmware lays out a notification.
  const index = Math.max(0, state.visiblePoints - 1);
  const frame = new DataView(new ArrayBuffer(FRAME_FIELDS * 4));
  const scale = mode.wire.scale;
  const fields = [{ channel: "CH1", meaning: "device time", unit: "s", value: index * FIXTURE_SECONDS_PER_POINT, precision: 2, color: "var(--ink)" }];
  for (let slot = 0; slot < FRAME_FIELDS - 1; slot += 1) {
    const available = slot < mode.series.length;
    fields.push(available ? {
      channel: `CH${slot + 2}`,
      meaning: mode.series.at(slot),
      unit: wireUnit(mode, slot),
      value: fixtures.get(mode.id).series.at(slot).at(index) / scale,
      precision: precisionFor(mode) + (scale === 1 ? 0 : 1),
      color: penColor(mode, slot),
    } : { channel: `CH${slot + 2}`, meaning: "not available", value: Number.NaN });
  }

  const items = fields.map((field, fieldIndex) => {
    const offset = fieldIndex * 4;
    frame.setFloat32(offset, field.value, true);
    const decoded = frame.getFloat32(offset, true);
    const item = createElement("li", { class: "frame-field" });
    if (Number.isNaN(decoded)) item.setAttribute("data-empty", "");
    else setSeriesColor(item, field.color);
    const meta = createElement("div", { class: "field-meta" });
    meta.append(
      createElement("span", { class: "field-channel" }, field.channel),
      createElement("span", { class: "label" }, `bytes ${offset}–${offset + 3}`),
    );
    const bytes = createElement("code", { class: "frame-bytes" });
    for (let byte = 0; byte < 4; byte += 1) {
      bytes.append(createElement("span", {}, frame.getUint8(offset + byte).toString(16).padStart(2, "0")));
    }
    const value = Number.isNaN(decoded) ? "NaN" : `${decoded.toFixed(field.precision)} ${field.unit}`;
    item.append(meta, bytes, createElement("span", { class: "field-value" }, value), createElement("span", { class: "field-meaning" }, field.meaning));
    return item;
  });
  document.querySelector("#frame-fields").replaceChildren(...items);
  document.querySelector("#frame-summary").textContent = `Sample ${index + 1} of ${pointCount} · little-endian float32`;
  document.querySelector("#frame-note").textContent = mode.wire.note;
}

function renderWorkspace() {
  const mode = currentMode();
  document.querySelector("#experiment-title").textContent = mode.name;
  document.querySelector("#experiment-description").textContent = mode.description;
  document.querySelector("#mode-kicker").textContent = `Mode ${mode.id}`;
  document.querySelector("#mode-sensor").textContent = mode.sensor;
  for (const button of modeList.querySelectorAll("button")) {
    button.setAttribute("aria-pressed", Number(button.dataset.mode) === state.modeId);
  }
  renderReadouts(mode);
  renderChart(mode);
  renderFrame(mode);
  const link = document.querySelector("#experiment-link");
  link.href = EXPERIMENT_BASE_URL + mode.experiment;
  link.textContent = mode.experiment;
  document.querySelector("#experiment-mode").textContent = mode.id;
}

function stopStream(message) {
  window.clearInterval(state.timer);
  state.timer = null;
  state.running = false;
  streamStatus.dataset.state = "idle";
  if (message) streamStatus.textContent = message;
  renderToggleButton("m8 5 11 7-11 7V5Z", "Start simulated stream");
}

function renderToggleButton(path, label) {
  const icon = createSvgElement("svg", { "aria-hidden": "true", viewBox: "0 0 24 24" });
  icon.append(createSvgElement("path", { d: path }));
  toggleButton.replaceChildren(icon, document.createTextNode(label));
}

function startStream() {
  if (state.visiblePoints >= pointCount) state.visiblePoints = 1;
  if (reducedMotion.matches) {
    state.visiblePoints = pointCount;
    renderWorkspace();
    streamStatus.textContent = "Simulated stream complete. Full fixture shown with reduced motion.";
    return;
  }
  state.running = true;
  streamStatus.dataset.state = "running";
  streamStatus.textContent = "Simulated stream started.";
  renderWorkspace();
  renderToggleButton("M7 5h4v14H7zM13 5h4v14h-4z", "Pause simulated stream");
  state.timer = window.setInterval(() => {
    state.visiblePoints += 1;
    renderWorkspace();
    if (state.visiblePoints >= pointCount) stopStream("Simulated stream complete. Full fixture shown.");
  }, 90);
}

modeList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-mode]");
  if (!button) return;
  stopStream();
  state.modeId = Number(button.dataset.mode);
  state.visiblePoints = pointCount;
  renderWorkspace();
  streamStatus.textContent = `${currentMode().name} fixture ready.`;
});

toggleButton.addEventListener("click", () => state.running ? stopStream("Simulated stream paused.") : startStream());
resetButton.addEventListener("click", () => { stopStream("Simulated fixture reset. Full fixture shown."); state.visiblePoints = pointCount; renderWorkspace(); });

reducedMotion.addEventListener("change", () => {
  if (reducedMotion.matches && state.running) {
    stopStream("Simulated stream complete. Full fixture shown with reduced motion.");
    state.visiblePoints = pointCount;
    renderWorkspace();
  }
});

let chartWidth = 0;
new ResizeObserver(([entry]) => {
  const width = Math.round(entry.contentRect.width);
  if (width === chartWidth) return;
  chartWidth = width;
  renderChart(currentMode());
}).observe(chart);

renderModes();
renderWorkspace();

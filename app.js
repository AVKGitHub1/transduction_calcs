"use strict";

const DIPOLES_EA0 = {
  blue: -6.93809e-3,
  uv: 1.70762e-3,
};

const CONSTANTS = {
  epsilon0: 8.8541878128e-12,
  c: 299792458,
  hbar: 1.054571817e-34,
  e: 1.602176634e-19,
  a0: 5.29177210903e-11,
};

const FIELD_GROUPS = {
  "cavity-fields": [
    ["gopt", "gopt (kHz)", 25.0, 0.001, 1e6, 1.0],
    ["gmm", "gmm (kHz)", 91.0, 0.001, 1e6, 1.0],
    ["kappaOpt", "kappaOpt (MHz)", 10.0, 1e-6, 1e4, 0.1],
    ["kappaMM", "kappaMM (MHz)", 10.0, 1e-6, 1e4, 0.1],
    ["Delta_e", "Delta_e (MHz)", 0.0, -1e4, 1e4, 0.1],
    ["Delta_r", "Delta_r (MHz)", 0.0, -1e4, 1e4, 0.1],
    ["DeltaMM", "DeltaMM (MHz)", 0.0, -1e4, 1e4, 0.1],
  ],
  "atom-fields": [
    ["Natoms", "Natoms", 5e5, 1.0, 1e10, 1e4],
    ["gammaOpt", "gammaOpt (MHz)", 6.0, 1e-6, 1e4, 0.1],
    ["gammaMM", "gammaMM (kHz)", 100.0, 0.001, 1e7, 1.0],
  ],
  "beam-fields": [
    ["PowerUV", "PowerUV (mW)", 250.0, 0.001, 1e6, 10.0],
    ["PowerBlue", "PowerBlue (mW)", 300.0, 0.001, 1e6, 10.0],
    ["WaistUV", "WaistUV (um)", 1200.0, 0.001, 1e6, 10.0],
    ["WaistBlue", "WaistBlue (um)", 1000.0, 0.001, 1e6, 10.0],
    ["DeltaUV", "DeltaUV (MHz)", 2.0, 1e-6, 1e4, 0.1],
    ["FBlue", "FBlue", 200.0, 1e-6, 1e6, 1.0],
  ],
};

const FIELD_LABELS = Object.fromEntries(
  Object.values(FIELD_GROUPS)
    .flat()
    .map(([name, label]) => [name, label]),
);

const EFFICIENCY_LABELS = {
  OtoM: "Efficiency Function Optical to Microwave",
  MtoO: "Efficiency Function Microwave to Optical",
  func_2: "Efficiency Function from Kumar2023",
};

const state = {
  fields: {},
  lastPlotData: null,
};

function byId(id) {
  return document.getElementById(id);
}

function power(base, exponent) {
  return Math.pow(base, exponent);
}

function linspace(start, end, count) {
  const values = new Array(count);
  const step = (end - start) / (count - 1);
  for (let i = 0; i < count; i += 1) {
    values[i] = start + step * i;
  }
  return values;
}

function peakFieldAmplitude(powerW, waistM) {
  const intensity = (2 * powerW) / (Math.PI * power(waistM, 2));
  const field = Math.sqrt((2 * intensity) / (CONSTANTS.epsilon0 * CONSTANTS.c));
  return { intensity, field };
}

function rabiFrequencyFromDipole(dipoleEa0, powerW, waistM) {
  const { intensity, field } = peakFieldAmplitude(powerW, waistM);
  const dipoleSI = Math.abs(dipoleEa0) * CONSTANTS.e * CONSTANTS.a0;
  const omegaRadS = (dipoleSI * field) / CONSTANTS.hbar;
  const omegaHz = omegaRadS / (2 * Math.PI);
  return {
    I0_W_m2: intensity,
    E0_V_m: field,
    dipole_ea0: dipoleEa0,
    Omega_rad_s: omegaRadS,
    Omega_Hz: omegaHz,
    Omega_MHz: omegaHz / 1e6,
  };
}

function getValues() {
  const values = {};
  for (const [name, input] of Object.entries(state.fields)) {
    values[name] = Number(input.value);
  }
  return values;
}

function calculateParams() {
  const values = getValues();
  const powerUvW = values.PowerUV * 1e-3;
  const powerBlueW = values.PowerBlue * 1e-3;
  const waistUvM = values.WaistUV * 1e-6;
  const waistBlueM = values.WaistBlue * 1e-6;
  const omegaBlue = rabiFrequencyFromDipole(
    DIPOLES_EA0.blue,
    powerBlueW,
    waistBlueM,
  ).Omega_MHz;
  const omegaUv = rabiFrequencyFromDipole(DIPOLES_EA0.uv, powerUvW, waistUvM)
    .Omega_MHz;
  const thetaUv = Math.atan(Math.abs(omegaUv / values.DeltaUV));
  const nMm = values.Natoms * power(Math.sin(thetaUv), 2);
  const nOpt = values.Natoms * power(Math.cos(thetaUv), 2);

  return {
    Gopt: values.gopt * 1e-3 * Math.sqrt(nOpt),
    Gmm: values.gmm * 1e-3 * Math.sqrt(nMm),
    kappaOpt: values.kappaOpt,
    GammaOpt: values.gammaOpt,
    Delta_e: values.Delta_e,
    Delta_r: values.Delta_r,
    gammaMM: values.gammaMM * 1e-3,
    kappaMM: values.kappaMM,
    DeltaMM: values.DeltaMM,
    OmegaB: Math.sqrt(values.FBlue / Math.PI) * omegaBlue,
    Ein: 1.0,
    epsilon: 1.0,
    omegaBlue,
    omegaUv,
  };
}

function efficiencyOtoM(omega, p) {
  const A = p.GammaOpt * p.kappaOpt + 2 * power(p.epsilon, 2) * (
    power(p.Gopt, 2) + 2 * (p.Delta_e - omega) * omega
  );
  const B = -p.Delta_e * p.kappaOpt + (p.GammaOpt + p.kappaOpt) * omega;
  const C =
    4 * power(p.epsilon, 2) * (p.Delta_r - omega) * B
    + p.gammaMM * A
    + 4 * power(p.epsilon, 2) * p.kappaOpt * power(p.OmegaB, 2);
  const D =
    p.gammaMM * (
      -2 * p.Delta_e * p.epsilon * p.kappaOpt
      + 2 * p.epsilon * (p.GammaOpt + p.kappaOpt) * omega
    )
    - 2 * p.epsilon * (p.Delta_r - omega) * A
    + 8 * power(p.epsilon, 3) * omega * power(p.OmegaB, 2);
  const denomReal =
    4 * power(p.Gmm, 2) * power(p.epsilon, 3)
      * (p.Delta_e * p.kappaOpt - (p.GammaOpt + p.kappaOpt) * omega)
    + 2 * p.epsilon * (p.DeltaMM - omega) * C
    + (-p.gammaMM - p.kappaMM) * D;
  const denomImag =
    2 * power(p.Gmm, 2) * power(p.epsilon, 2) * A
    - (-p.gammaMM - p.kappaMM) * C
    + 2 * p.epsilon * (p.DeltaMM - omega) * D;
  const numerator =
    64 * power(p.Ein, 2) * power(p.Gopt, 2) * power(p.Gmm, 2)
    * power(p.epsilon, 8) * p.kappaOpt * p.kappaMM * power(p.OmegaB, 2);
  return numerator / (power(denomReal, 2) + power(denomImag, 2));
}

function efficiencyMtoO(omega, p) {
  const A = p.gammaMM * (p.gammaMM + p.kappaMM) + 2 * power(p.epsilon, 2) * (
    power(p.Gmm, 2) + 2 * (p.Delta_r - omega) * (-p.DeltaMM + omega)
  );
  const B = p.gammaMM * (p.Delta_r + p.DeltaMM - 2 * omega)
    + p.kappaMM * (p.Delta_r - omega);
  const C =
    p.GammaOpt * B
    + (p.Delta_e - omega) * A
    + 4 * power(p.epsilon, 2) * (p.DeltaMM - omega) * power(p.OmegaB, 2);
  const D =
    p.GammaOpt * A
    + 4 * power(p.epsilon, 2) * (
      B * (-p.Delta_e + omega)
      + (p.gammaMM + p.kappaMM) * power(p.OmegaB, 2)
    );
  const denomReal =
    2 * power(p.Gopt, 2) * power(p.epsilon, 2) * A
    + 4 * power(p.epsilon, 2) * omega * C
    + p.kappaOpt * D;
  const denomImag =
    4 * power(p.Gopt, 2) * power(p.epsilon, 3) * B
    + 2 * p.epsilon * p.kappaOpt * C
    - 2 * p.epsilon * omega * D;
  const numerator =
    64 * power(p.Ein, 2) * power(p.Gopt, 2) * power(p.Gmm, 2)
    * power(p.epsilon, 8) * p.kappaOpt * p.kappaMM * power(p.OmegaB, 2);
  return numerator / (power(denomReal, 2) + power(denomImag, 2));
}

function efficiencyFunc2(omega, p) {
  const A = p.GammaOpt * p.kappaOpt + 2 * power(p.epsilon, 2) * (
    power(p.Gopt, 2) + 2 * (p.Delta_e - omega) * omega
  );
  const B = -p.Delta_e * p.kappaOpt + (p.GammaOpt + p.kappaOpt) * omega;
  const C =
    4 * power(p.epsilon, 2) * (p.Delta_r - omega) * B
    + p.gammaMM * A
    + 4 * power(p.epsilon, 2) * p.kappaOpt * power(p.OmegaB, 2);
  const D =
    p.gammaMM * (
      -2 * p.Delta_e * p.epsilon * p.kappaOpt
      + 2 * p.epsilon * (p.GammaOpt + p.kappaOpt) * omega
    )
    - 2 * p.epsilon * (p.Delta_r - omega) * A
    + 8 * power(p.epsilon, 3) * omega * power(p.OmegaB, 2);
  const denomReal =
    4 * power(p.Gmm, 2) * power(p.epsilon, 3)
      * (p.Delta_e * p.kappaOpt - (p.GammaOpt + p.kappaOpt) * omega)
    + 2 * p.epsilon * (p.DeltaMM - omega) * C
    - p.kappaMM * D;
  const denomImag =
    2 * power(p.Gmm, 2) * power(p.epsilon, 2) * A
    + p.kappaMM * C
    + 2 * p.epsilon * (p.DeltaMM - omega) * D;
  const numerator =
    64 * power(p.Ein, 2) * power(p.Gopt, 2) * power(p.Gmm, 2)
    * power(p.epsilon, 8) * p.kappaOpt * p.kappaMM * power(p.OmegaB, 2);
  return numerator / (power(denomReal, 2) + power(denomImag, 2));
}

function selectedEfficiencyFunction() {
  const key = byId("efficiency-function").value;
  return { OtoM: efficiencyOtoM, MtoO: efficiencyMtoO, func_2: efficiencyFunc2 }[key];
}

function calculateFwhm(omega, eta, peakIndex) {
  const halfMax = eta[peakIndex] / 2;

  function crossingBetween(firstIndex, secondIndex) {
    const x0 = omega[firstIndex];
    const x1 = omega[secondIndex];
    const y0 = eta[firstIndex];
    const y1 = eta[secondIndex];
    if (y1 === y0) return x0;
    return x0 + ((halfMax - y0) * (x1 - x0)) / (y1 - y0);
  }

  let leftIndex = peakIndex;
  while (leftIndex > 0 && eta[leftIndex] >= halfMax) leftIndex -= 1;
  const leftCrossing =
    leftIndex === 0 && eta[leftIndex] >= halfMax
      ? omega[0]
      : crossingBetween(leftIndex, leftIndex + 1);

  let rightIndex = peakIndex;
  const lastIndex = eta.length - 1;
  while (rightIndex < lastIndex && eta[rightIndex] >= halfMax) rightIndex += 1;
  const rightCrossing =
    rightIndex === lastIndex && eta[rightIndex] >= halfMax
      ? omega[omega.length - 1]
      : crossingBetween(rightIndex - 1, rightIndex);

  return rightCrossing - leftCrossing;
}

function calculatePlotData() {
  const params = calculateParams();
  const omega = linspace(-10, 10, 1000);
  const func = selectedEfficiencyFunction();
  const eta = omega.map((value) => func(value, params));
  let peakIndex = 0;
  for (let i = 1; i < eta.length; i += 1) {
    if (Number.isFinite(eta[i]) && eta[i] > eta[peakIndex]) peakIndex = i;
  }
  const maxEff = eta[peakIndex] * 100;
  const fwhm = calculateFwhm(omega, eta, peakIndex);
  return { omega, eta, maxEff, fwhm, params };
}

function formatMetric(value, suffix = "") {
  if (!Number.isFinite(value)) return "-";
  return `${value.toFixed(3)}${suffix}`;
}

function drawPlot(data, showStats = true, targetCanvas = byId("plot")) {
  const canvas = targetCanvas;
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(rect.width * dpr));
  canvas.height = Math.max(1, Math.round(rect.height * dpr));

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const width = rect.width;
  const height = rect.height;
  const pad = { left: 68, right: 22, top: 26, bottom: 54 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  function xScale(x) {
    return pad.left + ((x + 10) / 20) * plotW;
  }

  function yScale(y) {
    return pad.top + (1 - y) * plotH;
  }

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "#d7dde5";
  ctx.lineWidth = 1;
  ctx.font = "12px Inter, system-ui, sans-serif";
  ctx.fillStyle = "#647083";
  ctx.textAlign = "center";
  ctx.textBaseline = "top";

  for (let x = -10; x <= 10; x += 5) {
    const px = xScale(x);
    ctx.beginPath();
    ctx.moveTo(px, pad.top);
    ctx.lineTo(px, pad.top + plotH);
    ctx.stroke();
    ctx.fillText(String(x), px, pad.top + plotH + 9);
  }

  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (let y = 0; y <= 1.0001; y += 0.25) {
    const py = yScale(y);
    ctx.beginPath();
    ctx.moveTo(pad.left, py);
    ctx.lineTo(pad.left + plotW, py);
    ctx.stroke();
    ctx.fillText(y.toFixed(2), pad.left - 10, py);
  }

  ctx.strokeStyle = "#28364a";
  ctx.lineWidth = 1.25;
  ctx.strokeRect(pad.left, pad.top, plotW, plotH);

  ctx.beginPath();
  ctx.moveTo(xScale(data.omega[0]), yScale(0));
  for (let i = 0; i < data.omega.length; i += 1) {
    const y = Math.max(0, Math.min(1, data.eta[i]));
    ctx.lineTo(xScale(data.omega[i]), yScale(y));
  }
  ctx.lineTo(xScale(data.omega[data.omega.length - 1]), yScale(0));
  ctx.closePath();
  ctx.fillStyle = "rgba(31, 119, 180, 0.25)";
  ctx.fill();

  ctx.beginPath();
  data.omega.forEach((x, i) => {
    const y = Math.max(0, Math.min(1, data.eta[i]));
    const px = xScale(x);
    const py = yScale(y);
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.strokeStyle = "#1f77b4";
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.fillStyle = "#18212f";
  ctx.font = "14px Inter, system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "bottom";
  ctx.fillText("Photon Cavity Detuning [MHz]", pad.left + plotW / 2, height - 13);

  ctx.save();
  ctx.translate(18, pad.top + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("Conversion Efficiency", 0, 0);
  ctx.restore();

  if (showStats) {
    const text = [
      `Maximum Efficiency = ${data.maxEff.toFixed(3)}%`,
      `Bandwidth = ${data.fwhm.toFixed(3)} MHz`,
    ];
    const boxX = pad.left + 14;
    const boxY = pad.top + 14;
    const boxW = 224;
    const boxH = 58;
    ctx.fillStyle = "rgba(255,255,255,0.9)";
    ctx.strokeStyle = "#b8c2cf";
    ctx.lineWidth = 1;
    roundRect(ctx, boxX, boxY, boxW, boxH, 6);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#18212f";
    ctx.font = "13px Inter, system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText(text[0], boxX + 12, boxY + 11);
    ctx.fillText(text[1], boxX + 12, boxY + 32);
  }
}

function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}

function setStatus(message, isError = false) {
  const status = byId("status");
  status.textContent = message;
  status.classList.toggle("error", isError);
}

function updatePlot() {
  try {
    const data = calculatePlotData();
    state.lastPlotData = data;
    drawPlot(data, true);
    byId("plot-subtitle").textContent = EFFICIENCY_LABELS[byId("efficiency-function").value];
    byId("max-efficiency").textContent = formatMetric(data.maxEff, "%");
    byId("bandwidth").textContent = formatMetric(data.fwhm, " MHz");
    byId("omega-b").textContent = formatMetric(data.params.OmegaB, " MHz");
    byId("omega-uv").textContent = formatMetric(data.params.omegaUv, " MHz");
    setStatus("");
  } catch (error) {
    setStatus(error.message, true);
  }
}

function buildFields() {
  for (const [containerId, fields] of Object.entries(FIELD_GROUPS)) {
    const container = byId(containerId);
    fields.forEach(([name, label, value, min, max, step]) => {
      const row = document.createElement("div");
      row.className = "field-row";

      const labelEl = document.createElement("label");
      labelEl.htmlFor = name;
      labelEl.textContent = label;

      const input = document.createElement("input");
      input.id = name;
      input.name = name;
      input.type = "number";
      input.min = String(min);
      input.max = String(max);
      input.step = String(step);
      input.value = String(value);
      input.addEventListener("input", updatePlot);

      state.fields[name] = input;
      row.append(labelEl, input);
      container.append(row);
    });
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function csvEscape(value) {
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function exportCsv() {
  const rows = [["name", "label", "value"]];
  for (const [name, input] of Object.entries(state.fields)) {
    rows.push([name, FIELD_LABELS[name], Number(input.value).toPrecision(12)]);
  }
  rows.push(["efficiency_function", "Efficiency Function", byId("efficiency-function").value]);
  const csv = rows.map((row) => row.map(csvEscape).join(",")).join("\n");
  downloadBlob(new Blob([csv], { type: "text/csv;charset=utf-8" }), "transduction_parameters.csv");
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];
    if (char === '"' && inQuotes && next === '"') {
      field += '"';
      i += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      row.push(field);
      field = "";
    } else if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") i += 1;
      row.push(field);
      if (row.some((cell) => cell.length > 0)) rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  row.push(field);
  if (row.some((cell) => cell.length > 0)) rows.push(row);
  return rows;
}

function importCsvFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const rows = parseCsv(String(reader.result));
      const header = rows.shift().map((value) => value.trim());
      const nameIndex = header.indexOf("name") >= 0 ? header.indexOf("name") : header.indexOf("parameter");
      const valueIndex = header.indexOf("value");
      if (nameIndex < 0 || valueIndex < 0) throw new Error("CSV must include name and value columns.");

      let updated = 0;
      rows.forEach((row) => {
        const name = (row[nameIndex] || "").trim();
        const value = (row[valueIndex] || "").trim();
        if (name === "efficiency_function") {
          byId("efficiency-function").value = value;
          updated += 1;
        } else if (state.fields[name] && value !== "") {
          state.fields[name].value = String(Number(value));
          updated += 1;
        }
      });
      updatePlot();
      setStatus(`Imported ${updated} parameters from ${file.name}`);
    } catch (error) {
      setStatus(`Parameter import failed: ${error.message}`, true);
    }
  };
  reader.readAsText(file);
}

function canvasBlob(showStats) {
  const sourceData = state.lastPlotData || calculatePlotData();
  const exportCanvas = document.createElement("canvas");
  exportCanvas.style.width = "1100px";
  exportCanvas.style.height = "700px";
  exportCanvas.style.position = "fixed";
  exportCanvas.style.left = "-1200px";
  exportCanvas.style.top = "0";
  document.body.append(exportCanvas);
  drawPlot(sourceData, showStats, exportCanvas);
  return new Promise((resolve) => {
    exportCanvas.toBlob((blob) => {
      exportCanvas.remove();
      resolve(blob);
    }, "image/png");
  });
}

async function saveGraph(showStats, filename) {
  const blob = await canvasBlob(showStats);
  if (blob) downloadBlob(blob, filename);
}

async function saveAll() {
  exportCsv();
  await saveGraph(true, "transduction_efficiency.png");
  await saveGraph(false, "transduction_efficiency_noLegend.png");
}

function bindEvents() {
  byId("efficiency-function").addEventListener("change", updatePlot);
  byId("export-csv").addEventListener("click", exportCsv);
  byId("import-csv").addEventListener("click", () => byId("csv-file").click());
  byId("csv-file").addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (file) importCsvFile(file);
    event.target.value = "";
  });
  byId("save-graph").addEventListener("click", () => saveGraph(true, "transduction_efficiency_with_textbox.png"));
  byId("save-graph-clean").addEventListener("click", () => saveGraph(false, "transduction_efficiency_without_textbox.png"));
  byId("save-all").addEventListener("click", saveAll);
  window.addEventListener("resize", () => {
    if (state.lastPlotData) drawPlot(state.lastPlotData, true);
  });
}

buildFields();
bindEvents();
updatePlot();

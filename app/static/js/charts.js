const CHART_DEFAULTS = {
  margin: { t: 20, b: 36, l: 44, r: 16 },
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  font: { family: "Inter, ui-sans-serif, sans-serif", size: 11, color: "#a1a1aa" },
  xaxis: {
    gridcolor: "#27272a",
    linecolor: "#3f3f46",
    tickcolor: "#3f3f46",
    showgrid: true,
  },
  yaxis: {
    gridcolor: "#27272a",
    linecolor: "#3f3f46",
    tickcolor: "#3f3f46",
    showgrid: true,
  },
  legend: { bgcolor: "transparent", borderwidth: 0 },
  hovermode: "x unified",
  hoverlabel: { bgcolor: "#18181b", bordercolor: "#3f3f46", font: { color: "#f4f4f5" } },
};

const COLORS = {
  blue: "#3b82f6",
  slate: "#64748b",
  red: "#ef4444",
  amber: "#f59e0b",
  emerald: "#10b981",
  sky: "#0ea5e9",
};

const PLOTLY_CONFIG = { responsive: true, displayModeBar: false };

function renderCurveChart(elementId, records) {
  if (!records || !records.length) return;
  const dates = records.map(r => r.date);
  const s10y2y = records.map(r => r.spread_10y2y);
  const s10y3m = records.map(r => r.spread_10y3m);

  const traces = [
    {
      x: dates, y: s10y2y, name: "10Y–2Y",
      type: "scatter", mode: "lines",
      line: { color: COLORS.blue, width: 1.5 },
    },
    {
      x: dates, y: s10y3m, name: "10Y–3M",
      type: "scatter", mode: "lines",
      line: { color: COLORS.slate, width: 1.5, dash: "dash" },
    },
  ];

  const layout = {
    ...CHART_DEFAULTS,
    yaxis: { ...CHART_DEFAULTS.yaxis, ticksuffix: "%" },
    shapes: [{
      type: "rect", xref: "paper", x0: 0, x1: 1,
      yref: "y", y0: -10, y1: 0,
      fillcolor: "rgba(239,68,68,0.06)", line: { width: 0 },
    }],
    annotations: [{
      xref: "paper", x: 0.01, yref: "y", y: -0.05,
      text: "← Inversion zone", showarrow: false,
      font: { size: 10, color: "#ef4444" }, opacity: 0.6,
    }],
  };

  Plotly.newPlot(elementId, traces, layout, PLOTLY_CONFIG);
}

function renderCreditChart(elementId, records) {
  if (!records || !records.length) return;
  const dates = records.map(r => r.date);
  const spread = records.map(r => r.hy_spread);
  const ma = records.map(r => r.hy_spread_ma252);

  const traces = [
    {
      x: dates, y: spread, name: "HY Spread",
      type: "scatter", mode: "lines",
      line: { color: COLORS.amber, width: 1.5 },
      fill: "tozeroy", fillcolor: "rgba(245,158,11,0.05)",
    },
    {
      x: dates, y: ma, name: "1Y Average",
      type: "scatter", mode: "lines",
      line: { color: COLORS.slate, width: 1, dash: "dot" },
    },
  ];

  const layout = {
    ...CHART_DEFAULTS,
    yaxis: { ...CHART_DEFAULTS.yaxis, ticksuffix: "%" },
  };

  Plotly.newPlot(elementId, traces, layout, PLOTLY_CONFIG);
}

function renderInflationChart(elementId, records) {
  if (!records || !records.length) return;
  const monthly = records.filter(r => r.cpi_yoy !== null);
  const dates = monthly.map(r => r.date);
  const cpi = monthly.map(r => r.cpi_yoy);
  const core = monthly.map(r => r.core_cpi_yoy);
  const fed = monthly.map(r => r.fedfunds);

  const traces = [
    {
      x: dates, y: cpi, name: "CPI YoY",
      type: "bar", marker: { color: COLORS.red, opacity: 0.7 },
    },
    {
      x: dates, y: core, name: "Core CPI YoY",
      type: "scatter", mode: "lines",
      line: { color: COLORS.amber, width: 1.5 },
    },
    {
      x: dates, y: fed, name: "Fed Funds",
      type: "scatter", mode: "lines", yaxis: "y2",
      line: { color: COLORS.sky, width: 1.5, dash: "dot" },
    },
  ];

  const layout = {
    ...CHART_DEFAULTS,
    barmode: "overlay",
    yaxis: { ...CHART_DEFAULTS.yaxis, ticksuffix: "%", title: { text: "YoY %", font: { size: 10 } } },
    yaxis2: {
      overlaying: "y", side: "right",
      ticksuffix: "%",
      gridcolor: "transparent",
      title: { text: "Fed Funds", font: { size: 10 } },
    },
    shapes: [{
      type: "line", xref: "paper", x0: 0, x1: 1,
      yref: "y", y0: 2, y1: 2,
      line: { color: "rgba(16,185,129,0.3)", width: 1, dash: "dot" },
    }],
  };

  Plotly.newPlot(elementId, traces, layout, PLOTLY_CONFIG);
}

// Load all charts on page ready
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("curve-chart")) {
    fetch("/api/curve").then(r => r.json()).then(d => renderCurveChart("curve-chart", d.data));
  }
  if (document.getElementById("credit-chart")) {
    fetch("/api/credit").then(r => r.json()).then(d => renderCreditChart("credit-chart", d.data));
  }
  if (document.getElementById("inflation-chart")) {
    fetch("/api/inflation").then(r => r.json()).then(d => renderInflationChart("inflation-chart", d.data));
  }
  if (document.getElementById("comparison-table")) {
    fetch("/api/comparison").then(r => r.json()).then(d => renderComparisonTable("comparison-table", d.data));
  }
});

function renderComparisonTable(elementId, data) {
  const el = document.getElementById(elementId);
  if (!el || !data || !data.matches || !data.matches.length) {
    if (el) el.innerHTML = '<p class="text-xs text-zinc-500">No comparison data available yet.</p>';
    return;
  }

  const featureLabels = {
    spread_10y2y: "10Y–2Y",
    spread_10y3m: "10Y–3M",
    spread_10y2y_1m_delta: "Curve 1M Δ",
    hy_spread: "HY Spread",
    hy_spread_zscore_1y: "HY Z-Score",
    cpi_yoy: "CPI YoY",
    fedfunds: "Fed Funds",
  };

  const rows = data.matches.map((m, i) => {
    const deltaHtml = Object.entries(m.feature_deltas).map(([k, v]) => {
      const sign = v > 0 ? "+" : "";
      const color = Math.abs(v) < 0.1 ? "text-zinc-400" : v > 0 ? "text-emerald-400" : "text-red-400";
      return `<span class="inline-flex gap-1 items-center"><span class="text-zinc-600">${featureLabels[k] || k}:</span><span class="${color}">${sign}${v.toFixed(2)}</span></span>`;
    }).join(" ");

    return `
      <details class="border-b border-zinc-800 last:border-0">
        <summary class="flex items-center justify-between px-3 py-3 cursor-pointer hover:bg-zinc-800/40 transition-colors list-none">
          <div class="flex items-center gap-3">
            <span class="text-xs font-medium text-zinc-200 w-4 text-center">${i + 1}</span>
            <span class="text-sm font-medium text-zinc-100">${m.date}</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="text-right">
              <div class="text-xs text-zinc-400">Similarity</div>
              <div class="text-sm font-medium text-zinc-100">${(m.similarity_score * 100).toFixed(1)}%</div>
            </div>
            <svg class="w-4 h-4 text-zinc-500 rotate-0 group-open:rotate-90 transition-transform" viewBox="0 0 16 16"><path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>
          </div>
        </summary>
        <div class="px-4 pb-3 pt-1">
          <p class="text-xs text-zinc-500 mb-2">Feature deltas (historical − current):</p>
          <div class="flex flex-wrap gap-x-4 gap-y-1 text-xs">${deltaHtml}</div>
        </div>
      </details>`;
  }).join("");

  el.innerHTML = rows;
}

# HV plot: preserve zoom/pan across auto-refresh (PENDING — apply if verified on nTof)

**Status (2026-06-30):** Implemented and deployed in `nTof_x17_DAQ` (commit `8a36c5a`),
awaiting live verification there. **Apply the same change here once it's confirmed working
on the nTof DAQ.** This note is the reminder + the exact change to make.

## Problem
`flask_app/templates/index.html` → `updateHVPlots()` redraws the HV voltage/current plots
every 5 s (`setInterval(updateHVPlots, 5000)`) using `Plotly.newPlot`. `newPlot` tears the
plot down and rebuilds it, so any zoom/pan the user set is wiped on every refresh.

## Fix
No new plotting library needed — Plotly already gives the nice hover. Two changes:
1. Use `Plotly.react` instead of `Plotly.newPlot` (updates data in place instead of rebuilding).
2. Add `uirevision` to each layout, keyed to the selected `run/subrun`. With a stable
   `uirevision`, Plotly keeps the current zoom/pan/legend state across refreshes, and resets
   the view only when the key changes (i.e. when you switch to a different subrun — which is
   the behavior you want anyway).
3. (bonus) `hovermode: 'x unified'` shows all channels at a hovered timestamp; `responsive: true`.

## Exact edit
In `flask_app/templates/index.html`, inside `updateHVPlots()`, replace the block from
`const time = data.time;` through the two `Plotly.newPlot(...)` calls with:

```js
        const time = data.time;
        const run = document.getElementById("run-select").value;
        const subrun = document.getElementById("hv-subrun-select").value;

        const voltageTraces = Object.entries(data.voltage).map(([key, values]) => ({
            x: time,
            y: values,
            mode: 'lines',
            name: key
        }));

        const currentTraces = Object.entries(data.current).map(([key, values]) => ({
            x: time,
            y: values,
            mode: 'lines',
            name: key
        }));

        // uirevision keyed to run/subrun: Plotly preserves zoom/pan/legend state across
        // auto-refreshes (key unchanged) but resets the view when the subrun changes (new key).
        const uirev = `${run}/${subrun}`;

        const voltageLayout = {
            title: 'Voltage (V) vs Time',
            xaxis: { title: 'Time' },
            yaxis: { title: 'Voltage (V)' },
            legend: { orientation: 'h' },
            hovermode: 'x unified',
            uirevision: uirev,
            template: 'plotly_dark'
        };

        const currentLayout = {
            title: 'Current (µA) vs Time',
            xaxis: { title: 'Time' },
            yaxis: { title: 'Current (µA)' },
            legend: { orientation: 'h' },
            hovermode: 'x unified',
            uirevision: uirev,
            template: 'plotly_dark'
        };

        const plotConfig = { responsive: true, displaylogo: false };

        // Plotly.react updates the existing plot in place (instead of rebuilding like
        // newPlot), so combined with a stable uirevision the current zoom/pan is kept.
        Plotly.react('hv-voltage-plot', voltageTraces, voltageLayout, plotConfig);
        Plotly.react('hv-current-plot', currentTraces, currentLayout, plotConfig);
```

The Cosmic Bench `updateHVPlots`/`fetchHVData` use the same element IDs (`run-select`,
`hv-subrun-select`, `hv-voltage-plot`, `hv-current-plot`), so this is a drop-in replacement.

## Deploy note
`flask run` here caches Jinja templates in memory (no auto-reload), so after editing the
template you must restart the flask process for it to be served.

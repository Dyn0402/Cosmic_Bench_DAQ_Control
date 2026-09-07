#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
On-the-fly QA plots for Cosmic Bench DREAM DAQ data.

Produces per-detector QA plots from combined_hits ROOT files and writes them
to <base_out_dir>/analysis/<run_name>/<subrun_name>/<det_name>/, which is
the directory tree the flask Online QA tab serves.

Usage:
    python online_qa/detector_qa.py \\
        --subrun_dir  /path/to/Run/run_name/subrun_name \\
        --run_config  /path/to/Run/run_name/run_config.json \\
        [--mode all|first|per_file] \\
        [--file_num N]

Modes:
    all      — accumulate all combined_hits files in the subrun (default)
    first    — use only file_num == 0 (fast for long runs)
    per_file — use only the single file_num given by --file_num

Detectors processed: DREAM strip detectors only (banco, scintillators skipped).
Position plots (hits_vs_axis, amplitude_per_axis, xy_hit_map) are produced only
for detectors whose x_ and y_ FEU groups live on different FEU board IDs,
allowing clean axis separation from the feu column (e.g. mx17 detectors).
"""

import gc
import copy
import re
import sys
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import binned_statistic
from pathlib import Path
import uproot

COMBINED_INNER      = 'combined_hits_root'
DECODED_ROOT_DIR    = 'decoded_root'
AMP_THRESHOLD       = 200    # ADC — threshold line in amplitude plots
HITS_PER_EVENT_ZOOM = 50     # upper x-limit for the zoomed hits/event panel
WF_NS_PER_SAMPLE    = 20.0   # fallback ns/sample if not in run_config

# Memory control: cap on the number of tree entries read from each ROOT file
# (combined_hits "hits" rows / decoded "nt" waveform rows). Bounds peak memory
# regardless of how large an individual file grows over the course of a run.
# MAX_ENTRIES_PER_FILE = 5000
MAX_ENTRIES_PER_FILE = None

_SKIP_DET_TYPES = {'banco', 'scintillator'}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Cosmic Bench on-the-fly detector QA')
    parser.add_argument('--subrun_dir', required=True, help='Path to the subrun directory')
    parser.add_argument('--run_config', required=True, help='Path to run_config.json')
    parser.add_argument('--mode', default='all', choices=['all', 'first', 'per_file'])
    parser.add_argument('--file_num', type=int, default=None,
                        help='File number to process (per_file mode only)')
    args = parser.parse_args()
    run_qa(Path(args.subrun_dir), Path(args.run_config), args.mode, args.file_num)


# ---------------------------------------------------------------------------
# Core QA runner
# ---------------------------------------------------------------------------

def run_qa(subrun_dir: Path, run_config_path: Path, mode: str = 'all', file_num: int = None):
    with open(run_config_path) as f:
        run_cfg = json.load(f)

    run_name    = run_cfg['run_name']
    subrun_name = subrun_dir.name
    base_out    = Path(run_cfg['base_out_dir'])

    # Sample period from dream_daq_info if available (ns)
    ns_per_sample = (run_cfg.get('dream_daq_info') or {}).get('sample_period', WF_NS_PER_SAMPLE)

    combined_dir = subrun_dir / COMBINED_INNER
    if not combined_dir.exists():
        print(f'[qa] No {COMBINED_INNER} in {subrun_dir}, skipping')
        return

    included = set(run_cfg.get('included_detectors') or [])

    for det_cfg in run_cfg.get('detectors', []):
        name     = det_cfg['name']
        det_type = det_cfg.get('det_type', '')

        if included and name not in included:
            continue
        if det_type in _SKIP_DET_TYPES:
            continue

        dream_feus = det_cfg.get('dream_feus')
        if not isinstance(dream_feus, dict):
            continue

        # FEU board IDs = first element of each (board_id, connector) tuple
        feu_ids = {v[0] for v in dream_feus.values() if isinstance(v, (list, tuple))}
        if not feu_ids:
            continue

        # Separate x/y FEU boards for position-aware plots
        x_feu_ids = {v[0] for k, v in dream_feus.items()
                     if k.startswith('x_') and isinstance(v, (list, tuple))}
        y_feu_ids = {v[0] for k, v in dream_feus.items()
                     if k.startswith('y_') and isinstance(v, (list, tuple))}
        # Position plots only when x and y are on distinct FEU boards
        has_mapping = bool(x_feu_ids) and bool(y_feu_ids) and x_feu_ids.isdisjoint(y_feu_ids)

        df = _load_hits(combined_dir, feu_ids, mode, file_num)
        if df is None or df.empty:
            print(f'[qa] {name} — no hits found, skipping')
            continue

        n_events = df['eventId'].nunique() if 'eventId' in df.columns else '?'
        print(f'[qa] {name} — {len(df):,} hits  ({n_events:,} events)')

        out_dir = base_out / 'analysis' / run_name / subrun_name / name
        out_dir.mkdir(parents=True, exist_ok=True)

        title = f'{run_name} / {subrun_name} / {name}'

        # --- General plots (all strip detectors) ---
        _plot_hits_vs_channel(df, title, out_dir)
        _plot_amplitude_distribution(df, title, out_dir)
        _plot_hits_per_event(df, title, out_dir)
        _plot_hit_time_dist(df, title, out_dir)
        _plot_time_vs_channel(df, title, out_dir)
        _plot_event_rate(df, title, out_dir)
        _plot_amplitude_vs_time(df, title, out_dir)
        _plot_hits_above_threshold_vs_time(df, title, out_dir)

        # --- Position plots for detectors with separate x/y FEU boards ---
        if has_mapping:
            _plot_hits_vs_axis(df, x_feu_ids, y_feu_ids, title, out_dir)
            _plot_amplitude_per_axis(df, x_feu_ids, y_feu_ids, title, out_dir)
            _plot_xy_hit_map(df, x_feu_ids, y_feu_ids, title, out_dir)

        # --- Per-strip waveform mean/RMS from decoded ROOT files ---
        _plot_wf_stats(subrun_dir, feu_ids, ns_per_sample, title, out_dir, mode, file_num)

        plt.close('all')
        gc.collect()
        print(f'[qa] {name} — saved to {out_dir}')


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _extract_file_num(filename: str):
    m = re.match(r'.*_(\d{3})_feu-combined', filename)
    if m:
        return int(m.group(1))
    m = re.match(r'.*_(\d{3})_(\d{2})[._]', filename)
    if m:
        return int(m.group(1))
    return None


def _filter_by_mode(files, mode: str, file_num: int = None):
    """Restrict a sorted file list to the file_num(s) selected by mode (mirrors qa_watcher modes)."""
    if mode == 'first':
        return [f for f in files if _extract_file_num(f.name) == 0]
    if mode == 'per_file' and file_num is not None:
        return [f for f in files if _extract_file_num(f.name) == file_num]
    return files


def _load_hits(combined_dir: Path, feu_ids: set, mode: str,
               file_num: int = None) -> pd.DataFrame:
    all_files = sorted(
        f for f in combined_dir.iterdir()
        if f.suffix == '.root' and '_datrun_' in f.name and 'feu-combined' in f.name
    )
    if not all_files:
        return None

    all_files = _filter_by_mode(all_files, mode, file_num)
    if not all_files:
        return None

    # Read each file individually and cap entries, rather than uproot.concatenate
    # over everything at once — bounds peak memory for files that grow large.
    chunks = []
    for f in all_files:
        try:
            with uproot.open(f) as uf:
                if 'hits' not in uf:
                    continue
                c = uf['hits'].arrays(entry_stop=MAX_ENTRIES_PER_FILE, library='pd')
                # Drop unwanted FEUs per chunk so peak memory never holds rows
                # for boards this detector doesn't use.
                chunks.append(c[c['feu'].isin(feu_ids)])
                del c
        except Exception as e:
            print(f'[qa] Failed to load hits from {f.name}: {e}')

    if not chunks:
        return None

    df = pd.concat(chunks, ignore_index=True)
    del chunks
    gc.collect()
    return df


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _save(fig, out_dir: Path, name: str):
    fig.savefig(out_dir / name, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# General plots — produced for every strip detector
# ---------------------------------------------------------------------------

def _plot_hits_vs_channel(df: pd.DataFrame, title: str, out_dir: Path):
    """Strip occupancy histogram per FEU board."""
    feus = sorted(df['feu'].unique())
    n    = len(feus)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 4), squeeze=False)
    axes = axes[0]
    for ax, feu in zip(axes, feus):
        ch = df.loc[df['feu'] == feu, 'channel'].values
        lo, hi = int(ch.min()), int(ch.max())
        ax.hist(ch, bins=hi - lo + 1, range=(lo - 0.5, hi + 0.5),
                color='steelblue', edgecolor='none')
        ax.set_xlabel('Channel')
        ax.set_ylabel('Hits')
        ax.set_title(f'FEU {feu}')
        ax.grid(True, axis='y', alpha=0.3)
    fig.suptitle(f'Strip occupancy — {title}', fontsize=10)
    fig.tight_layout()
    _save(fig, out_dir, 'hits_vs_channel.png')


def _plot_amplitude_distribution(df: pd.DataFrame, title: str, out_dir: Path):
    """Amplitude histogram (log y) with threshold line."""
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(df['amplitude'].values, bins=200, color='steelblue',
            edgecolor='none', log=True)
    ax.axvline(AMP_THRESHOLD, color='red', lw=1.5, ls='--',
               label=f'Threshold = {AMP_THRESHOLD} ADC')
    ax.set_xlabel('Amplitude [ADC]')
    ax.set_ylabel('Hits')
    ax.set_title(f'Amplitude distribution — {title}')
    ax.legend(fontsize=8)
    ax.grid(True, axis='y', alpha=0.3)
    fig.tight_layout()
    _save(fig, out_dir, 'amplitude_distribution.png')


def _plot_hits_per_event(df: pd.DataFrame, title: str, out_dir: Path):
    """2×2 grid: all hits / above threshold × zoomed (linear) / full range (log y)."""
    if 'eventId' not in df.columns:
        return
    counts_all = df.groupby('eventId').size()
    counts_thr = (df[df['amplitude'] >= AMP_THRESHOLD]
                  .groupby('eventId').size())

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))

    for row_idx, (counts, row_label) in enumerate([
        (counts_all, 'All hits'),
        (counts_thr, f'Amp ≥ {AMP_THRESHOLD} ADC'),
    ]):
        if counts.empty:
            for ax in axes[row_idx]:
                ax.set_visible(False)
            continue

        hi        = int(counts.max())
        bins_zoom = np.arange(0.5, HITS_PER_EVENT_ZOOM + 1.5, 1)

        ax_z = axes[row_idx, 0]
        ax_z.hist(counts.clip(upper=HITS_PER_EVENT_ZOOM), bins=bins_zoom,
                  color='steelblue', edgecolor='none')
        ax_z.set_xlabel('Hits per event')
        ax_z.set_ylabel('Events')
        ax_z.set_title(f'{row_label}  —  0–{HITS_PER_EVENT_ZOOM} (linear)')
        ax_z.grid(True, axis='y', alpha=0.3)

        ax_f = axes[row_idx, 1]
        ax_f.hist(counts, bins=min(hi, 300), color='steelblue',
                  edgecolor='none', log=True)
        ax_f.set_xlabel('Hits per event')
        ax_f.set_ylabel('Events')
        ax_f.set_title(f'{row_label}  —  full range (log y)')
        ax_f.grid(True, axis='y', alpha=0.3)

    fig.suptitle(f'Hits per event — {title}', fontsize=10)
    fig.tight_layout()
    _save(fig, out_dir, 'hits_per_event.png')


def _plot_hit_time_dist(df: pd.DataFrame, title: str, out_dir: Path):
    """Hit time histogram: full range (log y) + zoomed to 1–99th percentile."""
    times = df['time'].values
    p_lo  = np.percentile(times, 1)
    p_hi  = np.percentile(times, 99)
    pad   = max((p_hi - p_lo) * 0.05, 1.0)

    fig, (ax_full, ax_zoom) = plt.subplots(1, 2, figsize=(12, 4))

    ax_full.hist(times, bins=200, color='steelblue', edgecolor='none', log=True)
    ax_full.axvspan(p_lo, p_hi, alpha=0.12, color='green',
                    label=f'1–99th pct [{p_lo:.0f}, {p_hi:.0f}] ns')
    ax_full.set_xlabel('Hit time [ns]')
    ax_full.set_ylabel('Hits')
    ax_full.set_title('Full range (log y)')
    ax_full.legend(fontsize=8)
    ax_full.grid(True, axis='y', alpha=0.3)

    zoom_mask = (times >= p_lo - pad) & (times <= p_hi + pad)
    ax_zoom.hist(times[zoom_mask], bins=200, color='steelblue', edgecolor='none')
    ax_zoom.set_xlabel('Hit time [ns]')
    ax_zoom.set_ylabel('Hits')
    ax_zoom.set_title(f'Zoomed [{p_lo:.0f}, {p_hi:.0f}] ns')
    ax_zoom.grid(True, axis='y', alpha=0.3)

    fig.suptitle(f'Hit time distribution — {title}', fontsize=10)
    fig.tight_layout()
    _save(fig, out_dir, 'hit_time_dist.png')


def _plot_time_vs_channel(df: pd.DataFrame, title: str, out_dir: Path):
    """2D histogram of hit time vs channel per FEU (time auto-zoomed to 1–99th pct)."""
    times = df['time'].values
    t_lo  = np.percentile(times, 1)
    t_hi  = np.percentile(times, 99)

    feus = sorted(df['feu'].unique())
    n    = len(feus)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 5), squeeze=False)
    axes = axes[0]

    cmap = copy.copy(plt.get_cmap('viridis'))
    cmap.set_bad('white')

    for ax, feu in zip(axes, feus):
        df_feu = df[(df['feu'] == feu) & (df['time'] >= t_lo) & (df['time'] <= t_hi)]
        if df_feu.empty:
            ax.set_title(f'FEU {feu}  (no data in time range)')
            continue
        h, xedges, yedges = np.histogram2d(
            df_feu['channel'].values, df_feu['time'].values, bins=(128, 100))
        im = ax.imshow(np.where(h > 0, h, np.nan).T, origin='lower', aspect='auto',
                       extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], cmap=cmap)
        plt.colorbar(im, ax=ax, label='Hits')
        ax.set_xlabel('Channel')
        ax.set_ylabel('Hit time [ns]')
        ax.set_title(f'FEU {feu}')

    fig.suptitle(f'Hit time vs channel — {title}', fontsize=10)
    fig.tight_layout()
    _save(fig, out_dir, 'time_vs_channel.png')


def _plot_event_rate(df: pd.DataFrame, title: str, out_dir: Path):
    """Event count vs time since run start."""
    if 'trigger_timestamp_ns' not in df.columns or 'eventId' not in df.columns:
        return
    ts    = df.groupby('eventId')['trigger_timestamp_ns'].first().values
    t_sec = (ts - ts.min()) / 1e9
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(t_sec, bins=100, color='steelblue', edgecolor='none')
    ax.set_xlabel('Time since run start [s]')
    ax.set_ylabel('Events / bin')
    ax.set_title(f'Event rate — {title}')
    ax.grid(True, axis='y', alpha=0.3)
    fig.tight_layout()
    _save(fig, out_dir, 'event_rate.png')


def _plot_amplitude_vs_time(df: pd.DataFrame, title: str, out_dir: Path, n_bins: int = 50):
    """Mean hit amplitude per time bin (stability monitor)."""
    if 'trigger_timestamp_ns' not in df.columns or 'eventId' not in df.columns:
        return
    ev    = df.groupby('eventId').agg(ts=('trigger_timestamp_ns', 'first'),
                                      amp=('amplitude', 'mean'))
    t_sec = (ev['ts'] - ev['ts'].min()) / 1e9
    mean_amp, edges, _ = binned_statistic(t_sec, ev['amp'], statistic='mean', bins=n_bins)
    std_amp,  _,    _ = binned_statistic(t_sec, ev['amp'], statistic='std',  bins=n_bins)
    count,    _,    _ = binned_statistic(t_sec, ev['amp'], statistic='count', bins=n_bins)
    centres = 0.5 * (edges[:-1] + edges[1:])
    err     = std_amp / np.sqrt(np.maximum(count, 1))
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.errorbar(centres, mean_amp, yerr=err,
                fmt='o-', color='steelblue', capsize=3, ms=4, lw=1.5)
    ax.set_xlabel('Time since run start [s]')
    ax.set_ylabel('Mean amplitude [ADC]')
    ax.set_title(f'Amplitude vs time — {title}')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save(fig, out_dir, 'amplitude_vs_time.png')


def _plot_hits_above_threshold_vs_time(df: pd.DataFrame, title: str, out_dir: Path):
    """Hits above AMP_THRESHOLD per event vs time (scatter)."""
    if 'trigger_timestamp_ns' not in df.columns or 'eventId' not in df.columns:
        return
    ts     = df.groupby('eventId')['trigger_timestamp_ns'].first()
    t_sec  = (ts - ts.min()) / 1e9
    counts = (df[df['amplitude'] >= AMP_THRESHOLD]
              .groupby('eventId').size()
              .reindex(ts.index, fill_value=0))
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.scatter(t_sec.values, counts.values, s=2, alpha=0.3,
               color='steelblue', linewidths=0)
    ax.set_xlabel('Time since run start [s]')
    ax.set_ylabel(f'Hits ≥ {AMP_THRESHOLD} ADC per event')
    ax.set_title(f'Hits above threshold vs time — {title}')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save(fig, out_dir, 'hits_above_threshold_vs_time.png')


# ---------------------------------------------------------------------------
# Position plots — detectors with separate x/y FEU boards (e.g. mx17)
# ---------------------------------------------------------------------------

def _plot_hits_vs_axis(df: pd.DataFrame, x_feu_ids: set, y_feu_ids: set,
                       title: str, out_dir: Path):
    """Strip occupancy split by x-axis FEUs and y-axis FEUs."""
    df_x = df[df['feu'].isin(x_feu_ids)]
    df_y = df[df['feu'].isin(y_feu_ids)]

    fig, (ax_x, ax_y) = plt.subplots(1, 2, figsize=(14, 4))

    for ax, data, axis_label, feu_label in [
        (ax_x, df_x, 'X-strips', '/'.join(str(f) for f in sorted(x_feu_ids))),
        (ax_y, df_y, 'Y-strips', '/'.join(str(f) for f in sorted(y_feu_ids))),
    ]:
        if data.empty:
            ax.set_visible(False)
            continue
        ch = data['channel'].values
        lo, hi = int(ch.min()), int(ch.max())
        ax.hist(ch, bins=hi - lo + 1, range=(lo - 0.5, hi + 0.5),
                color='steelblue', edgecolor='none')
        ax.set_xlabel('Channel')
        ax.set_ylabel('Hits')
        ax.set_title(f'{axis_label} (FEU {feu_label})')
        ax.grid(True, axis='y', alpha=0.3)

    fig.suptitle(f'Strip occupancy by axis — {title}', fontsize=10)
    fig.tight_layout()
    _save(fig, out_dir, 'hits_vs_axis.png')


def _plot_amplitude_per_axis(df: pd.DataFrame, x_feu_ids: set, y_feu_ids: set,
                              title: str, out_dir: Path):
    """Mean amplitude per channel, x and y axes side by side."""
    fig, (ax_x, ax_y) = plt.subplots(1, 2, figsize=(14, 4))

    for ax, feu_ids, axis_label in [
        (ax_x, x_feu_ids, 'X-strips'),
        (ax_y, y_feu_ids, 'Y-strips'),
    ]:
        data = df[df['feu'].isin(feu_ids)]
        if data.empty:
            ax.set_visible(False)
            continue
        mean_amp = data.groupby('channel')['amplitude'].mean().reset_index()
        ax.bar(mean_amp['channel'], mean_amp['amplitude'],
               width=1.0, color='steelblue', edgecolor='none')
        ax.axhline(AMP_THRESHOLD, color='red', lw=1, ls='--',
                   label=f'thr={AMP_THRESHOLD}', zorder=2)
        ax.set_xlabel('Channel')
        ax.set_ylabel('Mean amplitude [ADC]')
        ax.set_title(axis_label)
        ax.legend(fontsize=8)
        ax.grid(True, axis='y', alpha=0.3)

    fig.suptitle(f'Mean amplitude per channel — {title}', fontsize=10)
    fig.tight_layout()
    _save(fig, out_dir, 'amplitude_per_axis.png')


def _plot_xy_hit_map(df: pd.DataFrame, x_feu_ids: set, y_feu_ids: set,
                     title: str, out_dir: Path):
    """
    2D hit map using earliest-arrival x-strip and y-strip per event.
    Gives a crude position reconstruction without a detailed strip map.
    """
    if 'eventId' not in df.columns or 'time' not in df.columns:
        return

    df_x = df[df['feu'].isin(x_feu_ids)]
    df_y = df[df['feu'].isin(y_feu_ids)]
    if df_x.empty or df_y.empty:
        return

    idx_x = df_x.groupby('eventId')['time'].idxmin()
    idx_y = df_y.groupby('eventId')['time'].idxmin()

    x_ch = (df_x.loc[idx_x, ['eventId', 'channel']]
            .set_index('eventId').rename(columns={'channel': 'x_ch'}))
    y_ch = (df_y.loc[idx_y, ['eventId', 'channel']]
            .set_index('eventId').rename(columns={'channel': 'y_ch'}))

    pos = x_ch.join(y_ch, how='inner').dropna()
    if pos.empty:
        return

    fig, ax = plt.subplots(figsize=(7, 6))
    h, xedges, yedges = np.histogram2d(pos['x_ch'].values, pos['y_ch'].values, bins=64)
    cmap = copy.copy(plt.get_cmap('viridis'))
    cmap.set_bad('lightgrey')
    im = ax.imshow(np.where(h > 0, h, np.nan).T, origin='lower', aspect='auto',
                   extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], cmap=cmap)
    plt.colorbar(im, ax=ax, label='Events')
    ax.set_xlabel('X-strip channel (earliest hit)')
    ax.set_ylabel('Y-strip channel (earliest hit)')
    ax.set_title(f'2D hit map ({len(pos):,} events)\n{title}')
    fig.tight_layout()
    _save(fig, out_dir, 'xy_hit_map.png')


# ---------------------------------------------------------------------------
# Waveform mean/RMS from decoded ROOT files
# ---------------------------------------------------------------------------

def _load_wf_stats_from_decoded(decoded_dir: Path, feu_ids, mode: str,
                                file_num: int = None) -> dict:
    """
    Stream decoded ROOT files — restricted to the same file_num(s) _load_hits
    uses for `mode` (e.g. only file_num==0 in 'first' mode, the qa_watcher
    default) and capped at MAX_ENTRIES_PER_FILE waveform rows per file — and
    compute per-(channel, sample) mean & RMS amplitude.
    """
    result    = {}
    all_files = sorted(decoded_dir.iterdir(), key=lambda p: p.name)
    all_files = _filter_by_mode(all_files, mode, file_num)

    for feu in sorted(feu_ids):
        feu_str   = f'_{feu:02d}.'
        feu_files = [f for f in all_files if f.suffix == '.root' and feu_str in f.name]

        # Stream files and accumulate per-(channel, sample) count/sum/sum-of-
        # squares into small dense arrays. Peak memory stays bounded by a single
        # file plus the accumulators, regardless of how many waveforms a run has
        # — avoiding the giant concat + groupby that used to OOM on long runs.
        n_ch = n_smp = 0
        acc_cnt = acc_sum = acc_sq = None
        for fpath in feu_files:
            try:
                with uproot.open(fpath) as uf:
                    if 'nt' not in uf:
                        continue
                    tree         = uf['nt']
                    samples_arr  = tree['sample'].array(entry_stop=MAX_ENTRIES_PER_FILE, library='np')
                    channels_arr = tree['channel'].array(entry_stop=MAX_ENTRIES_PER_FILE, library='np')
                    amps_arr     = tree['amplitude'].array(entry_stop=MAX_ENTRIES_PER_FILE, library='np')
            except Exception as e:
                print(f'[qa/wf] Error reading {fpath.name}: {e}')
                continue
            if len(samples_arr) == 0:
                continue
            flat_s = np.concatenate([np.asarray(x) for x in samples_arr]).astype(np.int64)
            flat_c = np.concatenate([np.asarray(x) for x in channels_arr]).astype(np.int64)
            flat_a = np.concatenate([np.asarray(x) for x in amps_arr]).astype(np.float64)

            # Grow accumulators if this file exposes larger channel/sample ids.
            file_n_ch  = int(flat_c.max()) + 1
            file_n_smp = int(flat_s.max()) + 1
            if file_n_ch > n_ch or file_n_smp > n_smp:
                new_n_ch, new_n_smp = max(n_ch, file_n_ch), max(n_smp, file_n_smp)
                new_cnt = np.zeros((new_n_ch, new_n_smp))
                new_sum = np.zeros((new_n_ch, new_n_smp))
                new_sq  = np.zeros((new_n_ch, new_n_smp))
                if acc_cnt is not None:
                    new_cnt[:n_ch, :n_smp] = acc_cnt
                    new_sum[:n_ch, :n_smp] = acc_sum
                    new_sq[:n_ch, :n_smp]  = acc_sq
                acc_cnt, acc_sum, acc_sq = new_cnt, new_sum, new_sq
                n_ch, n_smp = new_n_ch, new_n_smp

            lin  = flat_c * n_smp + flat_s
            size = n_ch * n_smp
            acc_cnt += np.bincount(lin, minlength=size).reshape(n_ch, n_smp)
            acc_sum += np.bincount(lin, weights=flat_a, minlength=size).reshape(n_ch, n_smp)
            acc_sq  += np.bincount(lin, weights=flat_a * flat_a, minlength=size).reshape(n_ch, n_smp)

            del samples_arr, channels_arr, amps_arr, flat_s, flat_c, flat_a, lin
            gc.collect()

        if acc_cnt is None:
            continue

        ch_idx, smp_idx = np.nonzero(acc_cnt > 0)
        cnt  = acc_cnt[ch_idx, smp_idx]
        mean = acc_sum[ch_idx, smp_idx] / cnt
        var  = acc_sq[ch_idx, smp_idx] / cnt - mean * mean
        rms  = np.sqrt(np.clip(var, 0.0, None))
        result[feu] = pd.DataFrame({'channel': ch_idx.astype(np.int32),
                                    'sample':  smp_idx.astype(np.int32),
                                    'mean':    mean.astype(np.float32),
                                    'rms':     rms.astype(np.float32)})

    return result


def _plot_wf_mean_rms(stats: dict, feu_ids, title: str, out_dir: Path,
                       ns_per_sample: float) -> None:
    """2D color maps of mean and RMS amplitude vs channel and time, per FEU."""
    cmap = copy.copy(plt.get_cmap('viridis'))
    cmap.set_bad('lightgrey')

    for feu in sorted(feu_ids):
        if feu not in stats or stats[feu].empty:
            continue
        df = stats[feu]

        ch_min  = int(df['channel'].min())
        ch_max  = int(df['channel'].max())
        smp_min = int(df['sample'].min())
        smp_max = int(df['sample'].max())
        n_ch    = ch_max - ch_min + 1
        n_smp   = smp_max - smp_min + 1

        mean_img = np.full((n_ch, n_smp), np.nan)
        rms_img  = np.full((n_ch, n_smp), np.nan)
        ci = df['channel'].values.astype(int) - ch_min
        si = df['sample'].values.astype(int)  - smp_min
        mean_img[ci, si] = df['mean'].values
        rms_img[ci, si]  = df['rms'].values

        t0     = smp_min * ns_per_sample / 1000
        t1     = (smp_max + 1) * ns_per_sample / 1000
        extent = [t0, t1, ch_min - 0.5, ch_max + 0.5]

        fig_h = max(4.0, n_ch * 0.08 + 2.0)
        fig, (ax_m, ax_r) = plt.subplots(1, 2, figsize=(14, fig_h))

        im_m = ax_m.imshow(mean_img, origin='lower', aspect='auto', extent=extent, cmap=cmap)
        plt.colorbar(im_m, ax=ax_m, label='Mean amplitude [ADC]')
        ax_m.set_xlabel('Time [μs]')
        ax_m.set_ylabel('Channel')
        ax_m.set_title(f'FEU {feu} — mean')

        im_r = ax_r.imshow(rms_img, origin='lower', aspect='auto', extent=extent, cmap=cmap)
        plt.colorbar(im_r, ax=ax_r, label='RMS amplitude [ADC]')
        ax_r.set_xlabel('Time [μs]')
        ax_r.set_ylabel('Channel')
        ax_r.set_title(f'FEU {feu} — RMS')

        cap_note = 'all waveforms/file' if MAX_ENTRIES_PER_FILE is None else f'≤{MAX_ENTRIES_PER_FILE:,} waveforms/file'
        fig.suptitle(f'{title}\nWaveform mean & RMS ({cap_note})', fontsize=10)
        fig.tight_layout()
        _save(fig, out_dir, f'waveform_mean_rms_feu{feu:02d}.png')


def _plot_wf_mean_rms_per_strip(stats: dict, feu_ids, title: str, out_dir: Path) -> None:
    """Per-strip mean and RMS amplitude integrated over all samples, per FEU."""
    for feu in sorted(feu_ids):
        if feu not in stats or stats[feu].empty:
            continue
        df = stats[feu]

        per_ch = df.groupby('channel').agg(
            mean=('mean', 'mean'),
            rms=('rms',  'mean'),
        ).reset_index().sort_values('channel')

        channels = per_ch['channel'].values
        means    = per_ch['mean'].values
        rms_vals = per_ch['rms'].values
        ch_max   = int(channels.max())
        ch_min   = int(channels.min())
        xticks   = [t for t in [0] + list(range(63, ch_max + 1, 64)) if ch_min <= t <= ch_max]

        fig, (ax_m, ax_r) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

        ax_m.bar(channels, means, width=1.0, color='steelblue', edgecolor='none')
        ax_m.axhline(4096, color='red', lw=1.2, ls='--', label='4096')
        ax_m.set_ylabel('Mean amplitude [ADC]')
        ax_m.set_title(f'FEU {feu} — mean amplitude per strip')
        ax_m.legend(fontsize=8)
        ax_m.grid(True, axis='y', alpha=0.3)

        ax_r.bar(channels, rms_vals, width=1.0, color='steelblue', edgecolor='none')
        ax_r.set_ylabel('RMS amplitude [ADC]')
        ax_r.set_title(f'FEU {feu} — RMS amplitude per strip')
        ax_r.set_xlabel('Channel')
        ax_r.set_xticks(xticks)
        ax_r.grid(True, axis='y', alpha=0.3)

        fig.suptitle(f'{title}\nWaveform mean & RMS per strip', fontsize=10)
        fig.tight_layout()
        _save(fig, out_dir, f'waveform_strip_mean_rms_feu{feu:02d}.png')


def _plot_wf_stats(subrun_dir: Path, feu_ids, ns_per_sample: float,
                   title: str, out_dir: Path, mode: str, file_num: int = None) -> None:
    decoded_dir = subrun_dir / DECODED_ROOT_DIR
    if not decoded_dir.exists() or not feu_ids:
        return
    print(f'[qa/wf] Computing per-strip mean/RMS from decoded files ...')
    wf_stats = _load_wf_stats_from_decoded(decoded_dir, sorted(feu_ids), mode, file_num)
    if wf_stats:
        _plot_wf_mean_rms(wf_stats, sorted(feu_ids), title, out_dir, ns_per_sample)
        _plot_wf_mean_rms_per_strip(wf_stats, sorted(feu_ids), title, out_dir)
        print(f'[qa/wf] Saved waveform mean/RMS plots → {out_dir}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 09 09:56 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/plot_run_event_nums

@author: Dylan Neff, dn277127
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def main():
    run_dir = '/mnt/data/beam_sps_25/Run/'
    csv_name = 'daq_status_log.csv'
    event_col_name = 'dream_events'

    desync_monitor_csv_name = 'daq_status_log.csv'

    if len(sys.argv) != 2:
        print('Usage: python plot_run_event_nums.py <run_number>')
        sys.exit(1)
    run_num = sys.argv[1]
    run_num = 'run_' + run_num
    run_dir = os.path.join(run_dir, run_num)

    sub_run_names = []
    sub_run_events = []
    sub_run_times = []
    sub_run_banco_synced = []
    sub_run_dream_banco_synced = []

    for sub_run in os.listdir(run_dir):
        sub_run_path = os.path.join(run_dir, sub_run)
        if not os.path.isdir(sub_run_path):
            continue
        csv_path = os.path.join(sub_run_path, csv_name)
        if not os.path.exists(csv_path):
            print(f'CSV file not found: {csv_path}')
            continue
        # get file modification time as a POSIX timestamp (float seconds)
        mtime = os.path.getmtime(csv_path)
        df = pd.read_csv(csv_path)
        max_events = df[event_col_name].max()

        sub_run_names.append(sub_run)
        sub_run_events.append(max_events)
        sub_run_times.append(mtime)

        desync_csv_path = os.path.join(sub_run_path, desync_monitor_csv_name)
        banco_synced, dream_banco_synced = get_sync_status(desync_csv_path)
        sub_run_banco_synced.append(banco_synced)
        sub_run_dream_banco_synced.append(dream_banco_synced)

    # Sort by modification time
    sorted_indices = np.argsort(sub_run_times)
    sub_run_names = [sub_run_names[i] for i in sorted_indices]
    sub_run_events = [sub_run_events[i] for i in sorted_indices]
    sub_run_banco_synced = [sub_run_banco_synced[i] for i in sorted_indices]
    sub_run_dream_banco_synced = [sub_run_dream_banco_synced[i] for i in sorted_indices]

    fig, ax = plt.subplots(figsize=(10, 6))

    # --- Base bar plot ---
    bars = ax.bar(sub_run_names, sub_run_events, color='skyblue', edgecolor='black')

    # --- Compute desync positions ---
    x_positions = np.arange(len(sub_run_names))
    y_positions = np.array(sub_run_events) / 2  # center of bars

    # --- Plot symbols for desyncs ---
    # symbol_offset = max(sub_run_events) * 0.02  # small spacing above bars
    symbol_offset = 0

    # Banco not synced (red X)
    for i in np.where(np.logical_not(sub_run_banco_synced))[0]:
        ax.text(x_positions[i], y_positions[i] + symbol_offset, '✗',
                color='red', fontsize=30, ha='center', va='bottom')

    # Dream-Banco not synced (green ●)
    for i in np.where(np.logical_not(sub_run_dream_banco_synced))[0]:
        ax.text(x_positions[i], y_positions[i] + symbol_offset, '●',
                color='green', fontsize=30, ha='center', va='bottom')

    # --- Legend ---
    ax.scatter([], [], color='red', marker='x', label='Banco De-Synced', s=80)
    ax.scatter([], [], color='green', marker='o', label='Dream–Banco De-Synced', s=80)
    ax.legend(frameon=False, loc='upper right')

    # --- Labels & formatting ---
    ax.set_xlabel('Sub-run Name', fontsize=12)
    ax.set_ylabel('Number of Dream Events', fontsize=12)
    ax.set_title('Dream Event Counts per Sub-run', fontsize=14, weight='bold')
    ax.set_xticks(x_positions)
    ax.set_xticklabels(sub_run_names, rotation=45, ha='right')
    ax.margins(y=0.15)
    plt.tight_layout()
    plt.show()

    # fig, ax = plt.subplots(figsize=(10, 6))
    # ax.bar(sub_run_names, sub_run_events, color='skyblue')
    # # Plot sync status as text above bars. Use green circles for dream_banco not synced, red X for banco not synced
    # banco_desync_subruns = [i for i, synced in enumerate(sub_run_banco_synced) if synced is False]
    # dream_banco_desync_subruns = [i for i, synced in enumerate(sub_run_dream_banco_synced) if synced is False]
    # banco_desync_label = False
    # for i in banco_desync_subruns:
    #     if not banco_desync_label:
    #         ax.text(i, sub_run_events[i] + 5, 'X', color='red', fontsize=14, ha='center', va='bottom', label='Banco Not Synced')
    #         banco_desync_label = True
    #     else:
    #         ax.text(i, sub_run_events[i] + 5, 'X', color='red', fontsize=14, ha='center', va='bottom')
    # dream_desync_label = False
    # for i in dream_banco_desync_subruns:
    #     if not dream_desync_label:
    #         ax.text(i, sub_run_events[i] + 5, '●', color='green', fontsize=14, ha='center', va='bottom', label='Dream-Banco Not Synced')
    #         dream_desync_label = True
    #     else:
    #         ax.text(i, sub_run_events[i] + 5, '●', color='green', fontsize=14, ha='center', va='bottom')
    #
    # ax.set_xlabel('Sub-run Name')
    # ax.set_ylabel('Number of Dream Events')
    # ax.set_title('Number of Dream Events per Sub-run')
    # ax.set_xticklabels(sub_run_names, rotation=45, ha='right')
    # plt.tight_layout()
    # plt.show()

    print('donzo')


def get_sync_status(csv_path):
    """
    Reads a DAQ status log CSV and returns two booleans:
      - banco_synced: True if Banco internally synced
      - dream_banco_synced: True if Dream and Banco are mutually synced

    If no row has both RUNNING, returns (None, None)
    """
    df = pd.read_csv(csv_path)

    # Drop rows with missing or malformed values
    df = df.dropna(subset=["dream_status", "banco_status"], how="any")

    # Filter for rows where both systems are RUNNING
    running_rows = df[(df["dream_status"] == "RUNNING") & (df["banco_status"] == "RUNNING")]

    if running_rows.empty:
        return None, None  # No valid RUNNING rows found

    # Get the last such row
    last_row = running_rows.iloc[-1]

    # Extract fields safely
    banco_synced = bool(last_row.get("banco_synced"))
    difference = last_row.get("difference")

    # Convert difference to numeric (if string)
    try:
        difference = float(difference)
    except (ValueError, TypeError):
        difference = None

    dream_banco_synced = (difference == 0)

    return banco_synced, dream_banco_synced


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 09 09:56 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/plot_run_event_nums

@author: Dylan Neff, dn277127
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def main():
    run_dir = '/mnt/data/beam_sps_25/Run/run_19/'
    csv_name = 'daq_status_log.csv'
    event_col_name = 'dream_events'

    sub_run_names = []
    sub_run_events = []
    sub_run_times = []

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

    # Sort by modification time
    sorted_indices = np.argsort(sub_run_times)
    sub_run_names = [sub_run_names[i] for i in sorted_indices]
    sub_run_events = [sub_run_events[i] for i in sorted_indices]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(sub_run_names, sub_run_events, color='skyblue')
    ax.set_xlabel('Sub-run Name')
    ax.set_ylabel('Number of Dream Events')
    ax.set_title('Number of Dream Events per Sub-run')
    ax.set_xticklabels(sub_run_names, rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

    print('donzo')


if __name__ == '__main__':
    main()

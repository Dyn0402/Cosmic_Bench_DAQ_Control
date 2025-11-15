#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 11 21:55 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/cheap_efficiency_plot

@author: Dylan Neff, dn277127
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def main():
    base_dir = '/mnt/data/beam_sps_25/Analysis/'
    run_name = 'run_77'
    detector_names = [
        'urw_inter', 'rd5_plein_saral_2', 'rd5_plein_vfp_1',
        'rd5_grid_saral_1', 'rd5_strip_saral_1', 'rd5_strip_esl_1',
    ]
    sub_runs = {
        'rotation_-60_drift_resist_scan_-95': -95,
        'rotation_-60_drift_resist_scan_-90': -90,
        'rotation_-60_drift_resist_scan_-85': -85,
        'rotation_-60_drift_resist_scan_-80': -80,
        'rotation_-60_drift_resist_scan_-70': -70,
        'rotation_-60_drift_resist_scan_-65': -65,
        'rotation_-60_drift_resist_scan_-60': -60,
        'rotation_-60_drift_resist_scan_-55': -55,
        'rotation_-60_drift_resist_scan_-45': -45,
        'rotation_-60_drift_resist_scan_-40': -40,
        'rotation_-60_drift_resist_scan_-35': -35,
        'rotation_-60_drift_resist_scan_-30': -30,
        'rotation_-60_drift_resist_scan_-20': -20,
        'rotation_-60_drift_resist_scan_-15': -15,
        'rotation_-60_drift_resist_scan_-10': -10,
        'rotation_-60_drift_resist_scan_-5': -5,
        'rotation_-60_drift_resist_scan_0': 0,
    }

    fig, ax = plt.subplots(figsize=(8, 6))
    for detector_name in detector_names:
        efficiencies = []
        total_events = []
        voltages = []
        for sub_run_name, voltage in sub_runs.items():
            analysis_dir = f'{base_dir}{run_name}/{sub_run_name}/'
            efficiency_file = f'{analysis_dir}/{detector_name}/coincident_events.csv'
            if not os.path.exists(efficiency_file):
                print(f'Efficiency file not found: {efficiency_file}')
                continue
            df = pd.read_csv(efficiency_file)
            efficiency = df['fraction_of_total_events'].iloc[0]
            total_event = df['total_triggers'].iloc[0]
            efficiencies.append(efficiency)
            total_events.append(total_event)
            voltages.append(voltage)
        ax.plot(voltages, efficiencies, marker='o', linestyle='-', label=detector_name)
    ax.set_xlabel('Mesh Voltage (V)')
    ax.set_ylabel('Efficiency')
    ax.set_title(f'Efficiency vs Resist Voltage in {run_name}')
    ax.grid(True)
    ax.set_ylim(0, 1)
    ax.legend()
    plt.tight_layout()

        # fig, ax = plt.subplots(figsize=(8, 6))
        # ax.plot(voltages, total_events, marker='o', linestyle='-')
        # ax.set_xlabel('Mesh Voltage (V)')
        # ax.set_ylabel('Total Events')
    plt.show()
    print('donzo')


if __name__ == '__main__':
    main()

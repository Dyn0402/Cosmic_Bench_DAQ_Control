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
    run_name = 'run_160'
    detector_names = [
        'urw_inter', 'rd5_plein_saral_2', 'rd5_plein_vfp_1',
        'rd5_grid_saral_1', 'rd5_strip_saral_1', 'rd5_strip_esl_1',
    ]
    sub_run_name = 'rotation_-45_resist_scan_'
    sub_run_zero = 'rotation_-45_drift_resist_scan_'
    sub_runs = {
        f'{sub_run_name}-105': -105,
        f'{sub_run_name}-100': -100,
        f'{sub_run_name}-95': -95,
        f'{sub_run_name}-90': -90,
        f'{sub_run_name}-85': -85,
        f'{sub_run_name}-80': -80,
        f'{sub_run_name}-70': -70,
        f'{sub_run_name}-65': -65,
        f'{sub_run_name}-60': -60,
        f'{sub_run_name}-55': -55,
        f'{sub_run_name}-45': -45,
        f'{sub_run_name}-40': -40,
        f'{sub_run_name}-35': -35,
        f'{sub_run_name}-30': -30,
        f'{sub_run_name}-20': -20,
        f'{sub_run_name}-15': -15,
        f'{sub_run_name}-10': -10,
        f'{sub_run_name}-5': -5,
        f'{sub_run_zero}0': 0,
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
    ax.set_xlabel('Resist Voltage (V)')
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

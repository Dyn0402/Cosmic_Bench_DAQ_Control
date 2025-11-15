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
        'rd5_plein_esl_1', 'rd5_plein_saral_2', 'rd5_plein_vfp_1',
        'rd5_grid_saral_1', 'rd5_strip_saral_1', 'rd5_strip_esl_1',
    ]

    nominal_drift_voltage = 500  # volts
    sub_runs = {
        'rotation_-60_drift_resist_scan_-475': nominal_drift_voltage - 475,
        'rotation_-60_drift_resist_scan_-450': nominal_drift_voltage-450,
        'rotation_-60_drift_resist_scan_-425': nominal_drift_voltage-425,
        'rotation_-60_drift_resist_scan_-400': nominal_drift_voltage-400,
        'rotation_-60_drift_resist_scan_-375': nominal_drift_voltage-375,
        'rotation_-60_drift_resist_scan_-350': nominal_drift_voltage-350,
        'rotation_-60_drift_resist_scan_-325': nominal_drift_voltage-325,
        'rotation_-60_drift_resist_scan_-300': nominal_drift_voltage-300,
        'rotation_-60_drift_resist_scan_-275': nominal_drift_voltage-275,
        'rotation_-60_drift_resist_scan_-250': nominal_drift_voltage-250,
        'rotation_-60_drift_resist_scan_-225': nominal_drift_voltage-225,
        'rotation_-60_drift_resist_scan_-200': nominal_drift_voltage-200,
        'rotation_-60_drift_resist_scan_-175': nominal_drift_voltage-175,
        'rotation_-60_drift_resist_scan_-150': nominal_drift_voltage-150,
        'rotation_-60_drift_resist_scan_-125': nominal_drift_voltage-125,
        'rotation_-60_drift_resist_scan_-100': nominal_drift_voltage-100,
        'rotation_-60_drift_resist_scan_-75': nominal_drift_voltage-75,
        'rotation_-60_drift_resist_scan_-50': nominal_drift_voltage-50,
        'rotation_-60_drift_resist_scan_-25': nominal_drift_voltage-25,
        'rotation_-60_drift_resist_scan_0': nominal_drift_voltage - 0,
    }

    fig, ax = plt.subplots(figsize=(8, 6))

    for detector_name in detector_names:
        voltages = []
        resolutions = []
        resolution_errs = []

        for sub_run_name, voltage in sub_runs.items():
            analysis_dir = f'{base_dir}{run_name}/{sub_run_name}/'
            timing_file = f'{analysis_dir}/{detector_name}/timing_resolution.csv'

            if not os.path.exists(timing_file):
                print(f'Time resolution file not found: {timing_file}')
                continue

            df = pd.read_csv(timing_file)

            # Expecting something like:
            # orientation | time_resolution_ns | time_resolution_err_ns | ...
            # X           | sigma_x            | sigma_x_err            | ...
            # Y           | sigma_y            | sigma_y_err            | ...

            # If multiple orientations exist, take the average (or choose X/Y)
            # Here we take the mean over orientations
            res = df['time_resolution_ns'].mean()
            res_err = np.sqrt((df['time_resolution_err_ns'] ** 2).sum())  # quadrature

            voltages.append(voltage)
            resolutions.append(res)
            resolution_errs.append(res_err)

        ax.errorbar(
            voltages, resolutions, yerr=resolution_errs,
            marker='o', linestyle='-', capsize=4, label=detector_name
        )

    ax.set_xlabel("Drift Voltage (V)")
    ax.set_ylabel("Time Resolution (ns)")
    ax.set_title(f"Time Resolution vs Voltage — {run_name}")
    ax.grid(True)
    ax.legend()
    plt.tight_layout()
    plt.show()

    print('donzo')


if __name__ == '__main__':
    main()

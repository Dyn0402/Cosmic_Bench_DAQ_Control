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

    nominal_drift_voltage = 400  # volts
    sub_run_name = 'rotation_-45_resist_scan_'
    sub_run_zero = 'rotation_-45_drift_resist_scan_'
    sub_runs = {
        f'{sub_run_name}-400': nominal_drift_voltage-400,
        f'{sub_run_name}-375': nominal_drift_voltage-375,
        f'{sub_run_name}-350': nominal_drift_voltage-350,
        f'{sub_run_name}-325': nominal_drift_voltage-325,
        f'{sub_run_name}-300': nominal_drift_voltage-300,
        f'{sub_run_name}-275': nominal_drift_voltage-275,
        f'{sub_run_name}-250': nominal_drift_voltage-250,
        f'{sub_run_name}-225': nominal_drift_voltage-225,
        f'{sub_run_name}-200': nominal_drift_voltage-200,
        f'{sub_run_name}-175': nominal_drift_voltage-175,
        f'{sub_run_name}-150': nominal_drift_voltage-150,
        f'{sub_run_name}-125': nominal_drift_voltage-125,
        f'{sub_run_name}-100': nominal_drift_voltage-100,
        f'{sub_run_name}-75': nominal_drift_voltage-75,
        f'{sub_run_name}-50': nominal_drift_voltage-50,
        f'{sub_run_name}-25': nominal_drift_voltage-25,
        f'{sub_run_zero}0': nominal_drift_voltage - 0,
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

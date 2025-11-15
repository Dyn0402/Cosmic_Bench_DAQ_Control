#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 15 12:54 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/run_config_fixer

@author: Dylan Neff, dn277127
"""

# Add parent directory to sys.path to import run_config_beam
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt

from run_config_beam import Config


def main():
    base_path = '/mnt/data/beam_sps_25/Run'

    if len(sys.argv) != 2:
        print('Usage: python run_config_fixer.py <run_num>')
        sys.exit(1)
    run_num = sys.argv[1]

    run_config_path = f'{base_path}/run_{run_num}/run_config.json'
    config = Config(run_config_path)
    print(config.included_detectors)
    grid_vfp1 = [det for det in config.detectors if det['name'] == 'rd5_grid_vfp_1'][0]
    # plein_saral1 = [det for det in config.detectors if det['name'] == 'rd5_plein_saral_1'][0]
    print(f'grid_vfp1 dream feus: {grid_vfp1["dream_feus"]}')
    # Check if plein_saral_1 exists in detectors and print yes or no
    print(f'plein_saral_1 exists: {"rd5_plein_saral_1" in [det["name"] for det in config.detectors]}')
    # print(plein_saral1)

    # Add plein_saral_1 to detectors
    plein_saral_1 = {
                'name': 'rd5_plein_saral_1',
                'det_type': 'rd5_plein_saral',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 900,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 1),
                    'resist_1': (2, 5),
                    'resist_2': (2, 6)
                },
                'dream_feus': {
                    'x_1': (4, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (4, 6),
                    'y_1': (4, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (4, 8),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            }

    print('donzo')


if __name__ == '__main__':
    main()

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
    plein_saral1 = [det for det in config.detectors if det['name'] == 'rd5_plein_saral_1'][0]
    print(f'grid_vfp1 dream feus: {grid_vfp1["dream_feus"]}')
    print(f'plein_saral1 dream feus: {plein_saral1["dream_feus"]}')

    plein_saral1['dream_feus'] = {
        'x_1': (4, 5),  # Runs along x direction, indicates y hit location
        'x_2': (4, 6),
        'y_1': (4, 7),  # Runs along y direction, indicates x hit location
        'y_2': (4, 8),
    }

    grid_vfp1['dream_feus'] = {
        'x_1': (4, 1),  # Runs along x direction, indicates y hit location
        'x_2': (4, 2),
        'y_1': (4, 3),  # Runs along y direction, indicates x hit location
        'y_2': (4, 4),
    }

    # Ask if user wants to update the config
    response = input('Do you want to update the run_config.json with these changes? (y/n): ')
    if response.lower() == 'y':
        config.write_to_file(run_config_path)
        print(f'Updated run_config.json saved to {run_config_path}')
    else:
        print('No changes made to run_config.json')

    print('donzo')


if __name__ == '__main__':
    main()

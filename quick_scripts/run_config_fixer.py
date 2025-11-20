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

    if len(sys.argv) == 2:
        run_nums = [sys.argv[1]]
    elif len(sys.argv) == 3:
        run_nums = [str(i) for i in range(int(sys.argv[1]), int(sys.argv[2]) + 1)]
    else:
        print('Usage: python run_config_fixer.py <run_num> OR python run_config_fixer.py <start_run_num> <end_run_num>')
        return

    for run_num in run_nums:
        run_config_path = f'{base_path}/run_{run_num}/run_config.json'
        config = Config(run_config_path)
        print(config.included_detectors)

        # fix_angles(config, run_config_path)
        # fix_strip_esl_angles(config, run_config_path)
        # fix_banco_heights(config, run_config_path)
        fix_strip_esl_positions(config, run_config_path)

    print('donzo')


def fix_strip_esl_positions(config, run_config_path):
    """
    Fix the positions of the strip esl detectors in the config.
    :param config:
    :param run_config_path:
    :return:
    """
    for detector in config.detectors:
        if detector['name'] != 'rd5_strip_esl_1':
            continue
        if 'det_center_coords' in detector:
            print(f'Original det_center_coords for {detector["name"]}: {detector["det_center_coords"]}')
            detector['det_center_coords']['z'] = 300
            print(f'Updated det_center_coords for {detector["name"]}: {detector["det_center_coords"]}')

    # Ask if user wants to update the config
    response = input('\nDo you want to update the run_config.json with these changes? (y/n): ')
    if response.lower() == 'y':
        config.write_to_file(run_config_path)
        print(f'Updated run_config.json saved to {run_config_path}')
    else:
        print('No changes made to run_config.json')


def fix_banco_heights(config, run_config_path):
    """
    Fix the heights of the banco detectors in the config. Should be in mm but we were using
    the units of the motor which are hundreds of um.
    :param config:
    :param run_config_path:
    :return:
    """
    config.bench_geometry['banco_moveable_y_position'] /= 10.0

    print(f'Updated banco_moveable_y_position to {config.bench_geometry["banco_moveable_y_position"]} mm')
    # Ask if user wants to update the config
    response = input('\nDo you want to update the run_config.json with these changes? (y/n): ')

    if response.lower() == 'y':
        config.write_to_file(run_config_path)
        print(f'Updated run_config.json saved to {run_config_path}')
    else:
        print('No changes made to run_config.json')



def fix_strip_esl_angles(config, run_config_path):
    """
    Fix the angles of the detectors in the config.
    :param config:
    :param run_config_path:
    :return:
    """

    # For detector in detectors, if 'det_orientation' 'y' is -300, change to -30
    for detector in config.detectors:
        if detector['name'] != 'rd5_strip_esl_1':
            continue
        if 'det_orientation' in detector:
                detector['det_orientation']['z'] = -90

    # Print the updated detector orientations
    print('Updated detector orientations:')
    for detector in config.detectors:
        if detector['name'] != 'rd5_strip_esl_1':
            continue
        if 'det_orientation' in detector:
            print(' ', detector['name'], detector['det_orientation'])

    # Ask if user wants to update the config
    response = input('\nDo you want to update the run_config.json with these changes? (y/n): ')
    if response.lower() == 'y':
        config.write_to_file(run_config_path)
        print(f'Updated run_config.json saved to {run_config_path}')
    else:
        print('No changes made to run_config.json')


def fix_angles(config, run_config_path):
    """
    Fix the angles of the detectors in the config.
    :param config:
    :param run_config_path:
    :return:
    """

    # For subrun in subruns, in sub_run_name change _30_ to _-30_
    for sub_run in config.sub_runs:
        sub_run_name = sub_run['sub_run_name']
        if '_30_' in sub_run_name:
            new_sub_run_name = sub_run_name.replace('_30_', '_-30_')
            print(f'Changing sub_run_name from {sub_run_name} to {new_sub_run_name}')
            sub_run['sub_run_name'] = new_sub_run_name

    # For detector in detectors, if 'det_orientation' 'y' is -300, change to -30
    for detector in config.detectors:
        if 'det_orientation' in detector:
            if detector['det_orientation']['y'] == -300:
                print(f'Changing det_orientation y from -300 to -30 for detector {detector["name"]}')
                detector['det_orientation']['y'] = -30

    # Print the updated sub_run_names and detector orientations
    print('Updated sub_run_names:')
    for sub_run in config.sub_runs:
        print(' ', sub_run['sub_run_name'])
    print('Updated detector orientations:')
    for detector in config.detectors:
        if 'det_orientation' in detector:
            print(' ', detector['name'], detector['det_orientation'])

    # Ask if user wants to update the config
    response = input('\nDo you want to update the run_config.json with these changes? (y/n): ')
    if response.lower() == 'y':
        config.write_to_file(run_config_path)
        print(f'Updated run_config.json saved to {run_config_path}')
    else:
        print('No changes made to run_config.json')


def fix_dream_feus(config, run_config_path):
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


if __name__ == '__main__':
    main()

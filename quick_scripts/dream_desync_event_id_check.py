#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 09 11:38 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/dream_desync_event_id_check

@author: Dylan Neff, dn277127
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import uproot


def main():
    # base_dir = '/mnt/data/beam_sps_25/Bad_Runs_Repo/run_23/resist_hv_-10'
    base_dir = '/mnt/data/beam_sps_25/Run/run_24/resist_hv_-10'

    banco_dir = f'{base_dir}/banco_data/'
    dream_dir = f'{base_dir}/filtered_root/'

    banco_file_paths = []
    for file in os.listdir(banco_dir):
        if file.endswith('.root'):
            banco_file_paths.append(os.path.join(banco_dir, file))

    print('banco files found:')
    for path in banco_file_paths:
        print(' ', path.split('/')[-1])

    dream_file_paths = []
    for file in os.listdir(dream_dir):
        if file.endswith('_array_filtered.root'):
            dream_file_paths.append(os.path.join(dream_dir, file))

    print('dream files found:')
    for path in dream_file_paths:
        print(' ', path.split('/')[-1])

    # Get all max trgNum and eventId from all files
    dream_max_event_ids = []
    for dream_root_path in dream_file_paths:
        dream_file = uproot.open(dream_root_path)
        dream_tree = dream_file['nt']
        dream_event_id_branch = dream_tree['eventId']
        dream_event_ids = dream_event_id_branch.array(library='np')
        dream_max_event_ids.append(np.max(dream_event_ids))

    banco_max_event_ids = []
    for banco_root_path in banco_file_paths:
        banco_file = uproot.open(banco_root_path)
        banco_tree = banco_file['pixTree']
        banco_data_branch = banco_tree['fData']
        banco_data = banco_data_branch.array(library='np')
        trg_nums = banco_data['trgNum']
        banco_max_event_ids.append(np.max(trg_nums))

    print()
    print('Dream max event IDs per file:', dream_max_event_ids)
    print('Banco max trgNums per file:', banco_max_event_ids)

    # Check if all dreams match within themselves
    all_dreams_match = all(x == dream_max_event_ids[0] for x in dream_max_event_ids)
    if all_dreams_match:
        print('All Dream files have matching max event IDs:', dream_max_event_ids[0])
    else:
        print('Dream files have differing max event IDs:', dream_max_event_ids)

    # Check if all bancos match within themselves
    all_bancos_match = all(x == banco_max_event_ids[0] for x in banco_max_event_ids)
    if all_bancos_match:
        print('All Banco files have matching max trgNums:', banco_max_event_ids[0])
    else:
        print('Banco files have differing max trgNums:', banco_max_event_ids)

    # Compare dream and banco max event IDs
    if all_dreams_match and all_bancos_match:
        if dream_max_event_ids[0] == banco_max_event_ids[0]:
            print('Dream and Banco max event IDs match:', dream_max_event_ids[0])
        else:
            print('Mismatch between Dream and Banco max event IDs:')
            print('  Dream max event ID:', dream_max_event_ids[0])
            print('  Banco max trgNum:', banco_max_event_ids[0])
    else:
        print('Cannot compare Dream and Banco max event IDs due to internal mismatches.')

    print('donzo')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 09 11:38 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/dream_desync_event_id_check

@author: Dylan Neff, dn277127
"""

import numpy as np
import matplotlib.pyplot as plt
import uproot


def main():
    base_dir = '/mnt/data/beam_sps_25/Bad_Runs_Repo/run_21/resist_hv_-10/'
    banco_root_path = f'{base_dir}/banco_data/multinoiseScan_251109_110345-B0-ladder157.root'
    dream_root_path = f'{base_dir}/filtered_root/TbSPS25_resist_hv_-10_datrun_251109_11H03_000_05_decoded_array_filtered.root'

    banco_file = uproot.open(banco_root_path)
    dream_file = uproot.open(dream_root_path)

    print('banco keys:', banco_file.keys())
    print('dream keys:', dream_file.keys())

    banco_tree = banco_file['pixTree']
    dream_tree = dream_file['nt']

    print('banco branches:', banco_tree.keys())
    print('dream branches:', dream_tree.keys())

    banco_data_branch = banco_tree['fData']
    dream_event_id_branch = dream_tree['eventId']

    banco_data = banco_data_branch.array(library='np')
    dream_event_ids = dream_event_id_branch.array(library='np')

    trg_nums, chip_nums, col_nums, row_nums = banco_data['trgNum'], banco_data['chipId'], banco_data['col'], banco_data['row']

    print(f'Max trgNum in banco: {np.max(trg_nums)}')
    print(f'Max eventId in dream: {np.max(dream_event_ids)}')

    print('donzo')


if __name__ == '__main__':
    main()

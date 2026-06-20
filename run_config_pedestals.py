#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 9:37 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/run_config_pedestals.py

@author: Dylan Neff, Dylan
"""

import os
import json
import copy
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_config import Config as RunConfig


class Config:
    def __init__(self):
        # Pull all hardware / detector settings from the active run config so
        # the two files never drift apart.
        run = RunConfig()
        self.__dict__.update(run.__dict__)

        # --- Pedestal-specific overrides ---
        date_str = datetime.now().strftime('%m-%d-%y_%H-%M-%S')
        self.run_name = f'pedestals_{date_str}'
        self.data_out_dir = f'{self.base_out_dir}pedestals/'
        self.run_out_dir  = f'{self.data_out_dir}{self.run_name}/'

        self.power_off_hv_at_end = False
        self.start_time = None

        # dream_daq_info: inherit from run config, then force pedestal-mode flags
        self.dream_daq_info = copy.deepcopy(run.dream_daq_info)
        self.dream_daq_info.update({
            'run_directory':          f'{self.base_out_dir}dream_run/{self.run_name}/',
            'data_out_dir':           self.run_out_dir,
            'zero_suppress':          False,   # always full readout for pedestals
            'pedestal_subtraction':   False,
            'common_noise_subtraction': False,
            'pedestals_dir':          None,    # no existing pedestals applied
            'pedestals':              None,
            'do_pedestal_threshold_run': True,   # Sys Action PedThrRun (bool/int/str → 0 or 1)
            'do_trigger_threshold_run': False,   # Sys Action TrgThrRun
            'do_data_run': True,                 # Sys Action DataRun
        })

        # Point HV info at the pedestal output dir. (Everything else, including
        # any processor info, is already inherited via __dict__.update above.)
        self.hv_info = copy.deepcopy(run.hv_info)
        self.hv_info['run_out_dir'] = self.run_out_dir

        # Single pedestal subrun — set all channels to 0 V.
        # Adjust hvs here if low-voltage bias is needed during pedestal acquisition.
        self.sub_runs = [
            {
                'sub_run_name': 'pedestals',
                'run_time': 10 / 60,  # Minutes
                'hvs': {
                    0: {
                        0: 200,
                        1: 200,
                        2: 200,
                        3: 200,
                        4: 200,
                        5: 200,
                        6: 200,
                        7: 200,
                        8: 200,
                        9: 200,
                        10: 200,
                        11: 200,
                    },
                    3: {
                        0: 200,
                        1: 200,
                        2: 200,
                        3: 200,
                        4: 200,
                        5: 200,
                        6: 200,
                        7: 200,
                        8: 200,
                        9: 200,
                        10: 200,
                        11: 200,
                    },
                },
            }
        ]

    def write_to_file(self, file_path):
        with open(file_path, 'w') as f:
            json.dump(self.__dict__, f, indent=4)

    def load_from_file(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        self.__dict__.clear()
        self.__dict__.update(data)


if __name__ == '__main__':
    out_run_dir = '/local/home/usernsw/Cosmic_Bench_DAQ_Control/config/json_run_configs'
    config = Config()
    config.write_to_file(os.path.join(out_run_dir, 'run_config_pedestals.json'))
    print('donzo')

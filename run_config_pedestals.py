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

        # Pedestal bias applied only to HV channels that belong to a detector
        # included in run_config.py (self.detectors is already filtered to the
        # included detectors). Channels not used by an included detector are left
        # untouched, so we no longer ramp the whole crate for pedestals.
        ped_voltage = 200  # V; adjust if a different pedestal bias is needed
        ped_hvs = {}
        for det in self.detectors:
            hv_channels = det.get('hv_channels')
            if not isinstance(hv_channels, dict):
                continue  # e.g. banco ('banco' string) or detectors with no HV
            for slot, channel in hv_channels.values():
                ped_hvs.setdefault(slot, {})[channel] = ped_voltage

        # Single pedestal subrun — only the HV channels defined in run_config.py.
        self.sub_runs = [
            {
                'sub_run_name': 'pedestals',
                'run_time': 10 / 60,  # Minutes
                'hvs': ped_hvs,
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

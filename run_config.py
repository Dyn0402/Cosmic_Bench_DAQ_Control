#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 9:37 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/run_config.py

@author: Dylan Neff, Dylan
"""


class Config:
    def __init__(self):
        self.run_name = 'test_run'
        self.daq_dir = '/home/clas12/dylan/Run/'
        self.run_dir = f'{self.daq_dir}{self.run_name}/'
        self.daq_config_path = '../CosmicTb_TPOT.cfg'

        self.hv_info = {
            'hv_ip_address': '192.168.10.81',
            'hv_username': 'admin',
            'hv_password': 'admin',
            'n_cards': 4,
            'n_channels_per_card': 12,
        }

        self.sub_runs = [
            {
                'sub_run_name': 'sub_run_0',
                'run_time': 10,
                'hvs': {
                    1: {
                        1: 50,
                        2: 100,
                        3: 150
                    },
                    2: {
                        2: 200,
                        3: 250
                    }
                }
            },
            {
                'sub_run_name': 'sub_run_1',
                'run_time': 20,
                'hvs': {
                    1: {
                        0: 100,
                        1: 150,
                        2: 200
                    },
                    2: {
                        2: 250,
                        3: 300
                    }
                }
            }
        ]




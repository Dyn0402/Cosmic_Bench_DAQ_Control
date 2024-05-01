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
        self.run_name = 'm3_hv_scan'
        self.daq_dir = '/home/clas12/dylan/Run/'
        self.run_dir = f'{self.daq_dir}{self.run_name}/'
        self.daq_config_path = '../CosmicTb_TPOT.cfg'
        self.banco_daq_run_path = '/home/banco/Test_Beam/framework/bin/test_multi_noiseocc_int'

        self.hv_info = {
            'hv_ip_address': '192.168.10.81',
            'hv_username': 'admin',
            'hv_password': 'admin',
            'n_cards': 4,
            'n_channels_per_card': 12,
        }

        self.sub_runs = [
            {
                'sub_run_name': 'mesh440',
                'run_time': 10,  # Minutes
                'hvs': {
                    0: {
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500
                    },
                    3: {
                        8: 440,
                        9: 440,
                        10: 440,
                        11: 440
                    }
                }
            },
            {
                'sub_run_name': 'mesh445',
                'run_time': 10,  # Minutes
                'hvs': {
                    0: {
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500
                    },
                    3: {
                        8: 445,
                        9: 445,
                        10: 445,
                        11: 445
                    }
                }
            },
            {
                'sub_run_name': 'mesh450',
                'run_time': 10,  # Minutes
                'hvs': {
                    0: {
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500
                    },
                    3: {
                        8: 450,
                        9: 450,
                        10: 450,
                        11: 450
                    }
                }
            },
            {
                'sub_run_name': 'mesh455',
                'run_time': 10,  # Minutes
                'hvs': {
                    0: {
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500
                    },
                    3: {
                        8: 455,
                        9: 455,
                        10: 455,
                        11: 455
                    }
                }
            },
            {
                'sub_run_name': 'mesh460',
                'run_time': 10,  # Minutes
                'hvs': {
                    0: {
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500
                    },
                    3: {
                        8: 460,
                        9: 460,
                        10: 460,
                        11: 460
                    }
                }
            },
        ]

        self.sub_runs_test = [
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




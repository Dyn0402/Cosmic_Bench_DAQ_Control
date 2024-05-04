#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 9:37 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/run_config.py

@author: Dylan Neff, Dylan
"""

import json


class Config:
    def __init__(self):
        self.run_name = 'm3_hv_scan'
        self.daq_dir = '/home/clas12/dylan/Run/'
        self.run_dir = f'{self.daq_dir}{self.run_name}/'
        self.daq_config_path = '../../config/CosmicTb_TPOT.cfg'

        self.banco_info = {
            'daq_run_path': '/home/banco/Test_Beam/framework/bin/test_multi_noiseocc_int',
            'data_out_dir': '/home/banco/dylan/Run/',
        }
        # self.banco_daq_run_path = '/home/banco/Test_Beam/framework/bin/test_multi_noiseocc_int'

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
                'run_time': 30,  # Minutes
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
                'run_time': 30,  # Minutes
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
                'run_time': 30,  # Minutes
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
                'run_time': 30,  # Minutes
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
                'run_time': 30,  # Minutes
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
            {
                'sub_run_name': 'mesh465',
                'run_time': 30,  # Minutes
                'hvs': {
                    0: {
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500
                    },
                    3: {
                        8: 465,
                        9: 465,
                        10: 465,
                        11: 465
                    }
                }
            },
            {
                'sub_run_name': 'mesh470',
                'run_time': 30,  # Minutes
                'hvs': {
                    0: {
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500
                    },
                    3: {
                        8: 470,
                        9: 470,
                        10: 470,
                        11: 470
                    }
                }
            },
        ]

        self.bench_geometry = {
            'p1_z': 226,  # mm  To the top of P1 from the top of PB
            'bottom_level_z': 95,  # mm  From the top of P1 to the bottom level of stand
            'level_z_spacing': 92,  # mm  Spacing between levels on stand
        }

        self.detectors = [
            # {
            #     'name': 'banco',
            #     'strip_map_type': 'banco',
            #     'resist_map_type': 'banco',
            #     'det_center_coords': {  # Center of detector
            #         'x': 0,  # mm
            #         'y': 0,  # mm
            #         'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
            #              5 * self.bench_geometry['level_z_spacing'] + 50,  # mm
            #     },
            #     'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
            #         'x': 130,  # mm
            #         'y': 130,  # mm
            #         'z': 4,  # mm
            #     },
            #     'hv_channels': 'banco',
            #     'dream_feus': 'banco',
            # },
            # {
            #     'name': 'urw_strip',
            #     'strip_map_type': 'strip',
            #     'resist_map_type': 'plein',
            #     'det_center_coords': {  # Center of detector
            #         'x': 0,  # mm
            #         'y': 0,  # mm
            #         'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
            #              5 * self.bench_geometry['level_z_spacing'],  # mm
            #     },
            #     'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
            #         'x': 130,  # mm
            #         'y': 130,  # mm
            #         'z': 4,  # mm
            #     },
            #     'hv_channels': {
            #         'drift': (0, 0),
            #         'resist_1': (3, 1)
            #     },
            #     'dream_feus': {
            #         'x_1': (6, 5),  # Runs along x direction, indicates y hit location
            #         'x_2': (6, 6),
            #         'y_1': (6, 7),  # Runs along y direction, indicates x hit location
            #         'y_2': (6, 8),
            #     },
            # },
            # {
            #     'name': 'urw_inter',
            #     'strip_map_type': 'inter',
            #     'resist_map_type': 'plein',
            #     'det_center_coords': {  # Center of detector
            #         'x': 0,  # mm
            #         'y': 0,  # mm
            #         'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
            #              4 * self.bench_geometry['level_z_spacing'],  # mm
            #     },
            #     'hv_channels': {
            #         'drift': (0, 1),
            #         'resist_1': (3, 2)
            #     },
            #     'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
            #         'x': 130,  # mm
            #         'y': 130,  # mm
            #         'z': 4,  # mm
            #     },
            #     'dream_feus': {
            #         'x_1': (6, 1),  # Runs along x direction, indicates y hit location
            #         'x_2': (6, 2),
            #         'y_1': (6, 3),  # Runs along y direction, indicates x hit location
            #         'y_2': (6, 4),
            #     },
            # },
            # {
            #     'name': 'asacusa_strip_1',
            #     'strip_map_type': 'asacusa',
            #     'resist_map_type': 'strip',
            #     'det_center_coords': {  # Center of detector
            #         'x': 0,  # mm
            #         'y': 0,  # mm
            #         'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
            #              3 * self.bench_geometry['level_z_spacing'],  # mm
            #     },
            #     'hv_channels': {
            #         'drift': (0, 2),
            #         'resist_1': (3, 3),
            #         'resist_2': (3, 4),
            #     },
            #     'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
            #         'x': 130,  # mm
            #         'y': 130,  # mm
            #         'z': 4,  # mm
            #     },
            #     'dream_feus': {
            #         'x_1': (4, 5),  # Runs along x direction, indicates y hit location
            #         'x_2': (4, 6),
            #         'y_1': (4, 7),  # Runs along y direction, indicates x hit location
            #         'y_2': (4, 8),
            #     },
            # },
            # {
            #     'name': 'asacusa_strip_2',
            #     'strip_map_type': 'asacusa',
            #     'resist_map_type': 'strip',
            #     'det_center_coords': {  # Center of detector
            #         'x': 0,  # mm
            #         'y': 0,  # mm
            #         'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
            #              2 * self.bench_geometry['level_z_spacing'],  # mm
            #     },
            #     'hv_channels': {
            #         'drift': (0, 3),
            #         'resist_1': (3, 5),
            #         'resist_2': (3, 6)
            #     },
            #     'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
            #         'x': 130,  # mm
            #         'y': 130,  # mm
            #         'z': 4,  # mm
            #     },
            #     'dream_feus': {
            #         'x_1': (4, 1),  # Runs along x direction, indicates y hit location
            #         'x_2': (4, 2),
            #         'y_1': (4, 3),  # Runs along y direction, indicates x hit location
            #         'y_2': (4, 4),
            #     },
            # },
            # {
            #     'name': 'asacusa_plein_1',
            #     'strip_map_type': 'asacusa',
            #     'resist_map_type': 'plein',
            #     'det_center_coords': {  # Center of detector
            #         'x': 0,  # mm
            #         'y': 0,  # mm
            #         'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
            #              1 * self.bench_geometry['level_z_spacing'],  # mm
            #     },
            #     'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
            #         'x': 130,  # mm
            #         'y': 130,  # mm
            #         'z': 4,  # mm
            #     },
            #     'hv_channels': {
            #         'drift': (0, 4),
            #         'resist_1': (3, 7),
            #         'resist_2': (2, 0)
            #     },
            #     'dream_feus': {
            #         'x_1': (3, 5),  # Runs along x direction, indicates y hit location
            #         'x_2': (3, 6),
            #         'y_1': (3, 7),  # Runs along y direction, indicates x hit location
            #         'y_2': (3, 8),
            #     },
            # },
            {
                'name': 'm3_bot_bot',
                'strip_map_type': 'm3',
                'resist_map_type': 'm3',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 28,  # mm  Need to figure out height of active area, this is top of fixture
                },
                'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                    'x': 500,  # mm
                    'y': 500,  # mm
                    'z': 4,  # mm  Guess
                },
                'hv_channels': {  # Don't know HTM# matching to geometric layout, guessing
                    'drift': (0, 8),
                    'mesh_1': (3, 8)
                },
                'dream_feus': {  # Guesses
                    'x_1': (1, 1),  # Runs along x direction, indicates y hit location
                    'y_1': (1, 2),  # Runs along y direction, indicates x hit location
                },
            },
            {
                'name': 'm3_bot_top',
                'strip_map_type': 'm3',
                'resist_map_type': 'm3',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 145,  # mm  Need to figure out height of active area, this is top of fixture
                },
                'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                    'x': 500,  # mm
                    'y': 500,  # mm
                    'z': 4,  # mm  Guess
                },
                'hv_channels': {  # Don't know HTM# matching to geometric layout, guessing
                    'drift': (0, 9),
                    'mesh_1': (3, 9)
                },
                'dream_feus': {  # Guesses
                    'x_1': (1, 3),  # Runs along x direction, indicates y hit location
                    'y_1': (1, 4),  # Runs along y direction, indicates x hit location
                },
            },
            {
                'name': 'm3_top_bot',
                'strip_map_type': 'm3',
                'resist_map_type': 'm3',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1163 + 28,  # mm  Need to figure out height of active area, this is top of fixture
                },
                'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                    'x': 500,  # mm
                    'y': 500,  # mm
                    'z': 4,  # mm  Guess
                },
                'hv_channels': {  # Don't know HTM# matching to geometric layout, guessing
                    'drift': (0, 10),
                    'mesh_1': (3, 10)
                },
                'dream_feus': {  # Guesses
                    'x_1': (1, 5),  # Runs along x direction, indicates y hit location
                    'y_1': (1, 6),  # Runs along y direction, indicates x hit location
                },
            },
            {
                'name': 'm3_top_top',
                'strip_map_type': 'm3',
                'resist_map_type': 'm3',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1163 + 145,  # mm  Need to figure out height of active area, this is top of fixture
                },
                'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                    'x': 500,  # mm
                    'y': 500,  # mm
                    'z': 4,  # mm  Guess
                },
                'hv_channels': {  # Don't know HTM# matching to geometric layout, guessing
                    'drift': (0, 11),
                    'mesh_1': (3, 11)
                },
                'dream_feus': {  # Guesses
                    'x_1': (1, 7),  # Runs along x direction, indicates y hit location
                    'y_1': (1, 8),  # Runs along y direction, indicates x hit location
                },
            },
        ]

    def write_to_file(self, file_path):
        with open(file_path, 'w') as file:
            json.dump(self.__dict__, file, indent=4)

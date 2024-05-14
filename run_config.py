#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 9:37 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/run_config_template.py

@author: Dylan Neff, Dylan
"""

import json


class Config:
    def __init__(self):
        self.run_name = 'hv_scan_no_banco_5_14_24'
        self.daq_dir = '/home/clas12/dylan/Run/'
        self.run_dir = f'{self.daq_dir}{self.run_name}/'
        self.data_out_dir = '/mnt/cosmic_data/Run/'
        self.run_out_dir = f'{self.data_out_dir}{self.run_name}/'
        self.raw_daq_inner_dir = 'raw_daq_data'
        self.decoded_root_inner_dir = 'decoded_root'
        self.m3_tracking_inner_dir = 'm3_tracking'

        self.dream_daq_info = {
            'daq_config_template_path': '/home/clas12/dylan/Run/config/CosmicTb_TPOT.cfg',
        }

        self.banco_info = {
            'ip': '132.166.30.82',
            'port': 1100,
            'daq_run_path': '/home/banco/Test_Beam/framework/bin/test_multi_noiseocc_int',
            'data_temp_dir': '/home/banco/Test_Beam/data',
            'data_out_dir': f'/mnt/cosmic_data/Run/{self.run_name}',
            'data_inner_dir': self.raw_daq_inner_dir
        }

        self.processor_info = {
            'ip': '132.166.10.196',
            'port': 1100,
            'run_dir': f'/mnt/cosmic_data/Run/{self.run_name}',
            'raw_daq_inner_dir': self.raw_daq_inner_dir,
            'decoded_root_inner_dir': self.decoded_root_inner_dir,
            'm3_tracking_inner_dir': self.decoded_root_inner_dir,
            'source_root_path': '/local/home/banco/P2/root/bin/thisroot.sh',
            'decode_path': '/local/home/banco/dylan/decode/decode',
            'convert_path': '/local/home/banco/dylan/decode/convert_vec_tree_to_array',
            'tracking_run_dir': '/local/home/banco/dylan/m3_tracking/',
            'tracking_sh_path': '/local/home/banco/dylan/m3_tracking/run_tracking_single.sh',
            'out_type': 'both',  # 'vec', 'array', or 'both'
        }

        self.hv_control_info = {
            'ip': '192.168.10.1',
            'port': 1100,
        }

        self.hv_info = {
            'ip': '192.168.10.81',
            'username': 'admin',
            'password': 'admin',
            'n_cards': 4,
            'n_channels_per_card': 12,
        }

        self.trigger_switch_info = {
            'ip': '192.168.10.101',
            'port': 1100,
        }

        self.sub_runs = [
            # {
            #     'sub_run_name': 'HV7',
            #     'run_time': 90,  # Minutes
            #     'hvs': {
            #         0: {
            #             0: 600,
            #             1: 600,
            #             2: 800,
            #             3: 800,
            #             6: 800,
            #             8: 500,
            #             9: 500,
            #             10: 500,
            #             11: 500,
            #         },
            #         2: {
            #             0: 450,
            #         },
            #         3: {
            #             1: 365,
            #             2: 410,
            #             3: 450,
            #             4: 450,
            #             5: 450,
            #             6: 450,
            #             8: 460,
            #             9: 460,
            #             10: 460,
            #             11: 460,
            #         }
            #     }
            # },
            # {
            #     'sub_run_name': 'HV6',
            #     'run_time': 90,  # Minutes
            #     'hvs': {
            #         0: {
            #             0: 600,
            #             1: 600,
            #             2: 800,
            #             3: 800,
            #             6: 800,
            #             8: 500,
            #             9: 500,
            #             10: 500,
            #             11: 500,
            #         },
            #         2: {
            #             0: 445,
            #         },
            #         3: {
            #             1: 360,
            #             2: 405,
            #             3: 445,
            #             4: 445,
            #             5: 445,
            #             6: 445,
            #             8: 460,
            #             9: 460,
            #             10: 460,
            #             11: 460,
            #         }
            #     }
            # },
            {
                'sub_run_name': 'HV5',
                'run_time': 90,  # Minutes
                'hvs': {
                    0: {
                        0: 600,
                        1: 600,
                        2: 800,
                        3: 800,
                        6: 800,
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500,
                    },
                    2: {
                        0: 440,
                    },
                    3: {
                        1: 355,
                        2: 400,
                        3: 440,
                        4: 440,
                        5: 440,
                        6: 440,
                        8: 460,
                        9: 460,
                        10: 460,
                        11: 460,
                    }
                }
            },
            {
                'sub_run_name': 'HV4',
                'run_time': 90,  # Minutes
                'hvs': {
                    0: {
                        0: 600,
                        1: 600,
                        2: 800,
                        3: 800,
                        6: 800,
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500
                    },
                    2: {
                        0: 435,
                    },
                    3: {
                        1: 350,
                        2: 395,
                        3: 435,
                        4: 435,
                        5: 435,
                        6: 435,
                        8: 460,
                        9: 460,
                        10: 460,
                        11: 460,
                    }
                }
            },
            # {
            #     'sub_run_name': 'HV3',
            #     'run_time': 90,  # Minutes
            #     'hvs': {
            #         0: {
            #             0: 600,
            #             1: 600,
            #             2: 800,
            #             3: 800,
            #             6: 800,
            #             8: 500,
            #             9: 500,
            #             10: 500,
            #             11: 500
            #         },
            #         2: {
            #             0: 430,
            #         },
            #         3: {
            #             1: 345,
            #             2: 390,
            #             3: 430,
            #             4: 430,
            #             5: 430,
            #             6: 430,
            #             8: 460,
            #             9: 460,
            #             10: 460,
            #             11: 460,
            #         }
            #     }
            # },
            # {
            #     'sub_run_name': 'HV2',
            #     'run_time': 90,  # Minutes
            #     'hvs': {
            #         0: {
            #             0: 600,
            #             1: 600,
            #             2: 800,
            #             3: 800,
            #             6: 800,
            #             8: 500,
            #             9: 500,
            #             10: 500,
            #             11: 500
            #         },
            #         2: {
            #             0: 425,
            #         },
            #         3: {
            #             1: 340,
            #             2: 385,
            #             3: 425,
            #             4: 425,
            #             5: 425,
            #             6: 425,
            #             8: 460,
            #             9: 460,
            #             10: 460,
            #             11: 460,
            #         }
            #     }
            # },
            # {
            #     'sub_run_name': 'HV1',
            #     'run_time': 90,  # Minutes
            #     'hvs': {
            #         0: {
            #             0: 600,
            #             1: 600,
            #             2: 800,
            #             3: 800,
            #             6: 800,
            #             8: 500,
            #             9: 500,
            #             10: 500,
            #             11: 500
            #         },
            #         2: {
            #             0: 420,
            #         },
            #         3: {
            #             1: 335,
            #             2: 380,
            #             3: 420,
            #             4: 420,
            #             5: 420,
            #             6: 420,
            #             8: 460,
            #             9: 460,
            #             10: 460,
            #             11: 460,
            #         }
            #     }
            # },
        ]

        self.bench_geometry = {
            'p1_z': 227,  # mm  To the top of P1 from the top of PB
            'bottom_level_z': 82,  # mm  From the top of P1 to the bottom level of stand
            'level_z_spacing': 97,  # mm  Spacing between levels on stand
            'board_thickness': 5,  # mm  Thickness of PCB for test boards
            'banco_arm_bottom_to_center': 10,  # mm from bottom of lower banco arm to center of banco arm Guess!
            'banco_arm_separation_z': 71 - 44,  # mm from bottom of lower banco arm to bottom of upper banco arm
            'banco_arm_right_y': 34 + 100,  # mm from center of banco to right edge of banco arm
            'banco_arm_length_y': 230,  # mm from left edge of banco arm to right edge of banco arm
        }

        self.included_detectors = ['urw_strip', 'urw_inter', 'asacusa_strip_1', 'asacusa_strip_2',
                                   'asacusa_plein_1', 'm3_bot_bot', 'm3_bot_top', 'm3_top_bot', 'm3_top_top']

        self.detectors = [
            {
                'name': 'banco',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm  Centered by eye on top test detector's center screw
                    # y is measured from the right edge of the banco arm and center computed from measured length
                    'y': self.bench_geometry['banco_arm_right_y'] - self.bench_geometry['banco_arm_length_y'] / 2,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         5 * self.bench_geometry['level_z_spacing'] + 44,  # mm  To bottom of carbon on lower banco arm
                },
                'hv_channels': 'banco',
                'dream_feus': 'banco',
            },
            {
                'name': 'urw_strip',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         5 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                },
                'hv_channels': {
                    'drift': (0, 0),
                    'resist_1': (3, 1)
                },
                'dream_feus': {
                    'x_1': (6, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 6),
                    'y_1': (6, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 8),
                },
            },
            {
                'name': 'urw_inter',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         4 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                },
                'hv_channels': {
                    'drift': (0, 1),
                    'resist_1': (3, 2)
                },
                'dream_feus': {
                    'x_1': (6, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 2),
                    'y_1': (6, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 4),
                },
            },
            {
                'name': 'asacusa_strip_1',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         3 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                },
                'hv_channels': {
                    'drift': (0, 2),
                    'resist_1': (3, 3),
                    'resist_2': (3, 4),
                },
                'dream_feus': {
                    'x_1': (4, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (4, 6),
                    'y_1': (4, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (4, 8),
                },
            },
            {
                'name': 'asacusa_strip_2',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         2 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                },
                'hv_channels': {
                    'drift': (0, 3),
                    'resist_1': (3, 5),
                    'resist_2': (3, 6)
                },
                'dream_feus': {
                    'x_1': (4, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (4, 2),
                    'y_1': (4, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (4, 4),
                },
            },
            {
                'name': 'asacusa_plein_1',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         1 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                },
                'hv_channels': {
                    'drift': (0, 4),
                    'resist_1': (3, 7),
                    'resist_2': (2, 0)
                },
                'dream_feus': {
                    'x_1': (3, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (3, 6),
                    'y_1': (3, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (3, 8),
                },
            },
            {
                'name': 'm3_bot_bot',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 24,  # mm  28 from geometry diagram, 24 from m3 config json
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
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 144,  # mm  145 from geometry diagram, 144 from m3 config json
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
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1185,  # mm  1163 + 28 from geometry diagram, 1185 from m3 config json
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
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1302,  # mm  1163 + 145 from geometry diagram, 1302 from m3 config json
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

        self.detectors = [det for det in self.detectors if det['name'] in self.included_detectors]

    def write_to_file(self, file_path):
        with open(file_path, 'w') as file:
            json.dump(self.__dict__, file, indent=4)

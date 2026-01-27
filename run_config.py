#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 9:37 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/run_config_template.py

@author: Dylan Neff, Dylan
"""

import json
import copy


class Config:
    def __init__(self):
        self.run_name = 'mx17_det1_overnight_run_1-27-26'
        self.data_out_dir = '/mnt/cosmic_data/Run/'
        self.run_out_dir = f'{self.data_out_dir}{self.run_name}/'
        self.raw_daq_inner_dir = 'raw_daq_data'
        self.decoded_root_inner_dir = 'decoded_root'
        self.filtered_root_inner_dir = 'filtered_root'
        self.m3_tracking_inner_dir = 'm3_tracking_root'
        self.detector_info_dir = f'/mnt/cosmic_data/config/detectors/'
        self.m3_feu_num = 1
        self.power_off_hv_at_end = False  # True to power off HV at end of run
        self.filtering_by_m3 = False  # True to filter by m3 tracking, False to do no filtering
        self.process_on_fly = True  # True to process data on fly, False to process after run
        self.save_fdfs = True  # True to save FDF files, False to delete after decoding
        self.start_time = None  # '2024-06-03 15:30:00'  # 'YYYY-MM-DD HH:MM:SS' or None to start immediately
        self.write_all_dectors_to_json = False  # Only when making run config json template.
        self.generate_external_triggers = False  # If true, use raspberry pi to generate external triggers for DAQ
        self.gas = 'Ar/Iso 95/5'  # Gas type for run
        # self.gas = 'Ar/CO2/Iso 93/5/2'  # Gas type for run

        self.dream_daq_info = {
            # 'ip': '192.168.10.100',
            'ip': '192.168.10.1',
            'port': 1101,
            'daq_config_template_path': '/local/home/usernsw/dylan/Run/config/CosmicTb_MX17.cfg',
            # 'daq_config_template_path': '/local/home/usernsw/dylan/Run/config/CosmicTb_TPOT.cfg',
            # 'daq_config_template_path': '/local/home/usernsw/dylan/Run/config/CosmicTb_TPOT_P2.cfg',
            # 'daq_config_template_path': '/local/home/usernsw/dylan/Run/config/CosmicTb_SelfTrigger_thresh.cfg',
            # 'run_directory': f'/local/home/usernsw/dylan/Run/{self.run_name}/',
            'run_directory': f'/data/cosmic_data/Run/{self.run_name}/',
            'data_out_dir': f'/mnt/cosmic_data/Run/{self.run_name}',
            'raw_daq_inner_dir': self.raw_daq_inner_dir,
            'go_timeout': 7 * 60,  # Seconds to wait for 'Go' response from RunCtrl before assuming failure
            'max_run_time_addition': 60 * 5,  # Seconds to add to requested run time before killing run
            'copy_on_fly': True,  # True to copy raw data to out dir during run, False to copy after run
            'batch_mode': True,  # Run Dream RunCtrl in batch mode. Not implemented for cosmic bench C
            'zero_suppress': False,  # True to run in zero suppression mode, False to run in full readout mode
        }

        self.banco_info = {
            'ip': '132.166.30.82',
            'port': 1100,
            'daq_run_command': 'cd /home/banco/dylan/Run/framework/bin && ./test_multi_noiseocc_int',
            'data_temp_dir': '/home/banco/dylan/Run/data',
            'data_out_dir': f'/mnt/cosmic_data/Run/{self.run_name}',
            'data_inner_dir': 'banco_data'
        }

        self.dedip196_processor_info = {
            'ip': '192.168.10.1',
            'port': 1201,
            'run_dir': f'/mnt/cosmic_data/Run/{self.run_name}',
            'raw_daq_inner_dir': self.raw_daq_inner_dir,
            'decoded_root_inner_dir': self.decoded_root_inner_dir,
            'm3_tracking_inner_dir': self.m3_tracking_inner_dir,
            'decode_path': '/local/home/usernsw/dylan/decode/decode',
            'convert_path': '/local/home/usernsw/dylan/decode/convert_vec_tree_to_array',
            'detector_info_dir': self.detector_info_dir,
            'filtered_root_inner_dir': self.filtered_root_inner_dir,
            'out_type': 'array',  # 'vec', 'array', or 'both'
            'm3_feu_num': self.m3_feu_num,
        }

        self.sedip28_processor_info = {
            'ip': '192.168.10.1',
            'port': 1200,
            'run_dir': f'/mnt/cosmic_data/Run/{self.run_name}',
            'raw_daq_inner_dir': self.raw_daq_inner_dir,
            'm3_tracking_inner_dir': self.m3_tracking_inner_dir,
            'tracking_run_dir': '/local/home/usernsw/dylan/m3_tracking/',
            'tracking_sh_path': '/local/home/usernsw/dylan/m3_tracking/run_tracking_single.sh',
            'm3_feu_num': self.m3_feu_num,
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
            'run_out_dir': self.run_out_dir,
            'hv_monitoring': True,  # True to monitor HV during run, False to not monitor
            'monitor_interval': 2,  # Seconds between HV monitoring
        }

        self.trigger_switch_info = {
            'ip': '192.168.10.101',
            'port': 1100,
        }

        self.trigger_gen_info = {
            'ip': '192.168.10.101',
            'port': 1105,
            'n_triggers': 1000000,  # Number of triggers to send during run
            'trigger_rate': 200,  # Hz  Trigger rate to send during run
            'pulse_freq_ratio': 0.1,  # Ratio of pulse frequency to trigger frequency
        }

        self.sub_runs = [
            # {
            #     'sub_run_name': 'resist_scan_440V',
            #     'run_time': 10,  # Minutes
            #     'hvs': {
            #         0: {
            #             7: 600,
            #             8: 500,
            #             9: 500,
            #             10: 500,
            #             11: 500,
            #         },
            #         3: {
            #             0: 440,
            #             8: 450,
            #             9: 450,
            #             10: 450,
            #             11: 450,
            #         }
            #     }
            # },
            # {
            #     'sub_run_name': 'resist_scan_450V',
            #     'run_time': 10,  # Minutes
            #     'hvs': {
            #         0: {
            #             7: 600,
            #             8: 500,
            #             9: 500,
            #             10: 500,
            #             11: 500,
            #         },
            #         3: {
            #             0: 450,
            #             8: 450,
            #             9: 450,
            #             10: 450,
            #             11: 450,
            #         }
            #     }
            # },
            # {
            #     'sub_run_name': 'resist_scan_460V',
            #     'run_time': 10,  # Minutes
            #     'hvs': {
            #         0: {
            #             7: 600,
            #             8: 500,
            #             9: 500,
            #             10: 500,
            #             11: 500,
            #         },
            #         3: {
            #             0: 460,
            #             8: 450,
            #             9: 450,
            #             10: 450,
            #             11: 450,
            #         }
            #     }
            # },
            # {
            #     'sub_run_name': 'resist_scan_470V',
            #     'run_time': 10,  # Minutes
            #     'hvs': {
            #         0: {
            #             7: 600,
            #             8: 500,
            #             9: 500,
            #             10: 500,
            #             11: 500,
            #         },
            #         3: {
            #             0: 470,
            #             8: 450,
            #             9: 450,
            #             10: 450,
            #             11: 450,
            #         }
            #     }
            # },
            {
                'sub_run_name': 'flushing_run',
                'run_time': 60 * 2,  # Minutes
                'hvs': {
                    0: {
                        7: 600,
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500,
                    },
                    3: {
                        0: 465,
                        8: 450,
                        9: 450,
                        10: 450,
                        11: 450,
                    }
                }
            },
            {
                'sub_run_name': 'overnight_run',
                'run_time': 60 * 24,  # Minutes
                'hvs': {
                    0: {
                        7: 600,
                        8: 500,
                        9: 500,
                        10: 500,
                        11: 500,
                    },
                    3: {
                        0: 465,
                        8: 450,
                        9: 450,
                        10: 450,
                        11: 450,
                    }
                }
            },
        ]

        # Append copies of sub_runs where drifts are decreased by 50V for each sub_run
        # template = self.sub_runs[0]
        # # eic_drift_vs = [50, 100, 150, 200, 300, 400, 500, 600, 700, 800]
        # p2_mesh_vs = [415, 410, 405, 400, 395, 390, 385, 380, 375, 370]
        #
        # # drift_card_channel = {'card': 0, 'channel': 6}
        # mesh_card_channel = {'card': 1, 'channel': 1}
        #
        # # Create sub-runs
        # # for drift_v, mesh_v in zip(eic_drift_vs, p2_mesh_vs):
        # for mesh_v in p2_mesh_vs:
        #     sub_run = copy.deepcopy(template)
        #     # sub_run["sub_run_name"] = f"eic_drift_{drift_v}V_p2_mesh_{mesh_v}V"
        #     sub_run["sub_run_name"] = f"p2_mesh_{mesh_v}V"
        #
        #     # Set the voltages
        #     # sub_run["hvs"][drift_card_channel['card']][drift_card_channel['channel']] = drift_v
        #     sub_run["hvs"][mesh_card_channel['card']][mesh_card_channel['channel']] = mesh_v
        #
        #     self.sub_runs.append(sub_run)


        self.bench_geometry = {
            'p1_z': 227,  # mm  To the top of P1 from the top of PB
            'bottom_level_z': 82,  # mm  From the top of P1 to the bottom level of stand
            'level_z_spacing': 97,  # mm  Spacing between levels on stand
            'board_thickness': 5,  # mm  Thickness of PCB for test boards  Guess!
            'banco_arm_bottom_to_center': (193 - 172) / 2,  # mm from bottom of lower banco arm to center of banco arm
            'banco_arm_separation_z': 172 - 41,  # mm from bottom of lower banco arm to bottom of upper banco arm
            'banco_arm_right_y': 34 + 100,  # mm from center of banco to right edge of banco arm
            'banco_arm_length_y': 230,  # mm from left edge of banco arm to right edge of banco arm
        }

        # self.included_detectors = ['banco_ladder160', 'banco_ladder163', 'banco_ladder157', 'banco_ladder162',
        #                            'urw_strip', 'urw_inter', 'asacusa_strip_1', 'asacusa_strip_2', 'strip_plein_1',
        #                            'strip_strip_1',
        #                            'm3_bot_bot', 'm3_bot_top', 'm3_top_bot', 'm3_top_top', 'scintillator_top']
        self.included_detectors = ['mx17_1',
                                   'm3_bot_bot', 'm3_bot_top', 'm3_top_bot', 'm3_top_top']

        self.detectors = [
            {
                'name': 'mx17_1',
                'det_type': 'mx17',
                'resist_type': 'strip_with_silver_paste',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         1 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 7),
                    'resist': (3, 0),
                },
                'dream_feus': {
                    'x_1': (4, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (4, 2),
                    'x_3': (4, 3),
                    'x_4': (4, 4),
                    'x_5': (4, 5),
                    'x_6': (4, 6),
                    'x_7': (4, 7),
                    'x_8': (4, 8),
                    'y_1': (6, 1),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 2),
                    'y_3': (6, 3),
                    'y_4': (6, 4),
                    'y_5': (6, 5),
                    'y_6': (6, 6),
                    'y_7': (6, 7),
                    'y_8': (6, 8),
                },
            },
            {
                'name': 'banco_ladder157',
                'det_type': 'banco',
                'det_center_coords': {  # Center of detector
                    'x': -13.54 - 40,  # mm  Guess from previous alignment plus shift measurement
                    'y': -34.27 + 30,  # mm
                    'z': 842.20,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 180,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': 'banco',
                'dream_feus': 'banco',
            },
            {
                'name': 'banco_ladder162',
                'det_type': 'banco',
                'det_center_coords': {  # Center of detector
                    'x': -15.41 - 40,  # mm  Guess from previous alignment plus shift measurement
                    'y': -34.27 + 30,  # mm
                    'z': 853.26,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': 'banco',
                'dream_feus': 'banco',
            },
            {
                'name': 'banco_ladder160',
                'det_type': 'banco',
                'det_center_coords': {  # Center of detector
                    'x': -13.21 - 40,  # mm  Guess from previous alignment plus shift measurement
                    'y': -34.39 + 30,  # mm
                    'z': 971.45,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 180,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': 'banco',
                'dream_feus': 'banco',
            },
            {
                'name': 'banco_ladder163',
                'det_type': 'banco',
                'det_center_coords': {  # Center of detector
                    'x': -15.03 - 40,  # mm  Guess from previous alignment plus shift measurement
                    'y': -34.46 + 30,  # mm
                    'z': 982.50,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': 'banco',
                'dream_feus': 'banco',
            },
            {
                'name': 'urw_strip',
                'det_type': 'urw_strip',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         5 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
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
                'det_type': 'urw_inter',
                'det_center_coords': {  # Center of detector
                    # 'x': 0,  # mm
                    # 'y': 0,  # mm
                    # 'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                    #      4 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                    'x': 10,  # mm
                    'y': 40,  # mm
                    'z': 712.7,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
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
                'det_type': 'asacusa_strip',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         3 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
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
                'det_type': 'asacusa_strip',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         2 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
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
                'name': 'strip_plein_1',
                'det_type': 'strip_plein',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                         1 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 6),
                    'resist_2': (3, 7),
                },
                'dream_feus': {
                    'x_1': (3, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (3, 6),
                    'y_1': (3, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (3, 8),
                },
            },
            # {
            #     'name': 'inter_grid_1',
            #     'det_type': 'inter_grid',
            #     'det_center_coords': {  # Center of detector
            #         'x': 0,  # mm
            #         'y': 0,  # mm
            #         'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
            #              1 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
            #     },
            #     'det_orientation': {
            #         'x': 0,  # deg  Rotation about x axis
            #         'y': 0,  # deg  Rotation about y axis
            #         'z': 0,  # deg  Rotation about z axis
            #     },
            #     'hv_channels': {
            #         'drift': (0, 6),
            #         # 'resist_1': (3, 7),
            #         'resist_2': (2, 0)
            #     },
            #     'dream_feus': {
            #         'x_1': (3, 5),  # Runs along x direction, indicates y hit location
            #         'x_2': (3, 6),
            #         'y_1': (3, 7),  # Runs along y direction, indicates x hit location
            #         'y_2': (3, 8),
            #     },
            # },
            # {
            #     'name': 'strip_grid_1',
            #     'det_type': 'strip_grid',
            #     'det_center_coords': {  # Center of detector
            #         'x': 0,  # mm
            #         'y': 0,  # mm
            #         'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
            #              0 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
            #     },
            #     'det_orientation': {
            #         'x': 0,  # deg  Rotation about x axis
            #         'y': 0,  # deg  Rotation about y axis
            #         'z': 0,  # deg  Rotation about z axis
            #     },
            #     'hv_channels': {
            #         'drift': (0, 7),
            #         'resist_2': (3, 7)
            #     },
            #     'dream_feus': {
            #         'x_1': (3, 1),  # Runs along x direction, indicates y hit location
            #         'x_2': (3, 2),
            #         'y_1': (3, 3),  # Runs along y direction, indicates x hit location
            #         'y_2': (3, 4),
            #     },
            # },
            {
                'name': 'strip_strip_1',
                'det_type': 'strip_strip',
                'det_center_coords': {  # Center of detector
                    'x': 9.2,  # mm
                    'y': 38.4,  # mm
                    # 'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                    #      5 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                    'z': 712.7,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 6),
                    'resist_2': (3, 7),
                },
                'dream_feus': {
                    'x_1': (6, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 2),
                    'y_1': (6, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 4),
                },
            },
            {
                'name': 'inter_plein_1',
                'det_type': 'inter_plein',
                'det_center_coords': {  # Center of detector
                    'x': 9.2,  # mm
                    'y': 38.4,  # mm
                    # 'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                    #      5 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                    'z': 712.7,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 6),
                    'resist_2': (3, 7),
                },
                'dream_feus': {
                    'x_1': (6, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 2),
                    'y_1': (6, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 4),
                },
            },
            {
                'name': 'p2_3',
                'det_type': 'p2',
                'det_center_coords': {  # Center of detector
                    # 'x': 0,  # mm
                    # 'y': 0,  # mm
                    # 'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                    #      4 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                    'x': 10,  # mm
                    'y': 40,  # mm
                    'z': 712.7,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 6),
                    'mesh_1': (0, 7)
                },
                'dream_feus': {
                    'x_1': (6, 1),
                    'x_2': (6, 2),
                },
            },
            {
                'name': 'rd5_plein_1',
                'det_type': 'rd5_plein',
                'det_center_coords': {  # Center of detector
                    'x': 24,  # mm
                    'y': 75.6,  # mm
                    'z': 720.8,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 6),
                    'resist_1': (3, 3),
                    'resist_2': (3, 4)
                },
                'dream_feus': {
                    'x_1': (6, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 2),
                    'y_1': (6, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 4),
                },
            },
            {
                'name': 'rd5_strip_1',
                'det_type': 'rd5_strip',
                'det_center_coords': {  # Center of detector
                    'x': 24,  # mm
                    'y': 75.6,  # mm
                    'z': 720.8,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 6),
                    'resist_1': (3, 3),
                    'resist_2': (3, 4)
                },
                'dream_feus': {
                    'x_1': (6, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 2),
                    'y_1': (6, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 4),
                },
            },
            {
                'name': 'rd5_plein_2',
                'det_type': 'rd5_plein',
                'det_center_coords': {  # Center of detector
                    'x': 24,  # mm
                    'y': 75.6,  # mm
                    'z': 720.8,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 6),
                    'resist_1': (3, 3),
                    'resist_2': (3, 4)
                },
                'dream_feus': {
                    'x_1': (6, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 2),
                    'y_1': (6, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 4),
                },
            },
            {
                'name': 'rd5_plein_3',
                'det_type': 'rd5_plein',
                'det_center_coords': {  # Center of detector
                    'x': 24,  # mm
                    'y': 75.6,  # mm
                    'z': 720.8,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 6),
                    'resist_1': (3, 3),
                    'resist_2': (3, 4)
                },
                'dream_feus': {
                    'x_1': (6, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 2),
                    'y_1': (6, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 4),
                },
            },
            {
                'name': 'rd5_strip_2',
                'det_type': 'rd5_strip',
                'det_center_coords': {  # Center of detector
                    'x': -34.16,  # mm
                    'y': 33.09,  # mm
                    'z': 708.9,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 6),
                    'resist_1': (3, 3),
                    'resist_2': (3, 4)
                },
                'dream_feus': {
                    'x_1': (6, 0),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 1),
                    'y_1': (6, 2),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 3),
                },
            },
            {
                'name': 'rd5_plein_vfp_1',
                'det_type': 'rd5_plein',
                'det_center_coords': {  # Center of detector
                    'x': 24,  # mm
                    'y': 75.6,  # mm
                    'z': 720.8,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 0),
                    # 'resist_1': (2, 0),
                    'resist_2': (2, 1)
                },
                'dream_feus': {
                    'x_1': (1, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (1, 2),
                    'y_1': (1, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (1, 4),
                },
            },
            {
                'name': 'rd5_grid_vfp_1',
                'det_type': 'rd5_grid_vfp',
                'det_center_coords': {  # Center of detector
                    'x': 24,  # mm
                    'y': 75.6,  # mm
                    'z': 720.8,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 0),
                    'resist_1': (2, 0),
                    'resist_2': (2, 1)
                },
                'dream_feus': {
                    'x_1': (6, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 2),
                    'y_1': (6, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 4),
                },
            },
            {
                'name': 'rd5_plein_esl_1',
                'det_type': 'rd5_plein_esl',
                'det_center_coords': {  # Center of detector
                    'x': 24,  # mm
                    'y': 75.6,  # mm
                    'z': 720.8,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 0),
                    'resist_1': (2, 0),
                    'resist_2': (2, 1)
                },
                'dream_feus': {
                    'x_1': (6, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 2),
                    'y_1': (6, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 4),
                },
            },
            {
                'name': 'rd5_strip_esl_1',
                'det_type': 'rd5_strip_esl',
                'det_center_coords': {  # Center of detector
                    'x': 24,  # mm
                    'y': 75.6,  # mm
                    'z': 720.8,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (0, 6),
                    'resist_1': (3, 3),
                    'resist_2': (3, 4)
                },
                'dream_feus': {
                    'x_1': (6, 0),  # Runs along x direction, indicates y hit location
                    'x_2': (6, 1),
                    'y_1': (6, 2),  # Runs along y direction, indicates x hit location
                    'y_2': (6, 3),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            },
            {
                'name': 'p2_1',
                'det_type': 'p2',
                'det_center_coords': {  # Center of detector
                    'x': 9.2,  # mm
                    'y': 38.4,  # mm
                    # 'z': self.bench_geometry['p1_z'] + self.bench_geometry['bottom_level_z'] +
                    #      5 * self.bench_geometry['level_z_spacing'] + self.bench_geometry['board_thickness'],  # mm
                    'z': 100.0,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (1, 0),
                    'mesh': (1, 1),
                },
                'dream_feus': {
                    '0': (7, 0),
                    '1': (7, 1),
                    '2': (3, 0),
                    '3': (3, 1),
                    '4': (3, 2),
                    '5': (3, 3),
                    '6': (3, 4),
                    '7': (3, 5),
                    '8': (3, 6),
                    '9': (3, 7),
                    '10': (4, 0),
                    '11': (4, 1),
                    '12': (4, 2),
                    '13': (4, 3),
                    '14': (4, 4),
                    '15': (4, 5),
                    '16': (4, 6),
                    '17': (4, 7),
                    '18': (7, 2),
                    '19': (7, 3),
                },
            },
            {
                'name': 'm3_bot_bot',
                'det_type': 'm3',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 24,  # mm  28 from geometry diagram, 24 from m3 config json
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
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
                'det_type': 'm3',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 144,  # mm  145 from geometry diagram, 144 from m3 config json
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
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
                'det_type': 'm3',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1185,  # mm  1163 + 28 from geometry diagram, 1185 from m3 config json
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
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
                'det_type': 'm3',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1302,  # mm  1163 + 145 from geometry diagram, 1302 from m3 config json
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
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
            {
                'name': 'scintillator_top',
                'det_type': 'scintillator',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1412,  # mm  1163 + 145 + 110 from geometry diagram
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'dream_feus': {
                    'xy': (3, 4),
                },
                'dream_feu_channels': {
                    'xy': (3, 4, 21),
                }
            },
            {
                'name': 'scintillator_bottom',
                'det_type': 'scintillator',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 24 - 100,  # mm  24 - 100 from geometry diagram
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'dream_feus': {
                    'xy': (3, 4),
                },
                'dream_feu_channels': {
                    'xy': (3, 4, 20),
                }
            },
        ]

        if not self.write_all_dectors_to_json:
            self.detectors = [det for det in self.detectors if det['name'] in self.included_detectors]

    def write_to_file(self, file_path):
        with open(file_path, 'w') as file:
            json.dump(self.__dict__, file, indent=4)

    def load_from_file(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            self.__dict__.clear()
            self.__dict__.update(data)


if __name__ == '__main__':
    out_dir = '/local/home/dn277127/Bureau/beam_test_25/'
    # out_dir = 'C:/Users/Dylan/Desktop/banco_test3/'
    config = Config()
    config.write_to_file(f'{out_dir}run_config_test.json')
    print('donzo')

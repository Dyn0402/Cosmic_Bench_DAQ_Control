#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 9:37 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/run_config_template.py

@author: Dylan Neff, Dylan
"""

import sys
import json
import copy


class Config:
    def __init__(self, config_path=None):
        self.run_name = 'run_199'
        self.base_out_dir = '/mnt/data/beam_sps_25/'
        self.data_out_dir = f'{self.base_out_dir}Run/'
        self.run_out_dir = f'{self.data_out_dir}{self.run_name}/'
        self.raw_daq_inner_dir = 'raw_daq_data'
        self.decoded_root_inner_dir = 'decoded_root'
        self.filtered_root_inner_dir = 'filtered_root'
        self.m3_tracking_inner_dir = 'm3_tracking_root'
        self.detector_info_dir = f'{self.base_out_dir}config/detectors/'
        self.m3_feu_num = None
        self.power_off_hv_at_end = False  # True to power off HV at end of run
        self.filtering_by_m3 = False  # True to filter by m3 tracking, False to do no filtering
        self.process_on_fly = False  # True to process data on fly, False to process after run
        self.save_fdfs = True  # True to save FDF files, False to delete after decoding
        self.start_time = None
        self.write_all_dectors_to_json = True  # Only when making run config json template. Maybe do always?
        self.generate_external_triggers = False  # If true, use raspberry pi to generate external triggers for DAQ
        self.watch_for_desync = True  # If true, run desync watcher during run
        self.gas = 'Ar/CF4/CO2 40/45/15'  # Gas type for run
        self.beam_type = 'muons'

        self.weiner_ps_info = {  # If this exists, check for Weiner LV before applying any HV
            'ip': '192.168.10.222',
            'channels': {  # Check only the channels which exist here
                'U0': {
                    'expected_voltage': 4.5,  # V
                    'expected_current': 30,  # A
                    'voltage_tolerance': 0.4,  # V
                    'current_tolerance': 5,  # A
                },
            }
        }

        self.dream_daq_info = {
            'ip': '192.168.10.8',
            'port': 1101,
            'daq_config_template_path': f'{self.base_out_dir}dream_run/config/TbSPS25.cfg',
            # 'run_directory': f'/mnt/data/beam_sps_25/dream_run/{self.run_name}/',
            'run_directory': f'/local/home/banco/beam_test_2025/Run/{self.run_name}/',
            'data_out_dir': f'{self.base_out_dir}Run/{self.run_name}',
            'raw_daq_inner_dir': self.raw_daq_inner_dir,
            'n_samples_per_waveform': 24,  # Number of samples per waveform to configure in DAQ
            'go_timeout': 5 * 60,  # Seconds to wait for 'Go' response from RunCtrl before assuming failure
            'max_run_time_addition': 60 * 5,  # Seconds to add to requested run time before killing run
            'copy_on_fly': True,  # True to copy raw data to out dir during run, False to copy after run
            'batch_mode': True,  # Run Dream RunCtrl in batch mode. Not implemented for cosmic bench CPU.
            'zero_suppress': True,  # True to run in zero suppression mode, False to run in full readout mode
            'pedestals_dir': f'{self.base_out_dir}pedestals_noise/',  # None to ignore, else top directory for pedestal runs
            'pedestals': 'latest',  # 'latest' for most recent, otherwise specify directory name, eg "pedestals_10-22-25_13-43-34"
            'latency': 33,  # Latency setting for DAQ in clock cycles
            # 'latency': 22,  # Latency setting for DAQ in clock cycles
            'sample_period': 40,  # ns, sampling period
            # 'samples_beyond_threshold': 1,  # Number of samples to read out beyond threshold crossing
            'samples_beyond_threshold': 4,  # Number of samples to read out beyond threshold crossing
        }

        self.banco_info = {
            'ip': '128.141.41.199',
            'port': 1100,
            'daq_run_command': 'cd /home/banco/SPS_Test_Beam_25/framework/bin && ./test_multi_noiseocc_ext',
            'data_temp_dir': '/home/banco/SPS_Test_Beam_25/data',
            'data_out_dir': f'/mnt/data/beam_sps_25/Run/{self.run_name}',
            'data_inner_dir': 'banco_data'
        }

        self.dedip196_processor_info = {
            'ip': '192.168.10.8',
            'port': 1200,
            'run_dir': f'{self.base_out_dir}Run/{self.run_name}',
            'raw_daq_inner_dir': self.raw_daq_inner_dir,
            'decoded_root_inner_dir': self.decoded_root_inner_dir,
            'm3_tracking_inner_dir': self.m3_tracking_inner_dir,
            'decode_path': '/local/home/banco/dylan/decode/decode',
            'convert_path': '/local/home/banco/dylan/decode/convert_vec_tree_to_array',
            'detector_info_dir': self.detector_info_dir,
            'filtered_root_inner_dir': self.filtered_root_inner_dir,
            'out_type': 'both',  # 'vec', 'array', or 'both'
            'm3_feu_num': self.m3_feu_num,
            'on-the-fly_timeout': 2  # hours or None If running on-the-fly, time out and die after this time.
        }

        self.hv_control_info = {
            'ip': '192.168.10.8',
            'port': 1100,
        }

        self.hv_info = {
            'ip': '192.168.10.199',
            'username': 'admin',
            'password': 'admin',
            'n_cards': 6,
            'n_channels_per_card': 12,
            'run_out_dir': self.run_out_dir,
            'hv_monitoring': True,  # True to monitor HV during run, False to not monitor
            'monitor_interval': 1,  # Seconds between HV monitoring
        }

        self.trigger_switch_info = {
            'ip': '192.168.10.101',
            'port': 1100,
        }

        self.trigger_gen_info = {
            'ip': '192.168.10.101',
            'port': 1105,
            'n_triggers': 6000000,  # Number of triggers to send during run
            'trigger_rate': 200,  # Hz  Trigger rate to send during run
            'pulse_freq_ratio': 0.1,  # Ratio of pulse frequency to trigger frequency
        }

        self.desync_watcher_info = {
            'ip': '192.168.10.8',
            'port': 1105,
            'run_out_dir': f'{self.base_out_dir}Run/{self.run_name}',
            'check_interval': 0.2,  # Seconds between checking for desync
            'min_points': 10,  # Minimum number of desynced points to flag desync
            'min_duration': 12,  # Seconds minimum duration of desync to flag desync
        }

        hv_adjust = 0
        self.sub_runs = [
            {
                # 'sub_run_name': f'rotation_45_banco_scan_0',
                'sub_run_name': f'rotation_30_drift_resist_scan_0',
                # 'sub_run_name': f'rotation_0_resist_scan_0',
                'run_time': 4,  # Minutes
                'hvs': {
                    '2': {
                        '0': 640 + hv_adjust,
                        # '1': 785 - 55 + hv_adjust,
                        '1': 750 + hv_adjust,
                        '2': 810 + hv_adjust,
                        '3': 810 + hv_adjust,
                        '4': 475 + hv_adjust,
                        # '5': 790 - 140 + hv_adjust,
                        '5': 750 + hv_adjust,
                        '6': 990 + hv_adjust,
                        '7': 830 + hv_adjust,
                        '8': 830 + hv_adjust,
                        '9': 940 + hv_adjust,
                        '10': 940 + hv_adjust,
                    },
                    '5': {
                        '0': 500,
                        '1': 500,
                        # '2': 700,
                        # '3': 500,
                        # '4': 500,
                        # '5': 500,
                        # '6': 640,
                        # '7': 440,
                        # '8': 750,
                        # '9': 500,
                        # '10': 750,
                        # '11': 500,
                    },
                    # '12': {
                    #     '0': 1050 + hv_adjust
                    # }
                }
            },
        ]


        # Append copies of sub_runs where drifts are decreased by 50V for each sub_run
        # template = self.sub_runs[0]
        # resist_diffs = [-10, -20, -30, -40, -50, -60, -70, -80, -90, -100]
        # for resist_diff in resist_diffs:
        #     sub_run = copy.deepcopy(template)
        #     sub_run['sub_run_name'] = f'rotation_-30_resist_scan_{resist_diff}'
        #
        #     card = '2'
        #     channels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']  # Resist channels
        #     for channel in sub_run['hvs'][card]:
        #         if channel in channels:
        #             sub_run['hvs'][card][channel] = sub_run['hvs'][card][channel] + resist_diff
        #
        #     card = '12'
        #     channels = ['0']  # Resist channels
        #     for channel in sub_run['hvs'][card]:
        #         if channel in channels:
        #             sub_run['hvs'][card][channel] = sub_run['hvs'][card][channel] + resist_diff
        #
        #     # card = '5'
        #     # channels = ['2', '3', '6', '7', '8', '9', '10', '11']  # Resist channels
        #     # for channel in sub_run['hvs'][card]:
        #     #     if channel in channels:
        #     #         sub_run['hvs'][card][channel] = sub_run['hvs'][card][channel] + resist_diff
        #     self.sub_runs.append(sub_run)

        # # Remove the first two sub_runs to keep only the modified ones
        # self.sub_runs = self.sub_runs[1:]

        # For Drift Scans
        template = self.sub_runs[0]
        # drift_diffs_eic = [-400, -375, -350, -325, -300, -275, -250, -225, -200, -175, -150, -125,
        #                    -100, -75, -50, -25]

        drift_diffs_eic = [-450, -400, -375, -300, -225, -150, -75, -25, -100, -175, -250, -325, -350, -275, -225, -200,
                           -125, -50]
        # drift_diffs_eic = [-50, -100, -150, -200, -250, -300, -350, -400, -450]
        # drift_diffs_p2 = [-20, -40, -60, -80, -100, -120, -140, -160, -180]
        # for drift_diff_eic, drift_diff_p2 in zip(drift_diffs_eic, drift_diffs_p2):
        for drift_diff_eic in drift_diffs_eic:
            sub_run = copy.deepcopy(template)
            # Get sub_run name and just strip off everything after last underscore
            sub_run['sub_run_name'] = f'rotation_30_drift_scan_{drift_diff_eic}'

            card = '5'
            # channels = ['0', '1', '4', '5']  # Drift channels
            channels = ['0', '1']  # Drift channels
            for channel in sub_run['hvs'][card]:
                if channel in channels:
                    drift_diff = drift_diff_eic
                    # if channels in ['0', '1']:
                    #     drift_diff = int(drift_diff_eic * 45 / 25)
                    sub_run['hvs'][card][channel] = sub_run['hvs'][card][channel] + drift_diff

            # card = '5'
            # channels = ['6', '8', '10']
            # for channel in sub_run['hvs'][card]:
            #     if channel in channels:
            #         sub_run['hvs'][card][channel] = sub_run['hvs'][card][channel] + drift_diff_p2

            self.sub_runs.append(sub_run)

        # Append copies of sub_runs where drifts are decreased by 50V for each sub_run
        # For Resist Scans
        template = self.sub_runs[0]
        resist_diffs = [-100, -95, -90, -85, -80, -75, -70, -65, -60, -55, -50, -45, -40, -35, -30, -25, -20, -15,
                        -10, -5, -105]
        # resist_diffs = [-5, -10, -15, -20, -25, -30, -35, -40, -45, -50, -55, -60, -65, -70, -75, -80, -85, -90,
        #                 -95, -100, -105]
        # resist_diffs = [-5, -10, -15, -20, -25, -30, -35, -40, -45, -50, -60, -70, -80, -90, -100]
        for resist_diff in resist_diffs:
            sub_run = copy.deepcopy(template)
            sub_run['sub_run_name'] = f'rotation_30_resist_scan_{resist_diff}'

            card = '2'
            channels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']  # Resist channels
            # channels = ['0', '1', '2', '3', '4', '5', '6', '7', '8']  # Resist channels
            # channels = ['3']  # Resist channels
            for channel in sub_run['hvs'][card]:
                if channel in channels:
                    sub_run['hvs'][card][channel] = sub_run['hvs'][card][channel] + resist_diff

            # card = '12'
            # channels = ['0']  # Resist channels
            # for channel in sub_run['hvs'][card]:
            #     if channel in channels:
            #         sub_run['hvs'][card][channel] = sub_run['hvs'][card][channel] + resist_diff

            # card = '5'
            # channels = ['2', '3', '6', '7', '8', '9', '10', '11']  # Drift + resist channels
            # for channel in sub_run['hvs'][card]:
            #     if channel in channels:
            #         sub_run['hvs'][card][channel] = sub_run['hvs'][card][channel] + resist_diff
            self.sub_runs.append(sub_run)

        # Append to start of sub_runs a duplicate of the last sub_run with 0 minute run time
        template = copy.deepcopy(self.sub_runs[0])
        template['sub_run_name'] = 'long_wait_for_beam'
        template['run_time'] = 60 * 8  # Minutes
        self.sub_runs.insert(0, template)

        # Append copies of sub_runs with same voltages but different run names
        # Typically for banco scans.
        # template = self.sub_runs[0]
        # for i in range(1, 12):
        #     sub_run = copy.deepcopy(template)
        #     # Get sub_run name and just strip off everything after last underscore
        #     sub_run_name_base = sub_run['sub_run_name'].rsplit('_', 1)[0]
        #     sub_run['sub_run_name'] = f'{sub_run_name_base}_{i}'
        #     # sub_run['run_time'] = 10  # Minutes
        #     self.sub_runs.append(sub_run)

        self.bench_geometry = {
            'board_thickness': 5,  # mm  Thickness of PCB for test boards  Guess!
            'banco_arm_bottom_to_center': (193 - 172) / 2,  # mm from bottom of lower banco arm to center of banco arm
            'banco_ladder_separation_z': 11.0,  # mm Space between ladders on same arm.
            'banco_arm_separation_z': 172 - 41,  # mm from bottom of lower banco arm to bottom of upper banco arm
            'banco_arm_right_y': 34 + 100,  # mm from center of banco to right edge of banco arm
            'banco_arm_length_y': 230,  # mm from left edge of banco arm to right edge of banco arm
            'banco_moveable_y_position': 50.0,  # mm  Offset from moving table. Positive moves banco up.
        }

        self.included_detectors = ['banco_ladder160', 'banco_ladder163', 'banco_ladder157', 'banco_ladder162',
                                   'urw_inter', 'rd5_plein_saral_2', 'rd5_strip_esl_1', 'rd5_grid_saral_1',
                                   'rd5_plein_saral_1', 'urw_strip', 'rd5_strip_saral_1', 'rd5_strip_vfp_1']

        self.detectors = [
            {
                'name': 'banco_ladder157',
                'det_type': 'banco',
                'det_center_coords': {  # Center of detector
                    'x': -13.54,  # mm  Guess from previous alignment plus shift measurement
                    'y': self.bench_geometry['banco_moveable_y_position'],  # mm
                    'z': 842.20 - 842.20 + 500,  # mm
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
                    'x': -15.41,  # mm  Guess from previous alignment plus shift measurement
                    'y': self.bench_geometry['banco_moveable_y_position'],  # mm
                    # 'z': 853.26 - 842.20 + 500,  # mm
                    'z': 500 + self.bench_geometry['banco_ladder_separation_z'],  # mm
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
                    'x': -13.21,  # mm  Guess from previous alignment plus shift measurement
                    'y': self.bench_geometry['banco_moveable_y_position'],  # mm
                    'z': 600,  # mm
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
                    'x': -15.03,  # mm  Guess from previous alignment plus shift measurement
                    'y': self.bench_geometry['banco_moveable_y_position'],  # mm
                    'z': 600 + self.bench_geometry['banco_ladder_separation_z'],  # mm
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
                    'z': 900,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 1),
                    'resist_2': (2, 5)
                },
                'dream_feus': {
                    'x_1': (3, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (3, 6),
                    'y_1': (3, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (3, 8),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': True,
                    'y_2': True,
                }
            },

            {
                'name': 'urw_inter',
                'det_type': 'urw_inter',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 100,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 0),
                    'resist_1': (2, 0)
                },
                'dream_feus': {
                    'x_1': (1, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (1, 2),
                    'y_1': (1, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (1, 4),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            },

            {
                'name': 'asacusa_strip_2',
                'det_type': 'asacusa_strip',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 400,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 0),
                    'resist_2': (2, 3)
                },
                'dream_feus': {
                    'x_1': (2, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (2, 6),
                    'y_1': (2, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (2, 8),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            },

            {
                'name': 'rd5_plein_saral_1',
                'det_type': 'rd5_plein_saral',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 800,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 1),
                    'resist_1': (12, 0),
                },
                'dream_feus': {
                    'x_1': (3, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (3, 2),
                    'y_1': (3, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (3, 4),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            },

            {
                'name': 'rd5_plein_saral_2',
                'det_type': 'rd5_plein_saral',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 200,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 0),
                    'resist_2': (2, 1)
                },
                'dream_feus': {
                    'x_1': (1, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (1, 6),
                    'y_1': (1, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (1, 8),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                },
                'kel_connectors': '100 cm kel cable on y_2 (Feu 1 channel 8). With 2 1.5m bluejean cables.'
            },

            {
                'name': 'rd5_strip_saral_1',
                'det_type': 'rd5_strip_saral',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1000,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 1),
                    'resist_1': (2, 7),
                    'resist_2': (2, 8)
                },
                'dream_feus': {
                    'x_1': (4, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (4, 2),
                    'y_1': (4, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (4, 4),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            },

            {
                'name': 'rd5_grid_saral_1',
                'det_type': 'rd5_grid_saral',
                'drift_gap': 1,  # mm Drift gap for grid detector, default is 3 mm
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 400,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 0),
                    # 'resist_1': (2, 4),
                    'resist_2': (2, 6)
                },
                'dream_feus': {
                    'x_1': (2, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (2, 2),
                    'y_1': (2, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (2, 4),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            },

            {
                'name': 'rd5_plein_vfp_1',
                'det_type': 'rd5_plein_vfp',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 300,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 0),
                    'resist_2': (2, 2)
                },
                'dream_feus': {
                    'x_1': (2, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (2, 2),
                    'y_1': (2, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (2, 4),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            },

            {
                'name': 'rd5_strip_vfp_1',
                'det_type': 'rd5_strip_vfp',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1100,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 1),
                    'resist_1': (2, 9),
                    'resist_2': (2, 10)
                },
                'dream_feus': {
                    'x_1': (4, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (4, 6),
                    'y_1': (4, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (4, 8),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': True,
                    'y_2': True,
                }
            },

            {
                'name': 'rd5_grid_vfp_1',
                'det_type': 'rd5_grid_vfp',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 800,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 0),
                    'resist_1': (2, 9),
                    'resist_2': (2, 10)
                },
                'dream_feus': {
                    'x_1': (3, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (3, 2),
                    'y_1': (3, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (3, 4),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            },

            {
                'name': 'rd5_plein_esl_1',
                'det_type': 'rd5_plein_esl',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 100,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 4),
                    'resist_1': (2, 2),
                    'resist_2': (2, 4)
                },
                'dream_feus': {
                    'x_1': (2, 1),  # Runs along x direction, indicates y hit location
                    'x_2': (2, 2),
                    'y_1': (2, 3),  # Runs along y direction, indicates x hit location
                    'y_2': (2, 4),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            },

            {
                'name': 'rd5_strip_esl_1',
                'det_type': 'rd5_strip_esl',
                'drift_gap': 3.0,  # mm. Default is 3 mm
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 300,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': -90,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 0),
                    'resist_1': (2, 2),
                    'resist_2': (2, 3)
                },
                'dream_feus': {
                    'x_1': (2, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (2, 6),
                    'y_1': (2, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (2, 8),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': False,
                    'y_2': False,
                }
            },

            {
                'name': 'rd5_grid_esl_1',
                'det_type': 'rd5_grid_esl',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1100,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 30,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 1),
                    'resist_1': (2, 4),
                    'resist_2': (2, 6),
                },
                'dream_feus': {
                    'x_1': (4, 5),  # Runs along x direction, indicates y hit location
                    'x_2': (4, 6),
                    'y_1': (4, 7),  # Runs along y direction, indicates x hit location
                    'y_2': (4, 8),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                    'y_1': True,
                    'y_2': True,
                }
            },

            {
                'name': 'p2_small_1',
                'det_type': 'p2',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1490,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 8),
                    'mesh': (5, 9)
                },
                'dream_feus': {
                    'x_1': (5, 5),
                    'x_2': (5, 6),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': False,
                    'x_2': False,
                }
            },

            {
                'name': 'p2_small_2',
                'det_type': 'p2',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1620,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 10),
                    'mesh_1': (5, 11)
                },
                'dream_feus': {
                    # 'x_1': (5, 7),
                    # 'x_2': (5, 8),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                }
            },

            {
                'name': 'p2_small_3',
                'det_type': 'p2',
                'det_center_coords': {  # Center of detector
                    'x': 0,  # mm
                    'y': 0,  # mm
                    'z': 1560,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 2),
                    'mesh_1': (5, 3)
                },
                'dream_feus': {
                    'x_1': (5, 7),
                    'x_2': (5, 8),
                },
                'dream_feu_inversion': {  # If True, connector is inverted --> 1, 0, 3, 2 ...
                    'x_1': True,
                    'x_2': True,
                }
            },

            {
                'name': 'p2_large_1',
                'det_type': 'p2',
                'det_center_coords': {  # Center of detector
                    'x': 0.0,  # mm
                    'y': 0.0,  # mm
                    'z': 1290,  # mm
                },
                'det_orientation': {
                    'x': 0,  # deg  Rotation about x axis
                    'y': 0,  # deg  Rotation about y axis
                    'z': 0,  # deg  Rotation about z axis
                },
                'hv_channels': {
                    'drift': (5, 6),
                    'mesh': (5, 7),
                },
                'dream_feus': {
                    '9': (5, 1),
                    '10': (5, 2),
                    '11': (5, 3),
                    '12': (5, 4),
                },
            },

        ]

        if not self.write_all_dectors_to_json:
            self.detectors = [det for det in self.detectors if det['name'] in self.included_detectors]

        if config_path:  # Clear everything and load from file
            self.load_from_file(config_path)

    def write_to_file(self, file_path):
        with open(file_path, 'w') as file:
            json.dump(self.__dict__, file, indent=4)

    def load_from_file(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            self.__dict__.clear()
            self.__dict__.update(data)


if __name__ == '__main__':
    out_run_dir = 'config/json_run_configs/'

    config_name = 'run_config_beam.json'

    config = Config()

    config.write_to_file(f'{out_run_dir}{config_name}')

    print('donzo')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 25 4:04 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/main.py

@author: Dylan Neff, Dylan
"""

import os
from time import sleep
from caen_hv_py.CAENHVController import CAENHVController


def main():
    run_name = 'test_run'
    input_fdf_dir = '/mnt/nas_clas12/DATA/CosmicBench/2024/W05/'
    input_dir = f'{input_fdf_dir}{run_name}/'
    create_dir_if_not_exist(input_dir)
    output_dir = f'/local/home/usernsw/dylan/{run_name}/'
    create_dir_if_not_exist(output_dir)

    output_root_dir = f'{output_dir}output_root/'
    tracking_run_dir = f'{output_dir}tracking/'
    signal_run_dir = f'{output_dir}signal/'
    tracking_sh_file = f'{output_dir}tracking/run_tracking_single.sh'
    signal_sh_file = f'{output_dir}signal/run_data_reader_single.sh'

    hv_info = {
        'hv_lib_path': 'hv_c_lib/libhv_c.so',
        'hv_ip_address': '192.168.10.81',
        'hv_username': 'admin',
        'hv_password': 'admin',
    }

    sub_runs = [
        {
            'sub_run_name': 'sub_run_0',
            'run_time': 10,
            'hvs': {
                0: {
                    0: 50,
                    1: 100,
                    2: 150
                },
                1: {
                    0: 200,
                    1: 250
                }
            }
        },
        {
            'sub_run_name': 'sub_run_1',
            'run_time': 20,
            'hvs': {
                0: {
                    0: 100,
                    1: 150,
                    2: 200
                },
                1: {
                    0: 250,
                    1: 300
                }
            }
        }
    ]

    for sub_run in sub_runs:
        set_hvs(sub_run['hvs'], hv_info)
        # Start DAQ

    print('donzo')


def create_dir_if_not_exist(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)


def set_hvs(hv_info, hvs):
    ip_address, username, password = hv_info['hv_ip_address'], hv_info['hv_username'], hv_info['hv_password']
    with CAENHVController(ip_address, username, password) as caen_hv:
        for slot_channel, v0 in hvs.items():
            slot, channel = slot_channel.split('_')
            slot, channel = int(slot), int(channel)
            caen_hv.set_ch_v0(slot, channel, v0)
            power = caen_hv.get_ch_power(slot, channel)
            if not power:
                caen_hv.set_ch_pw(slot, channel, 1)

        all_ramped = False
        while not all_ramped:
            all_ramped = True
            for slot_channel, v0 in hvs.items():
                slot, channel = slot_channel.split('_')
                slot, channel = int(slot), int(channel)
                vmon = caen_hv.get_ch_vmon(slot, channel)
                if abs(vmon - v0) > 1.5:  # Make sure within 1.5 V of set value
                    all_ramped = False
                    break
            sleep(10)  # Make sure not to wait too long, after 15s crate times out


if __name__ == '__main__':
    main()

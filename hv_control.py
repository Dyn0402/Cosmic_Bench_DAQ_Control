#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 8:39 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/hv_control.py

@author: Dylan Neff, Dylan
"""

import time

from Server import Server
from caen_hv_py.CAENHVController import CAENHVController

from run_config import Config


def main():
    # config = Config()
    port = 1100
    with Server(port=port) as server:
        server.receive()
        server.send('HV control connected')
        hv_info = server.receive_json()

        res = server.receive()
        while 'Finished' not in res:
            if 'Start' in res:
                server.send('HV ready to start')
                sub_run = server.receive_json()
                set_hvs(hv_info, sub_run['hvs'])
                server.send(f'HV Set {sub_run["sub_run_name"]}')
                # sub_run_name = res.split()[1]
                # for sub_run in config.sub_runs:
                #     if sub_run['sub_run_name'] == sub_run_name:
                #         set_hvs(config.hv_info, sub_run['hvs'])
                #         server.send(f'HV Set {sub_run_name}')
                #         break
            else:
                server.send('Unknown Command')
            res = server.receive()
    # power_off_hvs(config.hv_info)
    power_off_hvs(hv_info)
    print('donzo')


def set_hvs(hv_info, hvs):
    ip_address, username, password = hv_info['hv_ip_address'], hv_info['hv_username'], hv_info['hv_password']
    with CAENHVController(ip_address, username, password) as caen_hv:
        for slot, channel_v0s in hvs.items():
            for channel, v0 in channel_v0s.items():
                caen_hv.set_ch_v0(slot, channel, v0)
                power = caen_hv.get_ch_power(slot, channel)
                if not power:
                    caen_hv.set_ch_pw(slot, channel, 1)

        all_ramped = False
        while not all_ramped:
            all_ramped = True
            for slot, channel_v0s in hvs.items():
                for channel, v0 in channel_v0s.items():
                    vmon = caen_hv.get_ch_vmon(slot, channel)
                    if abs(vmon - v0) > 1.5:  # Make sure within 1.5 V of set value
                        all_ramped = False
                        break
            print('Waiting for HV to ramp...')
            time.sleep(10)  # Make sure not to wait too long, after 15s crate times out


def power_off_hvs(hv_info):
    ip_address, username, password = hv_info['hv_ip_address'], hv_info['hv_username'], hv_info['hv_password']
    print('Powering off HV...')
    with CAENHVController(ip_address, username, password) as caen_hv:
        for slot in range(hv_info['n_cards']):
            for channel in range(hv_info['n_channels_per_card']):
                power = caen_hv.get_ch_power(slot, channel)
                if power:
                    caen_hv.set_ch_pw(slot, channel, 0)
    print('HV Powered Off')


if __name__ == '__main__':
    main()

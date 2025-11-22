#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 22 23:45 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/manual_hv_control

@author: Dylan Neff, dn277127
"""

import sys
from caen_hv_py.CAENHVController import CAENHVController


def main():
    power_off = False

    if len(sys.argv) == 2 and sys.argv[1].lower() == 'power-off':
        power_off = True

    hv_info = {
        'ip': '192.168.10.199',
        'username': 'admin',
        'password': 'admin',
    }
    channels = [(5, 2), (5, 3), (5, 6), (5, 7), (5, 8), (5, 9)]
    print('Reading HV channels...')
    hv_data = read_hv_channels(hv_info, channels)
    for (slot, channel), data in hv_data.items():
        print(f'Slot {slot} Channel {channel}: Voltage = {data["voltage"]} V, Current = {data["current"]} uA')

    if power_off:
        power_off_channels = channels  # Power off all read channels
        power_off_hvs(hv_info, power_off_channels)

    print('donzo')


def power_off_hvs(hv_info, power_off_channels):
    ip_address, username, password = hv_info['ip'], hv_info['username'], hv_info['password']
    print('Powering off HV...')
    with CAENHVController(ip_address, username, password) as caen_hv:
        for slot, channel in power_off_channels:
            power = caen_hv.get_ch_power(int(slot), int(channel))
            if power:
                caen_hv.set_ch_pw(int(slot), int(channel), 0)
    print('HV Powered Off')


def read_hv_channels(hv_info, channels):
    ip_address, username, password = hv_info['ip'], hv_info['username'], hv_info['password']
    hv_data = {}
    with CAENHVController(ip_address, username, password) as caen_hv:
        for slot, channel in channels:
            voltage = caen_hv.get_ch_vmon(int(slot), int(channel))
            current = caen_hv.get_ch_imon(int(slot), int(channel))
            hv_data[(slot, channel)] = {'voltage': voltage, 'current': current}
    return hv_data


if __name__ == '__main__':
    main()

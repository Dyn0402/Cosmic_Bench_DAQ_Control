#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on July 19 08:14 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/trigger_manual

@author: Dylan Neff, dn277127
"""

import sys
from time import sleep
from Client import Client


def main():
    argv = sys.argv
    if len(argv) < 2:
        print('No command given')
        return
    state = argv[1]
    if len(argv) == 3:
        sleep_time = int(argv[2])
    else:
        sleep_time = 5
    if len(argv) == 4:
        num_triggers = int(argv[1])
        freq_hz = float(argv[2])
        pulse_freq_ratio = float(argv[3])

    # trigger_switch_ip, trigger_switch_port = '192.168.10.101', 1100
    trigger_switch_ip, trigger_switch_port = '192.168.10.101', 1105
    with Client(trigger_switch_ip, trigger_switch_port) as trigger_switch_client:
        trigger_switch_client.send('Connected to trigger manual control')
        trigger_switch_client.receive()

        if len(argv) <= 3:
            trigger_switch_client.send(state)
            trigger_switch_client.receive()
            sleep(sleep_time)
        else:
            trigger_switch_client.send(f'send triggers {num_triggers} {freq_hz} {pulse_freq_ratio}')
            trigger_switch_client.receive()
        trigger_switch_client.send('Finished')
        trigger_switch_client.receive()
    print('donzo')


if __name__ == '__main__':
    main()

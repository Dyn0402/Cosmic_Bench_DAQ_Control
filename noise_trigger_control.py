#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 03 14:25 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/noise_trigger_control

@author: Dylan Neff, dn277127
"""


from time import time, sleep
from Client import Client


def main():
    n_triggers = 500
    trig_high_pause, inter_trig_pause = 1, 1  # ms
    trigger_switch_ip, trigger_switch_port = '169.254.91.5', 1100
    with Client(trigger_switch_ip, trigger_switch_port) as trigger_switch_client:
        trigger_switch_client.send('Connected to daq_control')
        trigger_switch_client.receive()
        for trig_i in range(n_triggers):
            trigger_switch_client.send('on')
            trigger_switch_client.receive()
            sleep(trig_high_pause / 1000)
            trigger_switch_client.send('off')
            trigger_switch_client.receive()
            sleep(inter_trig_pause / 1000)
        trigger_switch_client.send('Finished')
        trigger_switch_client.receive()

    print('donzo')


if __name__ == '__main__':
    main()

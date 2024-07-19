#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 03 14:25 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/noise_trigger_control

@author: Dylan Neff, dn277127
"""


from time import time, sleep
from random import random
from Client import Client


def main():
    n_triggers = 5000
    trig_width, inter_trig_pause, inter_trig_rand_pause = 0.01, 0.5, 0.2  # ms
    trigger_switch_ip, trigger_switch_port = '192.168.10.101', 1100
    with Client(trigger_switch_ip, trigger_switch_port) as trigger_switch_client:
        trigger_switch_client.send('Connected to daq_control')
        trigger_switch_client.receive()
        for trig_i in range(n_triggers):
            trigger_switch_client.send('on')
            trigger_switch_client.receive()
            sleep(trig_width / 1000)
            trigger_switch_client.send('off')
            trigger_switch_client.receive()
            pause = inter_trig_pause + inter_trig_rand_pause * random()
            sleep(pause / 1000)
        trigger_switch_client.send('Finished')
        trigger_switch_client.receive()

    print('donzo')


if __name__ == '__main__':
    main()

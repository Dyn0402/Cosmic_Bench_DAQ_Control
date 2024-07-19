#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on July 19 08:14 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/trigger_manual

@author: Dylan Neff, dn277127
"""

import sys
from Client import Client


def main():
    argv = sys.argv
    if len(argv) < 2:
        print('No command given')
        return
    state = argv[1]
    trigger_switch_ip, trigger_switch_port = '169.254.91.5', 1100
    with Client(trigger_switch_ip, trigger_switch_port) as trigger_switch_client:
        trigger_switch_client.send('Connected to trigger manual control')
        trigger_switch_client.receive()
        trigger_switch_client.send(state)
        trigger_switch_client.receive()
        trigger_switch_client.send('Finished')
        trigger_switch_client.receive()
    print('donzo')


if __name__ == '__main__':
    main()

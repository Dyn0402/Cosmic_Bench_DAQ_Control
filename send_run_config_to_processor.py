#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on October 22 10:36 PM 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/send_run_config_to_processor.py

@author: Dylan Neff, Dylan
"""

import sys
from Client import Client

RUNCONFIG_REL_PATH = "config/json_run_configs/"


def main():
    if len(sys.argv) != 2:
        print('No run config path given')
        return
    run_config_file = sys.argv[1]
    run_config_path = f'{RUNCONFIG_REL_PATH}{run_config_file}'

    processor_server_client = Client('192.168.10.8', 1250)

    with processor_server_client as client:
        client.send('Connected to run config sender')
        client.receive()

        client.send(f'config {run_config_path}')
        client.receive()

        client.send('Finished')

    print('donzo')


if __name__ == '__main__':
    main()

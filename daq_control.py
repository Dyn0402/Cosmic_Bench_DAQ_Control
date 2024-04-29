#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 8:58 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/daq_control.py

@author: Dylan Neff, Dylan
"""

import os
import time

from Client import Client
from DAQController import DAQController

from run_config import Config


def main():
    config = Config()
    server_ip, port = '192.168.10.1', 1100
    with Client(server_ip, port=port) as client:
        client.send('Hello')
        res = client.receive()
        print(res)

        create_dir_if_not_exist(config.run_dir)
        for sub_run in config.sub_runs:
            sub_run_name = sub_run['sub_run_name']
            client.send(f'Start {sub_run_name}')
            res = client.receive()
            if 'HV Set' in res:
                print(res)
                daq_controller = DAQController(config.daq_config_path, sub_run_name, config.run_dir)
                daq_controller.run()
                print('DAQ Done')
        client.send(f'Finished')
    print('donzo')


def create_dir_if_not_exist(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)


if __name__ == '__main__':
    main()

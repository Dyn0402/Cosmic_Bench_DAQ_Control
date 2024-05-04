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
    banco = 'banco' in [det['name'] for det in config.detectors]
    hv_ip, hv_port = '192.168.10.1', 1100
    trigger_switch_ip, trigger_switch_port = '169.254.91.5', 1100
    banco_daq_ip, banco_daq_port = '192.168.122.1', 1100
    with (Client(hv_ip, hv_port) as hv_client, Client(trigger_switch_ip, trigger_switch_port) as trigger_switch_client,
          Client(banco_daq_ip, banco_daq_port) as banco_daq_client):
        hv_client.send('Connected to daq_control')
        hv_client.receive()
        hv_client.send_json(config.hv_info)

        if banco:
            trigger_switch_client.send('Connected to daq_control')
            trigger_switch_client.receive()

            banco_daq_client.send('Connected to daq_control')
            banco_daq_client.receive()
            banco_daq_client.send_json(config.banco_info)

        create_dir_if_not_exist(config.run_dir)
        for sub_run in config.sub_runs:
            sub_run_name = sub_run['sub_run_name']
            sub_dir = f'{config.run_dir}{sub_run_name}/'
            create_dir_if_not_exist(sub_dir)
            if banco:
                trigger_switch_client.send('off')  # Turn off trigger to make sure daqs are synced
                trigger_switch_client.receive()
            # sub_run_name = sub_run['sub_run_name']
            # hv_client.send(f'Start {sub_run_name}')
            hv_client.send('Start')
            hv_client.send_json(sub_run)
            res = hv_client.receive()
            if 'HV Set' in res:
                if banco:
                    banco_daq_client.send(f'Start {sub_run_name}')
                    banco_daq_client.receive()

                daq_controller = DAQController(config.daq_config_path, sub_run['run_time'], sub_run_name, sub_dir)
                if banco:
                    daq_controller.run(trigger_switch_client)
                else:
                    daq_controller.run()

                if banco:
                    banco_daq_client.send('Stop')
                    banco_daq_client.receive()
                print('DAQ Done')
        hv_client.send(f'Finished')
    print('donzo')


def create_dir_if_not_exist(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)


if __name__ == '__main__':
    main()

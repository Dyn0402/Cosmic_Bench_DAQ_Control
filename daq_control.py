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
    banco = 'banco' in config.included_detectors

    hv_ip, hv_port = config.hv_info['ip'], config.hv_info['port']
    trigger_switch_ip, trigger_switch_port = config.trigger_switch_info['ip'], config.trigger_switch_info['port']
    banco_daq_ip, banco_daq_port = config.banco_info['ip'], config.banco_info['port']
    dedip196_ip, dedip196_port = config.processor_info['ip'], config.processor_info['port']

    with (Client(hv_ip, hv_port) as hv_client if True else None,
          Client(trigger_switch_ip, trigger_switch_port) if banco else None as trigger_switch_client,
          Client(banco_daq_ip, banco_daq_port) if banco else None as banco_daq_client,
          Client(dedip196_ip, dedip196_port) as processor_client):
        hv_client.send('Connected to daq_control')
        hv_client.receive()
        hv_client.send_json(config.hv_info)

        if banco:
            trigger_switch_client.send('Connected to daq_control')
            trigger_switch_client.receive()

            banco_daq_client.send('Connected to daq_control')
            banco_daq_client.receive()
            banco_daq_client.send_json(config.banco_info)

        processor_client.send('Connected to daq_control')
        processor_client.receive()
        processor_client.send_json(config.processor_info)

        create_dir_if_not_exist(config.run_dir)
        create_dir_if_not_exist(config.run_out_dir)
        for sub_run in config.sub_runs:
            sub_run_name = sub_run['sub_run_name']
            sub_run_dir = f'{config.run_dir}{sub_run_name}/'
            create_dir_if_not_exist(sub_run_dir)
            sub_top_out_dir = f'{config.run_out_dir}{sub_run_name}/'
            create_dir_if_not_exist(sub_top_out_dir)
            sub_out_dir = f'{sub_top_out_dir}{config.raw_daq_inner_dir}/'
            create_dir_if_not_exist(sub_out_dir)
            if banco:
                trigger_switch_client.send('off')  # Turn off trigger to make sure daqs are synced
                trigger_switch_client.receive()
            # sub_run_name = sub_run['sub_run_name']
            # hv_client.send(f'Start {sub_run_name}')
            hv_client.send('Start')
            hv_client.receive()
            hv_client.send_json(sub_run)
            res = hv_client.receive()
            if 'HV Set' in res:
                if banco:
                    banco_daq_client.send(f'Start {sub_run_name}')
                    banco_daq_client.receive()

                daq_controller = DAQController(config.daq_config_path, sub_run['run_time'],
                                               sub_run_name, sub_run_dir, sub_out_dir)
                if banco:
                    daq_controller.run(trigger_switch_client)
                else:
                    daq_controller.run()

                if banco:
                    banco_daq_client.send('Stop')
                    banco_daq_client.receive()

                processor_client.send(f'Decode FDFs {sub_run_name}')
                processor_client.receive()
                processor_client.send(f'Run M3 Tracking {sub_run_name}')
                processor_client.receive()
                if banco:
                    pass  # Process banco data

                print('DAQ Done')
        hv_client.send(f'Finished')
    print('donzo')


def create_dir_if_not_exist(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)


if __name__ == '__main__':
    main()

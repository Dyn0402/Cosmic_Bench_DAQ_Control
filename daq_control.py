#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 8:58 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/daq_control.py

@author: Dylan Neff, Dylan
"""

import os
from time import sleep
from contextlib import nullcontext

from Client import Client
from DAQController import DAQController

from run_config import Config
from common_functions import *


def main():
    config = Config()
    banco = any(['banco' in detector_name for detector_name in config.included_detectors])

    hv_ip, hv_port = config.hv_control_info['ip'], config.hv_control_info['port']
    trigger_switch_ip, trigger_switch_port = config.trigger_switch_info['ip'], config.trigger_switch_info['port']
    banco_daq_ip, banco_daq_port = config.banco_info['ip'], config.banco_info['port']
    dedip196_ip, dedip196_port = config.dedip196_processor_info['ip'], config.dedip196_processor_info['port']
    sedip28_ip, sedip28_port = config.sedip28_processor_info['ip'], config.sedip28_processor_info['port']

    hv_client = Client(hv_ip, hv_port)
    trigger_switch_client = Client(trigger_switch_ip, trigger_switch_port) if banco else nullcontext()
    banco_daq_client = Client(banco_daq_ip, banco_daq_port) if banco else nullcontext()
    dedip196_processor_client = Client(dedip196_ip, dedip196_port)
    sedip28_processor_client = Client(sedip28_ip, sedip28_port)

    # with (Client(hv_ip, hv_port) as hv_client,
    #       Client(trigger_switch_ip, trigger_switch_port) if banco else None as trigger_switch_client,
    #       Client(banco_daq_ip, banco_daq_port) if banco else None as banco_daq_client,
    #       Client(dedip196_ip, dedip196_port) as dedip196_processor_client):
    with (hv_client as hv, trigger_switch_client as trigger_switch, banco_daq_client as banco_daq,
          dedip196_processor_client as dedip196_processor, sedip28_processor_client as sedip28_processor):
        hv.send('Connected to daq_control')
        hv.receive()
        hv.send_json(config.hv_info)

        if banco:
            trigger_switch.send('Connected to daq_control')
            trigger_switch.receive()

            banco_daq.send('Connected to daq_control')
            banco_daq.receive()
            banco_daq.send_json(config.banco_info)

        dedip196_processor.send('Connected to daq_control')
        dedip196_processor.receive()
        dedip196_processor.send_json(config.dedip196_processor_info)
        dedip196_processor.send_json({'included_detectors': config.included_detectors})
        dedip196_processor.send_json({'detectors': config.detectors})

        sedip28_processor.send('Connected to daq_control')
        sedip28_processor.receive()
        sedip28_processor.send_json(config.sedip28_processor_info)

        create_dir_if_not_exist(config.run_dir)
        create_dir_if_not_exist(config.run_out_dir)
        config.write_to_file(f'{config.run_out_dir}run_config.json')
        for sub_run in config.sub_runs:
            sub_run_name = sub_run['sub_run_name']
            sub_run_dir = f'{config.run_dir}{sub_run_name}/'
            create_dir_if_not_exist(sub_run_dir)
            sub_top_out_dir = f'{config.run_out_dir}{sub_run_name}/'
            create_dir_if_not_exist(sub_top_out_dir)
            sub_out_dir = f'{sub_top_out_dir}{config.raw_daq_inner_dir}/'
            create_dir_if_not_exist(sub_out_dir)
            if banco:
                trigger_switch.send('off')  # Turn off trigger to make sure daqs are synced
                trigger_switch.receive()
            # sub_run_name = sub_run['sub_run_name']
            # hv.send(f'Start {sub_run_name}')
            hv.send('Start')
            hv.receive()
            hv.send_json(sub_run)
            res = hv.receive()
            if 'HV Set' in res:
                if banco:
                    banco_daq.send(f'Start {sub_run_name}')
                    banco_daq.receive()

                daq_trigger_switch = trigger_switch if banco else None
                daq_controller = DAQController(config.dream_daq_info['daq_config_template_path'], sub_run['run_time'],
                                               sub_run_name, sub_run_dir, sub_out_dir, daq_trigger_switch)

                daq_success = False
                while not daq_success:  # Rerun if failure
                    daq_success = daq_controller.run()

                if banco:
                    banco_daq.send('Stop')
                    banco_daq.receive()

                dedip196_processor.send(f'Decode FDFs {sub_run_name}')
                dedip196_processor.receive()
                sedip28_processor.send(f'Run M3 Tracking {sub_run_name}')
                sedip28_processor.receive()
                # Run filtering
                if banco:
                    pass  # Process banco data

                print(f'Finished {sub_run_name}, waiting 10 seconds before next run')
                sleep(10)
        hv.send('Finished')
        banco_daq.send('Finished')
    print('donzo')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 8:58 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/daq_control.py

@author: Dylan Neff, Dylan
"""

import os
import shutil
from time import sleep
import threading
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
        dedip196_processor.receive()
        dedip196_processor.send_json({'included_detectors': config.included_detectors})
        dedip196_processor.receive()
        dedip196_processor.send_json({'detectors': config.detectors})
        dedip196_processor.receive()

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

                # dedip196_processor.send(f'Dedip196 Decode and Filter On The Fly {sub_run_name}')
                # sedip28_processor.send(f'Sedip28 M3 Tracking On The Fly {sub_run_name}')

                daq_trigger_switch = trigger_switch if banco else None
                daq_control_args = (config.dream_daq_info['daq_config_template_path'], sub_run['run_time'],
                                    sub_run_name, sub_run_dir, sub_out_dir, daq_trigger_switch)
                daq_controller_thread = threading.Thread(target=run_daq_controller, args=daq_control_args)
                process_files_args = (sub_run_dir, sub_out_dir, sub_run_name, dedip196_processor, sedip28_processor)
                process_files_on_the_fly_thread = threading.Thread(target=process_files_on_the_fly,
                                                                   args=process_files_args)

                daq_controller_thread.start()
                process_files_on_the_fly_thread.start()

                daq_controller_thread.join()
                # daq_controller = DAQController(config.dream_daq_info['daq_config_template_path'], sub_run['run_time'],
                #                                sub_run_name, sub_run_dir, sub_out_dir, daq_trigger_switch)
                #
                # daq_success = False
                # while not daq_success:  # Rerun if failure
                #     daq_success = daq_controller.run()

                if banco:
                    banco_daq.send('Stop')
                    banco_daq.receive()

                # dedip196_processor.send(f'Decode FDFs {sub_run_name}')
                # dedip196_processor.receive()
                # sedip28_processor.send(f'Run M3 Tracking {sub_run_name}')
                # sedip28_processor.receive()
                # # Run filtering
                # dedip196_processor.send(f'Filter By M3 {sub_run_name}')
                # dedip196_processor.receive()
                # # Remove all but filtered files
                # dedip196_processor.send(f'Clean Up Unfiltered {sub_run_name}')
                # dedip196_processor.receive()
                if banco:
                    pass  # Process banco data
                process_files_on_the_fly_thread.join()

                print(f'Finished {sub_run_name}, waiting 10 seconds before next run')
                sleep(10)
        hv.send('Finished')
        banco_daq.send('Finished')
        trigger_switch.send('Finished')
        dedip196_processor.send('Finished')
        sedip28_processor.send('Finished')
    print('donzo')


def run_daq_controller(config_template_path, run_time, sub_run_name, sub_run_dir, sub_out_dir, daq_trigger_switch):
    daq_controller = DAQController(config_template_path, run_time, sub_run_name, sub_run_dir, sub_out_dir,
                                   daq_trigger_switch)

    daq_success = False
    while not daq_success:  # Rerun if failure
        daq_success = daq_controller.run()


def process_files_on_the_fly(sub_run_dir, sub_out_dir, sub_run_name, dedip196_processor, sedip28_processor):
    """
    Process files on the fly as they are created by the DAQ.
    :param sub_run_dir: Directory where DAQ is writing files.
    :param sub_out_dir: Directory where processed files will be moved to.
    :param sub_run_name: Name of subrun.
    :param dedip196_processor: Client to dedip196 processor.
    :param sedip28_processor: Client to sedip28 processor.
    :return:
    """

    create_dir_if_not_exist(sub_out_dir)
    sleep(60)  # Wait on start for daq to start running
    file_num, running = 0, True
    dedip196_processor.send('Starting on fly processing', silent=True)  # Debug
    dedip196_processor.receive(silent=True)
    while running:
        if file_num_still_running(sub_run_dir, file_num):
            sleep(60)  # Wait for file to finish
        else:  # File is done, process it
            for file_name in os.listdir(sub_run_dir):
                if file_name.endswith('.fdf') and get_file_num_from_fdf_file_name(file_name, -2) == file_num:
                    shutil.move(f'{sub_run_dir}{file_name}', f'{sub_out_dir}{file_name}')

            dedip196_processor.send(f'Decode FDFs {file_num} {sub_run_name}', silent=True)
            dedip196_processor.receive(silent=True)
            sedip28_processor.send(f'Run M3 Tracking {file_num} {sub_run_name}', silent=True)
            sedip28_processor.receive(silent=True)
            # Run filtering
            dedip196_processor.send(f'Filter By M3 {file_num} {sub_run_name}', silent=True)
            dedip196_processor.receive(silent=True)
            # Remove all but filtered files
            dedip196_processor.send(f'Clean Up Unfiltered {file_num} {sub_run_name}', silent=True)
            dedip196_processor.receive(silent=True)

            if found_file_num(sub_run_dir, file_num + 1):
                file_num += 1  # Move on to next file
            else:
                running = False  # Subrun over, exit
        dedip196_processor.send(f'On fly processing running={running}', silent=True)  # Debug
        dedip196_processor.receive(silent=True)


def found_file_num(fdf_dir, file_num):
    """
    Look for file number in fdf dir. Return True if found, False if not
    :param fdf_dir: Directory containing fdf files
    :param file_num:
    :return:
    """
    for file_name in os.listdir(fdf_dir):
        if not file_name.endswith('.fdf') or '_datrun_' not in file_name:
            continue
        if file_num == get_file_num_from_fdf_file_name(file_name, -2):
            return True
    return False


def file_num_still_running(fdf_dir, m3_tracking_feu_num=1, wait_time=30):
    """
    Check if dream DAQ is still running by finding m3 fdf and checking to see if file size increases within wait_time
    :param fdf_dir: Directory containing fdf files
    :param m3_tracking_feu_num: FEU number of m3 tracking fdf
    :param wait_time: Time to wait for file size increase
    :return: True if size increased over wait time (still running), False if not.
    """
    m3_fdf = None
    for file in os.listdir(fdf_dir):
        if not file.endswith('.fdf') or '_datrun_' not in file:
            continue
        if get_feu_num_from_fdf_file_name(file) == m3_tracking_feu_num:
            m3_fdf = file
            break

    if m3_fdf is None:
        print(f'No M3 tracking fdf found in {fdf_dir}')
        return False

    original_size = os.path.getsize(f'{fdf_dir}{m3_fdf}')
    sleep(wait_time)
    new_size = os.path.getsize(f'{fdf_dir}{m3_fdf}')

    if new_size > original_size:
        return True
    else:
        return False


if __name__ == '__main__':
    main()

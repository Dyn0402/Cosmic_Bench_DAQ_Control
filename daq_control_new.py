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
from datetime import datetime
import threading
from contextlib import nullcontext

from Client import Client
from DAQController import DAQController

from run_config import Config
from common_functions import *


def main():
    config = Config()
    config.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    banco = any(['banco' in detector_name for detector_name in config.included_detectors])
    m3 = any(['m3' in detector_name for detector_name in config.included_detectors])
    m3 = False if config.m3_feu_num is None else m3

    hv_ip, hv_port = config.hv_control_info['ip'], config.hv_control_info['port']
    trigger_switch_ip, trigger_switch_port = config.trigger_switch_info['ip'], config.trigger_switch_info['port']
    banco_daq_ip, banco_daq_port = config.banco_info['ip'], config.banco_info['port']
    dedip196_ip, dedip196_port = config.dedip196_processor_info['ip'], config.dedip196_processor_info['port']
    sedip28_ip, sedip28_port = config.sedip28_processor_info['ip'], config.sedip28_processor_info['port']
    dream_daq_ip, dream_daq_port = config.dream_daq_info['ip'], config.dream_daq_info['port']

    hv_client = Client(hv_ip, hv_port)
    trigger_switch_client = Client(trigger_switch_ip, trigger_switch_port) if banco else nullcontext()
    banco_daq_client = Client(banco_daq_ip, banco_daq_port) if banco else nullcontext()
    dedip196_processor_client = Client(dedip196_ip, dedip196_port)
    sedip28_processor_client = Client(sedip28_ip, sedip28_port)
    dream_daq_client = Client(dream_daq_ip, dream_daq_port)

    # with (Client(hv_ip, hv_port) as hv_client,
    #       Client(trigger_switch_ip, trigger_switch_port) if banco else None as trigger_switch_client,
    #       Client(banco_daq_ip, banco_daq_port) if banco else None as banco_daq_client,
    #       Client(dedip196_ip, dedip196_port) as dedip196_processor_client):
    with (hv_client as hv, trigger_switch_client as trigger_switch, banco_daq_client as banco_daq,
          dedip196_processor_client as dedip196_processor, sedip28_processor_client as sedip28_processor,
          dream_daq_client as dream_daq):
        hv.send('Connected to daq_control')
        hv.receive()
        hv.send_json(config.hv_info)

        dream_daq.send('Connected to daq_control')
        dream_daq.receive()
        dream_daq.send_json(config.dream_daq_info)

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

        sleep(2)  # Wait for all clients to do what they need to do (specifically, create directories)

        # create_dir_if_not_exist(config.run_dir)
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
                run_time = sub_run['run_time'] * 60 if daq_trigger_switch is None else sub_run['run_time'] * 60 + 5
                daq_control_args = (sub_run_name, run_time, sub_out_dir, daq_trigger_switch, dream_daq)
                # daq_controller_thread = threading.Thread(target=run_daq_controller, args=daq_control_args)
                # if config.process_on_fly:
                #     daq_finished = threading.Event()
                #     process_files_args = (sub_run_dir, sub_out_dir, sub_run_name, dedip196_processor, sedip28_processor,
                #                           daq_finished, m3, config.filtering_by_m3)
                #     process_files_on_the_fly_thread = threading.Thread(target=process_files_on_the_fly,
                #                                                    args=process_files_args)

                try:
                    # daq_controller_thread.start()
                    # if config.process_on_fly:
                    #     process_files_on_the_fly_thread.start()
                    run_daq_controller(*daq_control_args)

                    # daq_controller_thread.join()
                except KeyboardInterrupt:
                    print('Keyboard Interrupt, stopping run')
                finally:
                    # if config.process_on_fly:
                    #     daq_finished.set()
                    if banco:
                        banco_daq.send('Stop')
                        banco_daq.receive()

                    if banco:
                        pass  # Process banco data
                    # if config.process_on_fly:
                    #     process_files_on_the_fly_thread.join()

                    print(f'Finished {sub_run_name}, waiting 10 seconds before next run')
                    sleep(10)
        if config.power_off_hv_at_end:
            hv.send('Power Off')
            hv.receive()  # Starting power off
            hv.receive()  # Finished power off
        hv.send('Finished')
        if banco:
            banco_daq.send('Finished')
            trigger_switch.send('Finished')
        dedip196_processor.send('Finished')
        sedip28_processor.send('Finished')
    print('donzo')


def run_daq_controller(sub_run_name, run_time, sub_out_dir, daq_trigger_switch, dream_daq_client):
    daq_controller = DAQController(run_time=run_time, out_dir=sub_out_dir, out_name=sub_run_name,
                                   trigger_switch_client=daq_trigger_switch, dream_daq_client=dream_daq_client)

    daq_success = False
    while not daq_success:  # Rerun if failure
        daq_success = daq_controller.run_new()


def process_files_on_the_fly(sub_run_dir, sub_out_dir, sub_run_name, dedip196_processor, sedip28_processor,
                             daq_finished, m3_tracking=True, filtering=True):
    """
    Process files on the fly as they are created by the DAQ.
    :param sub_run_dir: Directory where DAQ is writing files.
    :param sub_out_dir: Directory where processed files will be moved to.
    :param sub_run_name: Name of subrun.
    :param dedip196_processor: Client to dedip196 processor.
    :param sedip28_processor: Client to sedip28 processor.
    :param daq_finished: Event to signal when DAQ is finished.
    :param m3_tracking: Run M3 tracking after decoding.
    :param filtering: Run filtering after tracking.
    :return:
    """

    create_dir_if_not_exist(sub_out_dir)
    sleep(60 * 5)  # Wait on start for daq to start running
    file_num, running = 0, True
    while running:
        if not daq_finished.is_set() and file_num_still_running(sub_run_dir, file_num, silent=True):
            if not daq_finished.is_set():  # Check again to see if daq finished while checking if file was still running
                sleep(30)  # Wait for file to finish
        else:  # File is done, process it
            if daq_finished.is_set():
                print('DAQ Finished, processing last files')
                sleep(3)  # If daq finished, give it a second to finish writing files then process them
            for file_name in os.listdir(sub_run_dir):
                if file_name.endswith('.fdf') and get_file_num_from_fdf_file_name(file_name, -2) == file_num:
                    shutil.move(f'{sub_run_dir}{file_name}', f'{sub_out_dir}{file_name}')

            dedip196_processor.send(f'Decode FDFs file_num={file_num} {sub_run_name}', silent=True)
            dedip196_processor.receive(silent=True)
            if m3_tracking:
                sedip28_processor.send(f'Run M3 Tracking file_num={file_num} {sub_run_name}', silent=True)
                sedip28_processor.receive(silent=True)
                sedip28_processor.receive(silent=True)  # Wait for tracking to finish
            dedip196_processor.receive(silent=True)  # Wait for decoding to finish

            if m3_tracking and filtering:
                # Run filtering
                dedip196_processor.send(f'Filter By M3 file_num={file_num} {sub_run_name}', silent=True)
                dedip196_processor.receive(silent=True)
                dedip196_processor.receive(silent=True)  # Wait for filtering to finish
            else:
                dedip196_processor.send(f'Copy To Filtered file_num={file_num} {sub_run_name}', silent=True)
                dedip196_processor.receive(silent=True)
                dedip196_processor.receive(silent=True)  # Wait for copy to finish

            # Remove all but filtered files
            dedip196_processor.send(f'Clean Up Unfiltered file_num={file_num} {sub_run_name}', silent=True)
            dedip196_processor.receive(silent=True)
            dedip196_processor.receive(silent=True)  # Wait for cleanup to finish

            if found_file_num(sub_run_dir, file_num + 1):
                file_num += 1  # Move on to next file
            else:
                running = False  # Subrun over, exit


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


def file_num_still_running(fdf_dir, file_num, wait_time=30, silent=False):
    """
    Check if dream DAQ is still running by finding all fdfs with file_num and checking to see if any file size
    increases within wait_time
    :param fdf_dir: Directory containing fdf files
    :param file_num: File number to check for
    :param wait_time: Time to wait for file size increase
    :param silent: Print debug info
    :return: True if size increased over wait time (still running), False if not.
    """
    file_paths = []
    for file in os.listdir(fdf_dir):
        if not file.endswith('.fdf') or '_datrun_' not in file:
            continue  # Skip non fdf data files
        if get_file_num_from_fdf_file_name(file) == file_num:
            file_paths.append(f'{fdf_dir}{file}')

    if len(file_paths) == 0:
        if not silent:
            print(f'No fdfs with file num {file_num} found in {fdf_dir}')
        return False

    old_sizes = []
    for fdf_path in file_paths:
        old_sizes.append(os.path.getsize(fdf_path))
        if not silent:
            print(f'File: {fdf_path} Original Size: {old_sizes[-1]}')

    sleep(wait_time)

    new_sizes = []
    for fdf_path in file_paths:
        new_sizes.append(os.path.getsize(fdf_path))
        if not silent:
            print(f'File: {fdf_path} New Size: {new_sizes[-1]}')

    for i in range(len(old_sizes)):
        if not silent:
            print(f'File: {file_paths[i]} Original Size: {old_sizes[i]} New Size: {new_sizes[i]}')
            print(f'Increased? {new_sizes[i] > old_sizes[i]}')
        if new_sizes[i] > old_sizes[i]:
            return True
    return False


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 08 13:57 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/dream_daq_control

@author: Dylan Neff, dn277127
"""

import os
import sys
from subprocess import Popen, PIPE
from time import sleep
import traceback
import shutil
import threading
from Server import Server
import socket
from common_functions import *


def main():
    port = 1101
    while True:
        try:
            clear_terminal()  # Dream DAQ output can get messy, try to clear after
            with Server(port=port) as server:
                server.receive()
                server.send('Dream DAQ control connected')
                dream_info = server.receive_json()
                cfg_template_path = dream_info['daq_config_template_path']
                run_directory = dream_info['run_directory']
                out_directory = dream_info['data_out_dir']
                raw_daq_inner_dir = dream_info['raw_daq_inner_dir']
                go_timeout = dream_info['go_timeout']
                max_run_time_addition = dream_info['max_run_time_addition']
                copy_on_fly = dream_info['copy_on_fly']
                batch_mode = dream_info['batch_mode']
                original_working_directory = os.getcwd()

                create_dir_if_not_exist(run_directory)
                create_dir_if_not_exist(out_directory)

                res = server.receive()
                while 'Finished' not in res:
                    if 'Start' in res:
                        print(res)
                        sub_run_name, run_time = res.split()[-2], int(float((res.split()[-1])))
                        print(f'Sub-run name: {sub_run_name}, Run time: {run_time} minutes')
                        sub_run_out_raw_inner_dir = f'{out_directory}/{sub_run_name}/{raw_daq_inner_dir}/'
                        create_dir_if_not_exist(sub_run_out_raw_inner_dir)

                        if run_directory is not None:
                            sub_run_dir = f'{run_directory}{sub_run_name}/'
                            print('Changing to sub-run directory:', sub_run_dir)
                            create_dir_if_not_exist(sub_run_dir)
                            os.chdir(sub_run_dir)
                        else:
                            sub_run_dir = os.getcwd()

                        # run_command = f'RunCtrl -c {cfg_file_path} -f {sub_run_name}'
                        # print(f'Running command: {run_command}')
                        # input('Press Enter to continue...')
                        #
                        # process = Popen(run_command, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
                        # start, run_start, sent_go_time, sent_continue_time = time.time(), None, None, None
                        # sent_go, sent_continue, run_successful, triggered, triggered_off = False, False, True, False, False
                        # server.send('Dream DAQ starting')
                        # max_run_time = run_time + max_run_time_addition
                        #
                        # if copy_on_fly:
                        #     daq_finished = threading.Event()
                        #     copy_files_args = (sub_run_dir, sub_run_out_raw_inner_dir, daq_finished)
                        #     copy_files_on_the_fly_thread = threading.Thread(target=copy_files_on_the_fly,
                        #                                                     args=copy_files_args)
                        #     copy_files_on_the_fly_thread.start()
                        #
                        # while True:
                        #     output = process.stdout.readline()
                        #     # if output == '' and process.poll() is not None:
                        #     #     print('DAQ process finished.')
                        #     #     break
                        #     if not sent_go and output.strip() == '***':  # Start of run, begin taking pedestals
                        #         process.stdin.write('G')
                        #         process.stdin.flush()  # Ensure the command is sent immediately
                        #         sent_go, sent_go_time = True, time.time()
                        #         print('Taking pedestals.')
                        #         server.send('Dream DAQ taking pedestals')
                        #     elif not sent_continue and 'Press C to Continue' in output.strip():  # End of pedestals, begin taking data
                        #         process.stdin.write('C')  # Signal to start data taking
                        #         process.stdin.flush()
                        #         sent_continue, sent_continue_time = True, time.time()
                        #         print('DAQ started.')
                        #         server.send('Dream DAQ started')
                        #         break
                        #
                        #     if output.strip() != '':
                        #         print(output.strip())
                        #
                        #     go_time_out = time.time() - sent_go_time > go_timeout if sent_go and not sent_continue else False
                        #     run_time_out = time.time() - start > max_run_time * 60
                        #     # if go_time_out or run_time_out or (output == '' and process.poll() is not None):
                        #     if go_time_out or run_time_out:
                        #         print('DAQ process timed out.')
                        #         process.kill()
                        #         sleep(5)
                        #         run_successful = False
                        #         print('DAQ process timed out.')
                        #         server.send('Dream DAQ timed out')
                        #         break

                        # make_config_from_template done in DAQController
                        # cfg_file_path = make_config_from_template(cfg_template_path, sub_run_dir, run_time)
                        cfg_run_path = os.path.join(os.getcwd(), os.path.basename(cfg_template_path))
                        run_command = f'RunCtrl -c {cfg_run_path} -f {sub_run_name}'
                        if batch_mode:
                            run_command += ' -b'

                        process = Popen(run_command, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
                        start, taking_pedestals, run_successful = time.time(), False, True
                        server.send('Dream DAQ starting')
                        max_run_time = run_time + max_run_time_addition

                        if copy_on_fly:
                            daq_finished = threading.Event()
                            copy_files_args = (sub_run_dir, sub_run_out_raw_inner_dir, daq_finished)
                            copy_files_on_the_fly_thread = threading.Thread(target=copy_files_on_the_fly,
                                                                               args=copy_files_args)
                            copy_files_on_the_fly_thread.start()

                        while True:
                            output = process.stdout.readline()

                            if batch_mode:
                                if not taking_pedestals and '_TakePedThr' in output.strip():
                                    taking_pedestals = True
                                    server.send('Dream DAQ taking pedestals')
                                elif '_TakeData' in output.strip():
                                    server.send('Dream DAQ started')
                                    break
                            else:
                                if not taking_pedestals and output.strip() == '***':  # Start of run, begin taking pedestals
                                    process.stdin.write('G')
                                    process.stdin.flush()  # Ensure the command is sent immediately
                                    taking_pedestals = True
                                    print('Taking pedestals.')
                                    server.send('Dream DAQ taking pedestals')
                                elif 'Press C to Continue' in output.strip():  # End of pedestals, begin taking data
                                    process.stdin.write('C')  # Signal to start data taking
                                    process.stdin.flush()
                                    print('DAQ started.')
                                    server.send('Dream DAQ started')
                                    break

                            if output.strip() != '':
                                print(output.strip())

                            pedestals_time_out = time.time() - start > go_timeout and taking_pedestals
                            run_time_out = time.time() - start > max_run_time * 60
                            if pedestals_time_out or run_time_out:
                                print('DAQ process timed out.')
                                process.kill()
                                sleep(5)
                                run_successful = False
                                print('DAQ process timed out.')
                                server.send('Dream DAQ timed out')
                                break

                        stop_event = threading.Event()
                        server.set_timeout(1.0)  # Set timeout for socket operations

                        stop_thread = threading.Thread(target=listen_for_stop, args=(server, stop_event))
                        stop_thread.start()
                        screen_clear_period = 30
                        screen_clear_timer = time.time()
                        # sleep(2)
                        while True:  # DAQ running
                            if stop_event.is_set():
                                process.stdin.write('g')
                                process.stdin.flush()
                                print('Stop command received. Stopping DAQ.')
                                break

                            if time.time() - screen_clear_timer > screen_clear_period:  # Clear terminal every 5 minutes
                                clear_terminal()
                                screen_clear_timer = time.time()

                            output = process.stdout.readline()
                            if output == '' and process.poll() is not None:
                                print('DAQ process finished.')
                                break
                            if output.strip() != '':
                                print(output.strip())
                        # server.set_blocking(True)
                        print('Waiting for DAQ process to terminate.')
                        stop_event.set()  # Tell the listener thread to stop
                        stop_thread.join()
                        print('Listener thread joined.')
                        server.set_timeout(None)

                        # DAQ finished
                        if copy_on_fly:
                            print('Waiting for on-the-fly copy thread to finish.')
                            daq_finished.set()
                            copy_files_on_the_fly_thread.join()

                        os.chdir(original_working_directory)

                        if run_successful:
                            print('Moving data files.')
                            move_data_files(sub_run_dir, sub_run_out_raw_inner_dir)

                        server.send('Dream DAQ stopped')
                    else:
                        server.send('Unknown Command')
                    res = server.receive()
        except Exception as e:
            traceback.print_exc()
            print(f'Error: {e}')
            sleep(30)
    print('donzo')


def move_data_files(src_dir, dest_dir):
    for file in os.listdir(src_dir):
        if file.endswith('.fdf'):
            # shutil.move(f'{src_dir}/{file}', f'{dest_dir}/{file}')
            # Copy for now, maybe move and clean up later when more confident
            shutil.copy(f'{src_dir}/{file}', f'{dest_dir}/{file}')


def listen_for_stop(server, stop_event):
    while not stop_event.is_set():
        try:
            res = server.receive()
            if 'Stop' in res:
                stop_event.set()
                break
        except socket.timeout:
            continue  # just loop again and check stop_event



def copy_files_on_the_fly(sub_run_dir, sub_out_dir, daq_finished_event, check_interval=5):
    """
    Continuously copy .fdf files from sub_run_dir to sud_out_dir while DAQ is running.
    :param sub_run_dir: Sub-run directory to monitor for new files.
    :param sub_out_dir: Sub-run output directory to copy files to.
    :param daq_finished_event: threading.Event() that is set when DAQ is finished.
    :param check_interval: Time in seconds between checks for new files.
    :return:
    """

    create_dir_if_not_exist(sub_out_dir)
    sleep(60 * 1)  # Wait on start for daq to start running
    file_num = 0
    while not daq_finished_event.is_set():  # Running
        if not file_num_still_running(sub_run_dir, file_num, silent=True):
            for file_name in os.listdir(sub_run_dir):
                if file_name.endswith('.fdf') and get_file_num_from_fdf_file_name(file_name, -2) == file_num:
                    shutil.move(f'{sub_run_dir}{file_name}', f'{sub_out_dir}{file_name}')
            file_num += 1
        sleep(check_interval)  # Check every 5 seconds


# Done in DAQController
# def make_config_from_template(cfg_template_path, run_directory, run_time):
#     cfg_file_name = os.path.basename(cfg_template_path)
#     cfg_file_path = f'{run_directory}/{cfg_file_name}'.replace('//', '/')
#     shutil.copy(cfg_template_path, cfg_file_path)
#     with open(cfg_file_path, 'r') as file:
#         cfg_lines = file.readlines()
#     for i, line in enumerate(cfg_lines):
#         if 'Sys DaqRun Time' in line:
#             cfg_lines[i] = cfg_lines[i].replace('0', f'{run_time}')
#     with open(cfg_file_path, 'w') as file:
#         file.writelines(cfg_lines)
#     return cfg_file_path


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


def clear_terminal():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except:
        print('Failed to clear terminal')  # Ignore any errors


if __name__ == '__main__':
    main()

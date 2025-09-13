#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 08 13:57 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/dream_daq_control

@author: Dylan Neff, dn277127
"""

from subprocess import Popen, PIPE
from time import time, sleep
import shutil
import threading
from Server import Server
from socket import error as SocketError
from common_functions import *


def main():
    port = 1100
    while True:
        try:
            with Server(port=port) as server:
                server.receive()
                server.send('Dream DAQ control connected')
                dream_info = server.receive_json()
                cfg_template_path = dream_info['daq_config_template_path']
                run_directory = dream_info['run_directory']
                out_directory = dream_info['data_out_dir']
                raw_daq_inner_dir = dream_info['raw_daq_inner_dir']
                go_timeout = dream_info['go_timeout']
                max_run_time = dream_info['max_run_time']
                copy_on_fly = dream_info['copy_on_fly']
                original_working_directory = os.getcwd()

                create_dir_if_not_exist(run_directory)
                create_dir_if_not_exist(out_directory)

                res = server.receive()
                while 'Finished' not in res:
                    if 'Start' in res:
                        sub_run_name, run_time = res.split()[-2], int(res.split()[-1])
                        sub_run_out_raw_inner_dir = f'{out_directory}/{sub_run_name}/{raw_daq_inner_dir}'
                        create_dir_if_not_exist(sub_run_out_raw_inner_dir)

                        if run_directory is not None:
                            sub_run_dir = f'{run_directory}/{sub_run_name}/'
                            create_dir_if_not_exist(sub_run_dir)
                            os.chdir(sub_run_dir)
                        else:
                            sub_run_dir = os.getcwd()

                        cfg_file_path = make_config_from_template(cfg_template_path, sub_run_dir, run_time)

                        run_command = f'RunCtrl -c {cfg_file_path} -f {sub_run_name}'

                        process = Popen(run_command, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
                        start, run_start, sent_go_time, sent_continue_time = time(), None, None, None
                        sent_go, sent_continue, run_successful, triggered, triggered_off = False, False, True, False, False
                        server.send('Dream DAQ starting')

                        if copy_on_fly:
                            daq_finished = threading.Event()
                            copy_files_args = (sub_run_dir, sub_run_out_raw_inner_dir, sub_run_name, daq_finished)
                            copy_files_on_the_fly_thread = threading.Thread(target=copy_files_on_the_fly,
                                                                               args=copy_files_args)

                        while True:
                            output = process.stdout.readline()
                            # if output == '' and process.poll() is not None:
                            #     print('DAQ process finished.')
                            #     break
                            if not sent_go and output.strip() == '***':  # Start of run, begin taking pedestals
                                process.stdin.write('G')
                                process.stdin.flush()  # Ensure the command is sent immediately
                                sent_go, sent_go_time = True, time()
                                print('Taking pedestals.')
                                server.send('Dream DAQ taking pedestals')
                            elif not sent_continue and 'Press C to Continue' in output.strip():  # End of pedestals, begin taking data
                                process.stdin.write('C')  # Signal to start data taking
                                process.stdin.flush()
                                sent_continue, sent_continue_time = True, time()
                                print('DAQ started.')
                                server.send('Dream DAQ started')
                                break

                            if output.strip() != '':
                                print(output.strip())

                            go_time_out = time() - sent_go_time > go_timeout if sent_go and not sent_continue else False
                            run_time_out = time() - start > max_run_time * 60
                            if go_time_out or run_time_out or (output == '' and process.poll() is not None):
                                print('DAQ process timed out.')
                                process.kill()
                                sleep(5)
                                run_successful = False
                                print('DAQ process timed out.')
                                server.send('Dream DAQ timed out')
                                break

                        server.set_blocking(False)
                        while True:  # DAQ running
                            try:  # Check for stop command from controller
                                res = server.receive()
                                if 'Stop' in res:
                                    print('Stop command received. Stopping DAQ.')
                                    process.stdin.write('g')  # Send signal to stop run
                            except (BlockingIOError, SocketError):
                                pass  # No command received, continue

                            output = process.stdout.readline()
                            if output == '' and process.poll() is not None:
                                print('DAQ process finished.')
                                break
                            if output.strip() != '':
                                print(output.strip())
                        server.set_blocking(True)

                        # DAQ finished
                        if copy_on_fly:
                            daq_finished.set()
                            copy_files_on_the_fly_thread.join()
                        print('Waiting for DAQ process to terminate.')

                        os.chdir(original_working_directory)

                        if run_successful:
                            move_data_files(sub_run_dir, sub_run_out_raw_inner_dir)

                        server.send('Dream DAQ stopped')
                    else:
                        server.send('Unknown Command')
                    res = server.receive()
        except Exception as e:
            print(f'Error: {e}')
    print('donzo')


def move_data_files(src_dir, dest_dir):
    for file in os.listdir(src_dir):
        if file.endswith('.fdf'):
            # shutil.move(f'{src_dir}/{file}', f'{dest_dir}/{file}')
            # Copy for now, maybe move and clean up later when more confident
            shutil.copy(f'{src_dir}/{file}', f'{dest_dir}/{file}')


def copy_files_on_the_fly(sub_run_dir, sud_out_dir, daq_finished_event, check_interval=5):
    """
    Continuously copy .fdf files from sub_run_dir to sud_out_dir while DAQ is running.
    :param sub_run_dir: Sub-run directory to monitor for new files.
    :param sud_out_dir: Sub-run output directory to copy files to.
    :param daq_finished_event: threading.Event() that is set when DAQ is finished.
    :param check_interval: Time in seconds between checks for new files.
    :return:
    """

    create_dir_if_not_exist(sud_out_dir)
    sleep(60 * 5)  # Wait on start for daq to start running
    while not daq_finished_event.is_set():  # Running
        for file in os.listdir(sub_run_dir):
            if file.endswith('.fdf'):
                # shutil.copy(f'{sub_run_dir}/{file}', f'{sud_out_dir}/{file}')
                shutil.move(f'{sub_run_dir}/{file}', f'{sud_out_dir}/{file}')
        sleep(check_interval)  # Check every 5 seconds


def make_config_from_template(cfg_template_path, run_directory, run_time):
    cfg_file_name = os.path.basename(cfg_template_path)
    cfg_file_path = f'{run_directory}/{cfg_file_name}'
    shutil.copy(cfg_template_path, cfg_file_path)
    with open(cfg_file_path, 'r') as file:
        cfg_lines = file.readlines()
    for i, line in enumerate(cfg_lines):
        if 'Sys DaqRun Time' in line:
            cfg_lines[i] = cfg_lines[i].replace('0', f'{run_time}')
    with open(cfg_file_path, 'w') as file:
        file.writelines(cfg_lines)
    return cfg_file_path


if __name__ == '__main__':
    main()

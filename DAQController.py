#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 11:13 AM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/DAQController.py

@author: Dylan Neff, Dylan
"""

import os
from subprocess import Popen, PIPE
import shutil
from time import time, sleep


class DAQController:
    def __init__(self, cfg_file_path, run_time=10, out_name=None, run_dir=None, out_dir=None):
        self.run_directory = run_dir  # Relative to run_directory if not None
        self.out_directory = out_dir
        self.original_working_directory = os.getcwd()

        self.run_time = run_time  # minutes
        self.max_run_time = self.run_time * 2  # minutes After this time assume stuck and kill

        if out_name is None:
            self.run_command = f'RunCtrl -c {cfg_file_path}'
        else:
            self.run_command = f'RunCtrl -c {cfg_file_path} -f {out_name}'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.original_working_directory)

    def run(self, trigger_switch_client=None):
        if self.run_directory is not None:
            os.chdir(self.run_directory)
        process = Popen(self.run_command, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
        start, run_start = time(), None
        sent_go, sent_continue, run_successful = False, False, True
        while True:
            if sent_continue:
                if run_start is not None and time() - run_start >= self.run_time * 60:
                    print('Turning off trigger switch.')
                    if trigger_switch_client is not None:
                        trigger_switch_client.send('off')
                        trigger_switch_client.receive()
                    sleep(5)
                    print('Run finished.')
                    process.stdin.write('g')  # Signal to stop run
                    process.stdin.flush()
                sleep(1)
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                print('DAQ process finished.')
                break
            if not sent_go and output.strip() == '***':  # Start of run, begin taking pedestals
                print(' Got the stars. Writing G.')  # Signal to start run
                process.stdin.write('G')
                process.stdin.flush()  # Ensure the command is sent immediately
                sent_go = True
            elif not sent_continue and 'Press C to Continue' in output.strip():  # End of pedestals, begin taking data
                print(' Got the continue. Writing C.')
                process.stdin.write('C')  # Signal to start data taking
                process.stdin.flush()
                sleep(5)
                if trigger_switch_client is not None:
                    trigger_switch_client.send('on')
                    trigger_switch_client.receive()
                run_start = time()
            if output.strip() != '':
                print(output.strip())
            if time() - start > self.max_run_time * 60:
                print('DAQ process timed out.')
                process.kill()
                sleep(5)
                run_successful = False
                print('DAQ process timed out.')
                break

        os.chdir(self.original_working_directory)

        if run_successful:
            move_data_files(self.run_directory, self.out_directory)

        return run_successful


def move_data_files(src_dir, dest_dir):
    for file in os.listdir(src_dir):
        if file.endswith('.fdf'):
            # shutil.move(f'{src_dir}/{file}', f'{dest_dir}/{file}')
            # Copy for now, maybe move and clean up later when more confident
            shutil.copy(f'{src_dir}/{file}', f'{dest_dir}/{file}')

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
    def __init__(self, cfg_template_file_path, run_time=10, out_name=None, run_dir=None, out_dir=None,
                 trigger_switch_client=None):
        self.cfg_template_file_path = cfg_template_file_path
        self.run_directory = run_dir  # Relative to run_directory if not None
        self.out_directory = out_dir
        self.trigger_switch_client = trigger_switch_client
        self.original_working_directory = os.getcwd()

        self.run_time = run_time  # minutes
        self.max_run_time = self.run_time * 2  # minutes After this time assume stuck and kill

        # If trigger switch is used, need to run past run time to bracket the trigger switch on/off. Else just run time.
        self.cfg_file_run_time = self.run_time * 60 if self.trigger_switch_client is None else self.run_time * 60 + 60
        self.cfg_file_path = None
        self.make_config_from_template()

        if out_name is None:
            self.run_command = f'RunCtrl -c {self.cfg_file_path}'
        else:
            self.run_command = f'RunCtrl -c {self.cfg_file_path} -f {out_name}'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.original_working_directory)

    def run(self):
        if self.run_directory is not None:
            os.chdir(self.run_directory)
        process = Popen(self.run_command, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
        start, run_start, sent_go_time, sent_continue_time = time(), None, None, None
        sent_go, sent_continue, run_successful, triggered = False, False, True, False
        while True:
            # if sent_continue:
            #     if run_start is not None and time() - run_start >= self.run_time * 60:
            #         if self.trigger_switch_client is not None:
            #             print('Turning off trigger switch.')
            #             self.trigger_switch_client.send('off')
            #             self.trigger_switch_client.receive()
            #             print('Run finished.')
                    # sleep(5)
                    # process.stdin.write('g')  # Signal to stop run
                    # process.stdin.flush()
                # sleep(1)
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                print('DAQ process finished.')
                break
            if not sent_go and output.strip() == '***':  # Start of run, begin taking pedestals
                # sleep(2)
                # print(' Got the stars. Writing G.')  # Signal to start run
                # sleep(1)
                process.stdin.write('G')
                process.stdin.flush()  # Ensure the command is sent immediately
                sent_go, sent_go_time = True, time()
            elif not sent_continue and 'Press C to Continue' in output.strip():  # End of pedestals, begin taking data
                # sleep(2)
                # print(' Got the continue. Writing C.')
                # sleep(1)
                process.stdin.write('C')  # Signal to start data taking
                process.stdin.flush()
                sent_continue, sent_continue_time = True, time()
                run_start = time()

            # Need to wait a bit for DAQ to start
            if (not triggered and self.trigger_switch_client is not None and sent_continue
                    and time() - sent_continue_time > 40):
                self.trigger_switch_client.send('on')
                self.trigger_switch_client.receive()
                triggered = True
                run_start = time()  # Reset run time if trigger used

            if self.trigger_switch_client is not None and sent_continue:
                if run_start is not None and time() - run_start >= self.run_time * 60:
                    print('Turning off trigger switch.')
                    self.trigger_switch_client.send('off')
                    self.trigger_switch_client.receive()
                    print('Run finished.')

            if output.strip() != '':
                print(output.strip())

            go_time_out = time() - sent_go_time > 120 if sent_go and not sent_continue else False
            run_time_out = time() - start > self.max_run_time * 60
            if go_time_out or run_time_out:
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

    def make_config_from_template(self):
        dest = self.run_directory if self.run_directory is not None else self.original_working_directory
        cfg_file_name = os.path.basename(self.cfg_template_file_path)
        self.cfg_file_path = f'{dest}/{cfg_file_name}'
        shutil.copy(self.cfg_template_file_path, self.cfg_file_path)
        with open(self.cfg_file_path, 'r') as file:
            cfg_lines = file.readlines()
        for i, line in enumerate(cfg_lines):
            if 'Sys DaqRun Time' in line:
                cfg_lines[i] = cfg_lines[i].replace('  0  ', f'  {self.cfg_file_run_time}  ')
        with open(self.cfg_file_path, 'w') as file:
            file.writelines(cfg_lines)



def move_data_files(src_dir, dest_dir):
    for file in os.listdir(src_dir):
        if file.endswith('.fdf'):
            # shutil.move(f'{src_dir}/{file}', f'{dest_dir}/{file}')
            # Copy for now, maybe move and clean up later when more confident
            shutil.copy(f'{src_dir}/{file}', f'{dest_dir}/{file}')

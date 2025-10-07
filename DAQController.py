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
import threading


class DAQController:
    def __init__(self, cfg_template_file_path=None, run_time=10, out_name=None, run_dir=None, out_dir=None,
                 trigger_switch_client=None, dream_daq_client=None, zero_supress_mode=False):
        self.cfg_template_file_path = cfg_template_file_path
        self.run_directory = run_dir  # Relative to run_directory if not None
        self.out_directory = out_dir
        self.out_name = out_name
        self.trigger_switch_client = trigger_switch_client
        self.dream_daq_client = dream_daq_client
        self.original_working_directory = os.getcwd()

        self.run_time = run_time  # minutes
        self.max_run_time = self.run_time + 5  # minutes After this time assume stuck and kill
        self.go_timeout = 8 * 60  # seconds
        self.run_start_time = None
        self.measured_run_time = None
        self.zero_supress_mode = zero_supress_mode

        # If trigger switch is used, need to run past run time to bracket the trigger switch on/off. Else just run time.
        # DAQ resets timer when first trigger received, so only need short pause to be sure.
        self.cfg_file_run_time = self.run_time * 60 if self.trigger_switch_client is None else self.run_time * 60 + 5
        self.cfg_file_path = None
        if self.cfg_template_file_path is not None:
            self.make_config_from_template()

        if out_name is None:
            self.run_command = f'RunCtrl -c {self.cfg_file_path} -f test'  # Think I need an out name
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
        sent_go, sent_continue, run_successful, triggered, triggered_off = False, False, True, False, False
        if self.trigger_switch_client is not None:
            self.trigger_switch_client.silent = True

        try:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    print('DAQ process finished.')
                    break
                if not sent_go and output.strip() == '***':  # Start of run, begin taking pedestals
                    process.stdin.write('G')
                    process.stdin.flush()  # Ensure the command is sent immediately
                    sent_go, sent_go_time = True, time()
                elif not sent_continue and 'Press C to Continue' in output.strip():  # End of pedestals, begin taking data
                    process.stdin.write('C')  # Signal to start data taking
                    process.stdin.flush()
                    sent_continue, sent_continue_time = True, time()
                    print('DAQ process started.')
                    run_start = time()
                    self.run_start_time = run_start

                # Need to wait a bit for DAQ to start
                if (not triggered and self.trigger_switch_client is not None and sent_continue
                        and time() - sent_continue_time > 5):  # Takes 0 seconds to start, 5 to be safe
                    self.trigger_switch_client.send('on')
                    self.run_start_time = time()
                    self.trigger_switch_client.receive()
                    triggered = True
                    run_start = time()  # Reset run time if trigger used

                if self.trigger_switch_client is not None and sent_continue and triggered and not triggered_off:
                    if run_start is not None and time() - run_start >= self.run_time * 60:
                        self.trigger_switch_client.send('off')
                        self.measured_run_time = time() - self.run_start_time
                        self.trigger_switch_client.receive()
                        triggered_off = True

                if output.strip() != '':
                    print(output.strip())

                go_time_out = time() - sent_go_time > self.go_timeout if sent_go and not sent_continue else False
                run_time_out = time() - start > self.max_run_time * 60
                if go_time_out or run_time_out:
                    print('DAQ process timed out.')
                    process.kill()
                    sleep(5)
                    run_successful = False
                    print('DAQ process timed out.')
                    break
        except KeyboardInterrupt:
            print('Keyboard interrupt. Stopping DAQ process.')
            if self.trigger_switch_client is not None:
                self.trigger_switch_client.send('off')
            self.measured_run_time = time() - self.run_start_time
            if self.trigger_switch_client is not None:
                self.trigger_switch_client.receive()
            sleep(1)
            process.stdin.write('g')  # Send signal to stop run
            print('DAQ process stopped.')
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    print('DAQ process finished.')
                    break
                if output.strip() != '':
                    print(output.strip())
        finally:
            os.chdir(self.original_working_directory)
            if self.trigger_switch_client is not None:
                self.trigger_switch_client.silent = False

            if self.measured_run_time is None:
                self.measured_run_time = time() - self.run_start_time

            if run_successful:
                move_data_files(self.run_directory, self.out_directory)
                self.write_run_time()

        return run_successful

    def run_new(self):
        run_successful = True
        if self.trigger_switch_client is not None:
            self.trigger_switch_client.silent = True

        try:
            self.dream_daq_client.send(f'Start {self.out_name} {self.run_time}')
            res = self.dream_daq_client.receive()
            if res != 'Dream DAQ starting':
                print('Error starting Dream DAQ')
                return False

            res = self.dream_daq_client.receive()
            if res != 'Dream DAQ taking pedestals':
                print('Error taking pedestals')
                return False

            res = self.dream_daq_client.receive()
            if res != 'Dream DAQ started':
                print('Error starting DAQ')
                return False
            self.run_start_time = time()

            if self.trigger_switch_client is not None:
                sleep(5)  # Wait a bit to ensure DAQ is running before starting trigger
                self.trigger_switch_client.send('on')
                self.run_start_time = time()
                self.trigger_switch_client.receive()

            if self.trigger_switch_client:  # Wait for run to finish
                sleep(self.run_time * 60 - (time() - self.run_start_time))
                # if time() - self.run_start_time >= self.run_time * 60:
                self.trigger_switch_client.send('off')
                self.measured_run_time = time() - self.run_start_time
                self.trigger_switch_client.receive()

            res = self.dream_daq_client.receive()  # Wait for dream daq to finish
            if res != 'Dream DAQ stopped':
                print('Error stopping DAQ')
                return False

            if self.trigger_switch_client is None:  # Run time dictated by DREAM DAQ if no trigger switch
                self.measured_run_time = time() - self.run_start_time

        except KeyboardInterrupt:
            print('Keyboard interrupt. Stopping DAQ process.')
            if self.trigger_switch_client is not None:
                self.trigger_switch_client.send('off')
            if self.run_start_time is not None:
                self.measured_run_time = time() - self.run_start_time
            else:
                self.measured_run_time = 0
            if self.trigger_switch_client is not None:
                self.trigger_switch_client.receive()
            sleep(1)
            self.dream_daq_client.send('Stop')
            res = self.dream_daq_client.receive()
            if res != 'Dream DAQ stopped':
                print('Error stopping Dream DAQ')
        finally:
            if self.trigger_switch_client is not None:
                self.trigger_switch_client.silent = False

            if self.measured_run_time is None:
                if self.run_start_time is None:
                    self.measured_run_time = 0
                else:
                    self.measured_run_time = time() - self.run_start_time

            if run_successful:
                self.write_run_time()

        return run_successful

    def make_config_from_template(self):
        dest = self.run_directory if self.run_directory is not None else self.original_working_directory
        cfg_file_name = os.path.basename(self.cfg_template_file_path)
        self.cfg_file_path = f'{dest}/{cfg_file_name}'
        shutil.copy(self.cfg_template_file_path, self.cfg_file_path)

        # Copy all Grace* files from template directory to run directory
        template_dir = os.path.dirname(self.cfg_template_file_path)
        print(f'Copying Grace files from {template_dir} to {dest}')
        for file in os.listdir(template_dir):
            print(f'Found file: {file}')
            if file.startswith('Grace_'):
                print(f'Copying {file} to {dest}')
                shutil.copy(f'{template_dir}/{file}', f'{dest}/{file}')
        # input('Enter to continue...')

        with open(self.cfg_file_path, 'r') as file:
            cfg_lines = file.readlines()
        for i, line in enumerate(cfg_lines):
            if 'Sys DaqRun Time' in line:
                cfg_lines[i] = cfg_lines[i].replace('0', f'{self.cfg_file_run_time}')
            if self.zero_supress_mode and 'Sys DaqRun Mode' in line:
                cfg_lines[i] = cfg_lines[i].replace('Raw', 'ZS')
        with open(self.cfg_file_path, 'w') as file:
            file.writelines(cfg_lines)

    def write_run_time(self):
        with open(f'{self.out_directory}/run_time.txt', 'w') as file:
            out_str = ''
            if self.measured_run_time is not None:
                out_str += f'Run Time: {self.measured_run_time:.2f} seconds'
            if self.run_start_time is not None:
                out_str += f'\nRun Start Time: {self.run_start_time}'
            if out_str != '':
                file.write(out_str)
            else:
                file.write('None')


def move_data_files(src_dir, dest_dir):
    for file in os.listdir(src_dir):
        if file.endswith('.fdf'):
            # shutil.move(f'{src_dir}/{file}', f'{dest_dir}/{file}')
            # Copy for now, maybe move and clean up later when more confident
            shutil.copy(f'{src_dir}/{file}', f'{dest_dir}/{file}')

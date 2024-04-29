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
from time import time, sleep


class DAQController:
    def __init__(self, cfg_file_path, out_name=None, run_directory=None):
        self.run_directory = run_directory  # Relative to run_directory if not None
        self.original_working_directory = os.getcwd()

        self.max_run_time = 30  # minutes After this time assume stuck and kill

        if out_name is None:
            self.run_command = f'RunCtrl -c {cfg_file_path}'
        else:
            self.run_command = f'RunCtrl -c {cfg_file_path} -f {out_name}'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.original_working_directory)

    def run(self):
        if self.run_directory is not None:
            os.chdir(self.run_directory)
        process = Popen(self.run_command, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
        start = time()
        sent_go, sent_continue, run_successful = False, False, True
        while True:
            if sent_continue:
                sleep(1)
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                print('DAQ process finished.')
                break
            if not sent_go and output.strip() == '***':
                print(' Got the stars. Writing G.')
                process.stdin.write('G')
                process.stdin.flush()  # Ensure the command is sent immediately
                sent_go = True
            elif not sent_continue and 'Press C to Continue' in output.strip():
                print(' Got the continue. Writing C.')
                process.stdin.write('C')
                process.stdin.flush()
            if output.strip() != '':
                print(output.strip())
            if time() - start > self.max_run_time * 60:
                print('DAQ process timed out.')
                process.kill()
                run_successful = False
                break
        os.chdir(self.original_working_directory)

        return run_successful



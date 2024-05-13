#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 02 12:05 AM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/banco_daq_control.py

@author: Dylan Neff, Dylan
"""

import os
import shutil
from subprocess import Popen, PIPE
import signal
from datetime import datetime

from Server import Server
from common_functions import *

# from run_config import Config


def main():
    # config = Config()
    port = 1100
    # run_path = config.banco_daq_run_path
    with (Server(port=port) as server):
        server.receive()
        server.send('Banco DAQ control connected')
        banco_info = server.receive_json()
        run_path = banco_info['daq_run_path']
        temp_dir, out_dir = banco_info['data_temp_dir'], banco_info['data_out_dir']
        create_dir_if_not_exist(out_dir)

        res = server.receive()
        while 'Finished' not in res:
            if 'Start' in res:
                start_time = datetime.now()
                sub_run_name = res.split()[-1]
                sub_run_out_dir = f'{out_dir}{sub_run_name}/'
                create_dir_if_not_exist(sub_run_out_dir)
                sub_run_raw_out_dir = f'{sub_run_out_dir}{banco_info["data_inner_dir"]}/'
                create_dir_if_not_exist(sub_run_raw_out_dir)
                process = Popen(run_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
                server.send('Banco DAQ started')
                res = server.receive()
                while 'Stop' not in res:
                    server.send('Banco DAQ running! Need to stop it before anything else can be done!')
                    res = server.receive()
                os.kill(process.pid, signal.SIGINT)  # Send ctrl-c to stop banco_daq
                # process.stdin.write('q')  # Don't know signal to stop banco_daq!!!!!!!! FIX THIS
                # process.stdin.flush()
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        print('DAQ process finished.')
                        break
                end_time = datetime.now()
                move_data_files(temp_dir, sub_run_raw_out_dir, start_time, end_time)

                server.send('Banco DAQ stopped')
            else:
                server.send('Unknown Command')
            res = server.receive()
    print('donzo')


def move_data_files(src_dir, dest_dir, start_time, end_time):
    for file in os.listdir(src_dir):
        if file.endswith('.root') and '-chip' not in file:
            file_time = datetime.strptime('_'.join(file.split('_')[1:3]), '%y%m%d_%H%M%S')
            if start_time <= file_time <= end_time:
                # Copy file, maybe move and clean up later if confident
                shutil.copy(f'{src_dir}{file}', f'{dest_dir}{file}')


if __name__ == '__main__':
    main()

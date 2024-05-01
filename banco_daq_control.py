#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 02 12:05 AM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/banco_daq_control.py

@author: Dylan Neff, Dylan
"""

import os
from subprocess import Popen, PIPE
import signal

from Server import Server

from run_config import Config


def main():
    config = Config()
    port = 1100
    run_path = config.banco_daq_run_path
    with Server(port=port) as server:
        server.receive()
        server.send('Banco DAQ control connected')

        res = server.receive()
        while 'Finished' not in res:
            if 'Start' in res:
                process = Popen(run_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
                server.send('Banco DAQ started')
                res = server.receive()
                while 'Stop' not in res:
                    server.send('Banco DAQ running! Need to stop it before anything else can be done!')
                    res = server.receive()
                os.kill(process.pid, signal.SIGINT)  # Send ctrl-c to stop banco_daq
                # process.stdin.write('q')  # Don't know signal to stop banco_daq!!!!!!!! FIX THIS
                # process.stdin.flush()
                server.send('Banco DAQ stopped')
            else:
                server.send('Unknown Command')
            res = server.receive()
    print('donzo')


def create_dir_if_not_exist(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)


if __name__ == '__main__':
    main()

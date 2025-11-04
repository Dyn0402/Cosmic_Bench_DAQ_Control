#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 04 18:31 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/processor_runner

@author: Dylan Neff, dn277127
"""

import sys
from subprocess import Popen, PIPE
from Processor import *


def main():
    if len(sys.argv) != 3:
        print("Usage: python processor_runner.py decoder_port run_config_json_path")
        sys.exit(1)
    decoder_port = int(sys.argv[1])
    run_config_json_path = sys.argv[2]

    # Initialize processor with run config path
    processor = Processor(run_config_json_path)

    # Start on-the-fly processing
    processor.process_on_the_fly()

    # Wait till finished. Once so, kill first decoder_port tmux session and then own processor_port tmux.
    kill_tmux_session(f'decoder_{decoder_port}')
    kill_tmux_session(f'processor_{decoder_port}')  # Should be own session so process should die here!

    print('donzo')  # Should be unreachable!


def kill_tmux_session(session_name):
    """
    Kill tmux session of given name
    :param session_name:
    :return:
    """
    Popen('tmux kill-session -t ' + session_name, shell=True).wait()


if __name__ == '__main__':
    main()

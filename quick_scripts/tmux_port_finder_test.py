#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 04 18:54 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/tmux_port_finder_test

@author: Dylan Neff, dn277127
"""

from send_run_config_to_processor import get_open_decoder_port, start_tmux
from processor_runner import kill_tmux_session


def main():
    new_port = get_open_decoder_port()
    print(f'New port: {new_port}')
    start_tmux(f'decoder_{new_port}', 'python "processing_control.py"')
    start_tmux(f'processor_{new_port}')

    kill_tmux_session(f'decoder_{new_port - 1}')

    print('donzo')


if __name__ == '__main__':
    main()

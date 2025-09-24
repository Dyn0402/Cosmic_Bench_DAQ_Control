#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 14 20:00 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/processor_test

@author: Dylan Neff, dn277127
"""

from Processor import *


def main():
    processor = Processor('/local/home/dn277127/Bureau/beam_test_25/run_config_test.json')
    # processor = Processor('/mnt/cosmic_data/Run/rd542_strip_1_9-24-25/run_config.json')
    processor.config['save_fds'] = True

    processor.process_all()

    print('donzo')


if __name__ == '__main__':
    main()

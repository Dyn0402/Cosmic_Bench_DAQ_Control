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
    # processor = Processor('/local/home/dn277127/Bureau/beam_test_25/run_config_test.json')
    # processor = Processor('/mnt/cosmic_data/Run/rd542_strip_1_overnight_9-24-25/run_config.json')
    # processor = Processor('/mnt/cosmic_data/Run/rd542_strip_1_quick_tests_9-25-25/run_config.json')
    # processor = Processor('/mnt/cosmic_data/Run/rd542_strip_1_weekend_run_9-25-25/run_config.json')
    # processor = Processor('/mnt/cosmic_data/Run/rd542_plein_2_first_test_9-30-25/run_config.json')
    # processor = Processor('/mnt/cosmic_data/Run/rd542_plein_2_first_test_9-30-25/run_config.json')
    # processor = Processor('/mnt/cosmic_data/Run/rd542_strip_1_beam_test_test_9-30-25/run_config.json')
    # processor = Processor('/mnt/cosmic_data/Run/rd542_plein_3_first_test_10-2-25/run_config.json')
    # processor = Processor('/mnt/cosmic_data/Run/rd542_plein_3_first_test_10-2-25/run_config.json')
    processor = Processor('/mnt/cosmic_data/Run/beam_test_fe_zs_test_10-9-25/run_config.json')
    # processor = Processor('/mnt/cosmic_data/Run/zs_test_9-2-25/run_config.json')
    # processor.config['save_fds'] = True

    # processor.process_all()
    processor.process_on_the_fly()

    print('donzo')


if __name__ == '__main__':
    main()

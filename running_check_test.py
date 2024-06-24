#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on June 24 1:53 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/running_check_test.py

@author: Dylan Neff, Dylan
"""

from daq_control import file_num_still_running


def main():
    fdf_dir = '/home/clas12/dylan/Run/on_fly_test/'
    while True:
        running = file_num_still_running(fdf_dir, 0)
        print(f'File 0 running: {running}')
    print('donzo')


if __name__ == '__main__':
    main()

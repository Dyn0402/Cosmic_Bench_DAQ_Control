#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 11:48 AM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/daq_controller_test.py

@author: Dylan Neff, Dylan
"""

from DAQController import DAQController


def main():
    cfg_file_name = 'CosmicTb_TPOT.cfg'
    out_name = 'test_py_communication'
    run_dir = '/home/clas12/dylan/Run/remote_test_dir/'
    daq_controller = DAQController(cfg_file_name, out_name, run_dir)
    daq_controller.run()
    print('donzo')


if __name__ == '__main__':
    main()

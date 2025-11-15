#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 15 12:54 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/run_config_fixer

@author: Dylan Neff, dn277127
"""

# Add parent directory to sys.path to import run_config_beam
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt

from run_config_beam import Config


def main():
    base_path = '/mnt/data/beam_sps_25/Run/run_79'
    run_config_path = f'{base_path}/run_config.json'
    config = Config(run_config_path)
    print(config.included_detectors)
    print('donzo')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 13 4:44 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/common_functions.py

@author: Dylan Neff, Dylan
"""

import os


def create_dir_if_not_exist(dir_path):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
        os.chmod(dir_path, 0o777)


def get_date_from_fdf_file_name(file_name):
    """
    Get date from file name with format ...xxx_xxx_240212_11H42_000_01.xxx
    :param file_name:
    :return:
    """
    date_str = file_name.split('_')[-4] + ' ' + file_name.split('_')[-3]
    date = datetime.strptime(date_str, '%y%m%d %HH%M')
    return date


def get_feu_num_from_fdf_file_name(file_name):
    """
    Get fdf style feu number from file name with format ...xxx_xxx_240212_11H42_000_01.xxx
    :param file_name:
    :return:
    """
    fdf_num = int(file_name.split('_')[-1].split('.')[0])
    return fdf_num


def get_file_num_from_fdf_file_name(file_name):
    """
    Get fdf style file number from file name with format ...xxx_xxx_240212_11H42_000_01.xxx
    :param file_name:
    :return:
    """
    file_num = int(file_name.split('_')[-2])
    return file_num


def get_run_name_from_fdf_file_name(file_name):
    # Should work for fdfs, maybe other file types
    run_name = file_name[:file_name.rfind('_', 0, file_name.rfind('_'))].split('/')[-1]
    return run_name

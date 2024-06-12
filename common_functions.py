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


def get_file_num_from_fdf_file_name(file_name, num_index=-1):
    """
    Get fdf style file number from file name with format ...xxx_xxx_240212_11H42_000_01.xxx
    Updated to more robustly get first number from back.
    :param file_name:
    :param num_index:
    :return:
    """
    file_split = file_name.split('_')
    file_nums, check_index, split_len = [], -2, len(file_split)
    while check_index > -split_len:
        try:
            file_nums.append(int(file_split[check_index]))
        except ValueError:
            pass
        check_index -= 1
    num_index = abs(num_index) - 1
    if len(file_nums) < num_index + 1:
        return None
    return file_nums[num_index]


def get_run_name_from_fdf_file_name(file_name):
    file_name_split = file_name.split('_')
    # Find xxHxx in file name split
    run_name_end_index = 0
    for i, part in enumerate(file_name_split):
        print(f'{i}: {part}')
        if len(part) == 5 and part[2] == 'H' and is_convertible_to_int(part[:2]) and is_convertible_to_int(part[3:]):
            print(f'Found H flag: {i} {part}')
            run_name_end_index = i
            break
    run_name = '_'.join(file_name_split[:run_name_end_index + 1])
    return run_name


def is_convertible_to_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

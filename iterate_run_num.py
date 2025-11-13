#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on October 22 11:25 PM 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/iterate_run_num.py

@author: Dylan Neff, Dylan
"""

import sys
import os
import re

# RUNCONFIG_REL_PATH = "config/json_run_configs/"
from run_config_beam import Config
BASE_DIR = '/local/home/banco/dylan/Cosmic_Bench_DAQ_Control'
RUNCONFIG_PY_PATH = 'run_config_beam.py'


def main():
    # if len(sys.argv) != 2:
    #     print('No run config path given')
    #     return
    # config_path = os.path.join(RUNCONFIG_REL_PATH, sys.argv[1]) if not os.path.isabs(sys.argv[1]) else sys.argv[1]
    # config = Config(config_path)
    config = Config()

    # Check run_out_dir. If it exists, check if run_name has a _<number> suffix.
    # If so, increment the number until a non-existing directory is found. Else, add _1 suffix.
    # Then replace all occurrences of the old run_name string with the new one in the config.
    run_out_dir = config.run_out_dir
    run_name = config.run_name

    if os.path.exists(run_out_dir):
        base_run_name = run_name
        suffix_num = 1
        if '_' in run_name and run_name.split('_')[-1].isdigit():
            base_run_name = '_'.join(run_name.split('_')[:-1])
            suffix_num = int(run_name.split('_')[-1]) + 1

        new_run_name = f"{base_run_name}_{suffix_num}"
        new_full_run_path = os.path.join(run_out_dir, new_run_name)

        while os.path.exists(new_full_run_path):
            suffix_num += 1
            new_run_name = f"{base_run_name}_{suffix_num}"
            new_full_run_path = os.path.join(run_out_dir, new_run_name)

        # Open the original json config path file and update the run_name
        # with open(config_path, 'r') as f:
        #     config_json = f.read()
        # config_json = config_json.replace(run_name, new_run_name)  # Not very robust but works for now
        # with open(config_path, 'w') as f:
        #     f.write(config_json)
        # print(f"Updated run name to {new_run_name} in config.")

        # Open the original python config file and update the run_name
        py_path = os.path.join(BASE_DIR, RUNCONFIG_PY_PATH)
        update_run_number(py_path, suffix_num)

    print('donzo')


def update_run_number(file_path, new_run_number):
    """
    Updates the 'run_name' assignment in a Python config file.

    Args:
        file_path (str): Path to the Python config file.
        new_run_number (int): New run number to set, e.g. 64 for 'run_64'.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to match: self.run_name = 'run_63' (single or double quotes)
    new_run_name = f"run_{new_run_number}"
    new_line = f"self.run_name = '{new_run_name}'"
    updated_content, n = re.subn(
        r"self\.run_name\s*=\s*['\"]run_\d+['\"]",
        new_line,
        content
    )

    if n == 0:
        raise ValueError("No run_name line found to update in file.")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Updated run_name to '{new_run_name}' in {file_path}")


if __name__ == '__main__':
    main()

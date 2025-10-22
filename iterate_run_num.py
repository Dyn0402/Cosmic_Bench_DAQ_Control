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

RUNCONFIG_REL_PATH = "config/json_run_configs/"
from run_config import Config


def main():
    if len(sys.argv) != 2:
        print('No run config path given')
        return
    config_path = os.path.join(RUNCONFIG_REL_PATH, sys.argv[1]) if not os.path.isabs(sys.argv[1]) else sys.argv[1]
    config = Config(config_path)

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
        with open(config_path, 'r') as f:
            config_json = f.read()
        config_json = config_json.replace(f'"run_name": "{run_name}"', f'"run_name": "{new_run_name}"')
        with open(config_path, 'w') as f:
            f.write(config_json)
        print(f"Updated run name to {new_run_name} in config.")


    print('donzo')


if __name__ == '__main__':
    main()

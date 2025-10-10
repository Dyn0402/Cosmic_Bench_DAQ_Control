#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on October 10 9:45 PM 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/dream_cfg_templater.py

@author: Dylan Neff, Dylan
"""

import re
from pathlib import Path


def main():
    updates = {
        "Sys DaqRun Trig": "Slf",
        "Sys DaqRun Rate": "High",
        "Feu * Feu_RunCtrl_CM": 1,
        "Feu * DrmClk WrClk_Phase": 3,
    }

    update_config_value("C:/Users/Dylan/Desktop/test/CosmicTb_TPOT_test.cfg", updates)
    print('donzo')


def update_config_value(filepath, updates, output_path=None):
    """
    Updates parameters in a free-form config file without changing spacing/comments.

    Parameters
    ----------
    filepath : str or Path
        Path to the input config file.
    updates : dict
        Keys are full parameter flags (e.g., "Sys DaqRun Trig"),
        values are the new values to insert.
    output_path : str or Path, optional
        Where to save the updated file. Defaults to overwriting the original.
    """
    output_path = output_path or filepath
    with open(filepath, 'r') as f:
        lines = f.readlines()

    updates = {re.escape(k.strip()): str(v) for k, v in updates.items()}
    new_lines = []

    for line in lines:
        if re.match(r'^\s*#', line) or not line.strip():
            new_lines.append(line)
            continue

        for flag_pattern, new_value in updates.items():
            pattern = rf"^(\s*{flag_pattern}\s+)([^\s#]+)(?=(\s*#|$))"
            if re.search(pattern, line):
                # Use a lambda to avoid backreference confusion
                line = re.sub(pattern, lambda m: f"{m.group(1)}{new_value}", line)
                break

        new_lines.append(line)

    with open(output_path, 'w') as f:
        f.writelines(new_lines)


if __name__ == '__main__':
    main()

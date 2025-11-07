#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 07 02:18 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/make_dream_ped_cfg

@author: Dylan Neff, dn277127
"""

import shutil
import re


def main():
    cfg_dir = "/mnt/data/beam_sps_25/dream_run/config/"
    src_file = f"{cfg_dir}TbSPS25.cfg"
    dst_file = f"{cfg_dir}TbSPS25_ped.cfg"

    # Make a copy of the file first
    shutil.copy(src_file, dst_file)

    # Read and modify the new file
    with open(dst_file, "r") as f:
        lines = f.readlines()

    modified_lines = []
    for line in lines:
        # 1. Change "Sys Action PedThrRun 0" → "Sys Action PedThrRun 1"
        if re.match(r"^\s*Sys\s+Action\s+PedThrRun\s+0\b", line):
            line = re.sub(r"\b0\b", "1", line, count=1)

        # 2. Comment out Feu x Feu_RunCtrl_PdFile/ZsFile lines
        elif re.match(r"^\s*Feu\s+\d+\s+Feu_RunCtrl_(PdFile|ZsFile)\b", line):
            if not line.strip().startswith("#"):
                line = "# " + line  # add comment marker

        modified_lines.append(line)

    # Write the modified content back
    with open(dst_file, "w") as f:
        f.writelines(modified_lines)

    print(f"Created {dst_file} with modified PedThrRun and commented Feu *_PdFile/ZsFile lines.")

    print('donzo')


if __name__ == '__main__':
    main()

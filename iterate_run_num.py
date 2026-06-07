#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on October 22 11:25 PM 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/iterate_run_num.py

@author: Dylan Neff, Dylan
"""

import os
import re
from pathlib import Path

from run_config import Config

BASE_DIR = '/local/home/usernsw/Cosmic_Bench_DAQ_Control'
RUNCONFIG_PY = os.path.join(BASE_DIR, 'run_config.py')


def main():
    config = Config()
    run_name    = config.run_name
    run_out_dir = config.run_out_dir
    run_base_dir = str(Path(run_out_dir).parent)

    if not os.path.exists(run_out_dir):
        print(f"Run directory does not exist yet — no increment needed: {run_out_dir}")
        print('donzo')
        return

    print(f"Run output directory already exists: {run_out_dir}")

    # Strip a trailing _<number> suffix if present, then start from the next integer.
    # Uses _(\d+)$ so date-like suffixes (e.g. _06-07-26) are never stripped.
    m = re.match(r'^(.*?)_(\d+)$', run_name)
    if m:
        base_run_name = m.group(1)
        suffix_num    = int(m.group(2)) + 1
    else:
        base_run_name = run_name
        suffix_num    = 1

    new_run_name = f"{base_run_name}_{suffix_num}"
    while os.path.exists(os.path.join(run_base_dir, new_run_name)):
        print(f"  {new_run_name} also exists, trying next...")
        suffix_num  += 1
        new_run_name = f"{base_run_name}_{suffix_num}"

    print(f"Incrementing run_name: {run_name!r} -> {new_run_name!r}")
    update_run_name(RUNCONFIG_PY, new_run_name)
    print('donzo')


def update_run_name(file_path, new_run_name):
    """Replace the single uncommented self.run_name = '...' line in file_path."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match only lines where self.run_name is the first non-whitespace token
    # (i.e. not commented out).  Preserves indentation.
    updated, n = re.subn(
        r"^(\s*)self\.run_name\s*=\s*'[^']*'",
        lambda m: f"{m.group(1)}self.run_name = '{new_run_name}'",
        content,
        flags=re.MULTILINE,
    )

    if n == 0:
        raise ValueError(f"No uncommented self.run_name = '...' line found in {file_path}")
    if n > 1:
        raise ValueError(
            f"Found {n} uncommented self.run_name lines in {file_path} — expected exactly 1"
        )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"Updated run_name to {new_run_name!r} in {file_path}")


if __name__ == '__main__':
    main()

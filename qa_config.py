#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone QA watcher configuration for Cosmic Bench.
Edit the constants below, then run this script to regenerate config/qa_config.json.
The flask UI's Start QA Watcher button reads that JSON to launch qa_watcher.py.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_config import BASE_DATA_DIR

CONFIG = {
    # Top-level directory containing all run subdirectories
    'runs_dir': f'{BASE_DATA_DIR}Run/',

    # Subdirectory name for combined hits files (must match processor_config)
    'combined_hits_inner_dir': 'combined_hits_root',

    # QA file mode:
    #   'all'      — rerun QA with all accumulated files whenever a new one appears
    #   'first'    — run QA once per subrun using only file_num=0 (default, fast)
    #   'per_file' — independent QA plot set for each file_num
    'qa_file_mode': 'first',

    # Run filtering
    'include_runs': None,  # e.g. ['run_name_1', 'run_name_2'] — only process these; None = all
    'exclude_runs': None,  # e.g. ['pedestals_06-07-26_10-00-00'] — skip these

    # Watcher behavior
    'poll_interval':   10,  # seconds between scans
    'stale_run_days':   2,  # runs with no new combined_hits for this many days are skipped
    'memory_kill_pct': 80,  # kill the QA process if system RAM usage exceeds this %
}

if __name__ == '__main__':
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'qa_config.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(CONFIG, f, indent=4)
    print(f'Written: {out_path}')

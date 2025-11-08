#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 07 15:55 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/analyzer_control

@author: Dylan Neff
"""

import sys
import json
import os
import time
from subprocess import Popen


# ==== CONFIGURABLE PARAMETERS ====
CHECK_INTERVAL = 60              # seconds between checks for new data
POST_DIR_WAIT = 120              # seconds to wait after directory first appears
INACTIVITY_TIMEOUT_HOURS = 2     # exit if no new data for this long
# =================================


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyzer_control.py run_config_json_path")
        sys.exit(1)

    run_config_json_path = sys.argv[1]
    config = load_config(run_config_json_path)

    run_name = config["run_name"]
    run_out_dir = config["run_out_dir"]
    sub_runs = config["sub_runs"]
    included_detectors = config["included_detectors"]
    daq_type = "beam"

    timeout_seconds = INACTIVITY_TIMEOUT_HOURS * 3600
    last_activity_time = time.time()

    for sub_run in sub_runs:
        sub_run_name = sub_run["sub_run_name"]
        filtered_root_dir = os.path.join(run_out_dir, sub_run_name, "filtered_root")

        # Wait for filtered_root directory to appear or timeout
        while not os.path.exists(filtered_root_dir):
            if time.time() - last_activity_time > timeout_seconds:
                print(f"No new data for {INACTIVITY_TIMEOUT_HOURS} hours. Exiting gracefully.")
                sys.exit(0)
            print(f"Waiting for {filtered_root_dir} to appear...")
            time.sleep(CHECK_INTERVAL)

        print(f"{filtered_root_dir} found. Waiting {POST_DIR_WAIT} seconds for files to stabilize.")
        time.sleep(POST_DIR_WAIT)

        # Monitor for new files or changes
        prev_snapshot = get_dir_snapshot(filtered_root_dir)

        while True:
            time.sleep(CHECK_INTERVAL)
            new_snapshot = get_dir_snapshot(filtered_root_dir)

            if new_snapshot != prev_snapshot:
                print(f"New data detected in {filtered_root_dir}. Resetting inactivity timer.")
                last_activity_time = time.time()
                prev_snapshot = new_snapshot

                # Run online QA scripts for each detector
                for detector in included_detectors:
                    cmd = [
                        "python",
                        "online_qa_plots.py",
                        daq_type,
                        run_name,
                        sub_run_name,
                        detector,
                    ]
                    print(f"Running: {' '.join(cmd)}")
                    Popen(cmd, start_new_session=True)

            # Timeout check
            if time.time() - last_activity_time > timeout_seconds:
                print(f"No new data for {INACTIVITY_TIMEOUT_HOURS} hours. Exiting gracefully.")
                sys.exit(0)

    print("All sub-runs processed. Exiting normally.")


def load_config(path):
    with open(path, "r") as f:
        return json.load(f)


def get_dir_snapshot(directory):
    """Return a snapshot (dict) of {filename: mtime} for all files in the directory."""
    snapshot = {}
    for root, _, files in os.walk(directory):
        for f in files:
            fp = os.path.join(root, f)
            try:
                snapshot[fp] = os.path.getmtime(fp)
            except FileNotFoundError:
                pass  # file may have been deleted mid-scan
    return snapshot


if __name__ == "__main__":
    main()
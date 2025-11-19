#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 18 22:48 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/elog_updater

@author: Dylan Neff, dn277127
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update an existing ELOG entry based on a run config file.

Created on November 18, 2025
Author: Dylan Neff
"""

import sys
import json
import subprocess
import tempfile
import os
import numpy as np
import pandas as pd
from statistics import mode


# -------------------------------------------------------
# Utility to load config
# -------------------------------------------------------
def load_run_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)


# # -------------------------------------------------------
# # Determine the elog ID corresponding to a run
# # -------------------------------------------------------
# def find_elog_id_for_run(run_id):
#     """
#     Search the local ELOG for entries with the attribute RunID=<run_id>.
#     Returns the elog entry ID (string).
#     """
#
#     search_cmd = [
#         "elog",
#         "-h", "localhost",
#         "-p", "8080",
#         "-n", "2",
#         "-l", "SPS H4 2025",
#         "--search", f"RunID={run_id}",
#     ]
#
#     try:
#         result = subprocess.run(search_cmd, check=True, capture_output=True, text=True)
#         output = result.stdout.strip()
#
#     except subprocess.CalledProcessError as e:
#         print("Error running elog search!")
#         print("stdout:", e.stdout)
#         print("stderr:", e.stderr)
#         return None
#
#     if not output:
#         print(f"No elog entry found with RunID={run_id}")
#         return None
#
#     # ELOG search results look like:
#     #   12345: Title="Run_0253" RunID="253" ...
#     #   12346: Title="Run_0254" RunID="254" ...
#     #
#     # Extract IDs (before the colon)
#     ids = []
#     for line in output.splitlines():
#         line = line.strip()
#         if ":" in line:
#             entry_id = line.split(":", 1)[0].strip()
#             if entry_id.isdigit():
#                 ids.append(entry_id)
#
#     if len(ids) == 0:
#         print(f"No valid elog IDs found in search results for RunID={run_id}.")
#         return None
#
#     if len(ids) > 1:
#         print(f"Warning: Multiple elog entries found for RunID={run_id}: {ids}")
#         print("Returning the first one.")
#         return ids[0]
#
#     return ids[0]


def find_elog_id_for_run(run_id):
    """
    Search the local ELOG for entries with the attribute RunID=<run_id>
    using the old-style elog search (no --search).
    """

    search_cmd = [
        "elog",
        "-h", "localhost",
        "-p", "8080",
        "-n", "2",
        "-l", "SPS H4 2025",
        "-a", f"RunID={run_id}",
        "-m", ""    # empty text → search mode
    ]

    try:
        result = subprocess.run(search_cmd, check=True, capture_output=True, text=True)
        output = result.stdout.strip()

    except subprocess.CalledProcessError as e:
        print("Error running elog search!")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return None

    if not output:
        print(f"No elog entry found with RunID={run_id}")
        return None

    # Parse lines like: "12345: Title="Run_0138" RunID="138" ..."
    ids = []
    for line in output.splitlines():
        line = line.strip()
        if ":" in line:
            possible_id = line.split(":", 1)[0].strip()
            if possible_id.isdigit():
                ids.append(possible_id)

    if not ids:
        print(f"No valid elog entry IDs found for RunID={run_id}")
        return None

    if len(ids) > 1:
        print(f"Warning: Multiple ELOG entries match RunID={run_id}: {ids}")
        print("Using the first one.")

    return ids[0]



def get_total_dream_events_for_run(run_number,
                                   base_run_dir="/mnt/data/beam_sps_25/Run/",
                                   csv_name="daq_status_log.csv",
                                   event_col_name="dream_events"):
    """
    Computes the total number of dream events for an entire run by summing
    the max event count from each sub-run directory.

    Parameters
    ----------
    run_number : int or str
        The integer run number (e.g. 253) or string without the "run_" prefix.
    base_run_dir : str
        Base directory containing run_<N> directories.
    csv_name : str
        Name of the DAQ CSV file in each sub-run directory.
    event_col_name : str
        Column name containing the event counter.

    Returns
    -------
    int
        Total number of dream events from all sub-runs.
        Returns 0 if no valid sub-runs are found.
    """

    # --- Normalize run path ---
    run_number = str(run_number)
    run_dir = os.path.join(base_run_dir, f"run_{run_number}")

    if not os.path.isdir(run_dir):
        print(f"[WARN] Run directory not found: {run_dir}")
        return 0

    sub_run_times = []
    sub_run_events = []

    # --- Loop over sub-run directories ---
    for sub_run in os.listdir(run_dir):
        sub_path = os.path.join(run_dir, sub_run)
        if not os.path.isdir(sub_path):
            continue

        csv_path = os.path.join(sub_path, csv_name)
        if not os.path.isfile(csv_path):
            continue

        try:
            df = pd.read_csv(csv_path)
        except Exception:
            continue

        if event_col_name not in df.columns:
            continue

        max_events = df[event_col_name].max()

        # Track event + time so we can sort like original code
        sub_run_events.append(max_events)
        sub_run_times.append(os.path.getmtime(csv_path))

    if not sub_run_events:
        return 0

    # Sort in the same order as your script (by mtime)
    sorted_idx = np.argsort(sub_run_times)
    sorted_events = [sub_run_events[i] for i in sorted_idx]

    # --- Total ---
    return int(sum(sorted_events))


def infer_rotation_angle(run_config):
    """
    Look through included detectors whose names start with:
      - 'urw_'
      - 'asacusa_'
      - 'rd5_'
    Extract det_orientation['y'] for those detectors,
    return the most frequently occurring rotation angle.

    Returns:
        int or float rotation angle, or None if no matching detectors found.
    """

    prefixes = ("urw_", "asacusa_", "rd5_")

    included = set(run_config.get("included_detectors", []))
    detectors = run_config.get("detectors", [])

    rotation_values = []

    for det in detectors:
        name = det.get("name", "")

        # must be included AND start with one of the prefixes
        if name not in included:
            continue
        if not name.startswith(prefixes):
            continue

        # extract rotation angle in "y"
        orientation = det.get("det_orientation", {})
        if "y" in orientation:
            rotation_values.append(orientation["y"])

    if not rotation_values:
        return None

    # get the most common rotation value
    try:
        return mode(rotation_values)
    except Exception:
        # if multimodal, choose the smallest or first?
        # Default: choose the first value encountered
        return rotation_values[0]


# -------------------------------------------------------
# Build dictionary of updated attributes
# -------------------------------------------------------
def build_attribute_updates(run_config):
    """
    Edit/fill this dict with the attributes you want to update.
    Keys must match ELOG attribute names.
    """
    run_id = int(run_config['run_name'].split('_')[1])

    updates = {
        # EXAMPLES (delete or modify these)
        'Gas': run_config['gas'],
        'HBanco': run_config['bench_geometry']['banco_moveable_y_position'],
        'BeamInfo': run_config.get('beam_type', 'muons'),
        'StartTime': run_config.get('start_time', ''),
        'Sampling': run_config['dream_daq_info'].get('sampling_period', '60'),
        'Angle': infer_rotation_angle(run_config) or 0,
    }

    return updates


def get_n_triggers(run_config):
    pass


# -------------------------------------------------------
# Send ELOG update
# -------------------------------------------------------
def submit_elog_update(log_id, attributes, message_text=None):
    elog_cmd = [
        "elog",
        "-h", "localhost",
        "-p", "8080",
        "-n", "2",
        "-l", "SPS H4 2025",
        "-e", str(log_id),  # Edit mode
    ]

    # Add all -a key=value attributes
    for key, value in attributes.items():
        elog_cmd.extend(["-a", f"{key}={value}"])

    tmp_msg_path = None

    # Optional message update
    if message_text:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as tmp:
            tmp.write(message_text)
            tmp_msg_path = tmp.name
        elog_cmd.extend(["-m", tmp_msg_path])

    print("Running:", " ".join(elog_cmd))

    try:
        result = subprocess.run(elog_cmd, check=True, capture_output=True, text=True)
        print("ELOG updated successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error updating ELOG entry!")
        print("Stdout:", e.stdout)
        print("Stderr:", e.stderr)
    finally:
        if tmp_msg_path and os.path.exists(tmp_msg_path):
            os.remove(tmp_msg_path)


# -------------------------------------------------------
# Main
# -------------------------------------------------------
def main():
    out_run_dir = '/mnt/data/beam_sps_25/Run/'
    if len(sys.argv) != 2:
        print("Usage: python elog_update_from_config.py <run_num>")
        sys.exit(1)

    run_num = sys.argv[1]

    print(f"Processing run number: {run_num}")
    elog_entry = find_elog_id_for_run(run_num)
    if elog_entry is None:
        print("Error: ELOG ID lookup failed.")
        sys.exit(1)
    print(f"Found ELOG entry ID: {elog_entry}")
    # config_path = os.path.join(out_run_dir, f'run_{run_num}', 'run_config.json')
    #
    # # Load JSON
    # run_config = load_run_config(config_path)
    # run_id = int(run_config['run_name'].split('_')[1])
    #
    # log_id = find_elog_id_for_run(run_id)
    # if log_id is None:
    #     print("Error: elog ID lookup failed.")
    #     sys.exit(1)
    #
    # # Build updates
    # attributes = build_attribute_updates(run_config)
    #
    # # Submit update
    # submit_elog_update(log_id, attributes)


if __name__ == "__main__":
    main()

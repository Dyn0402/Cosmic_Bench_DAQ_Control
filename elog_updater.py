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
import re
import numpy as np
import pandas as pd
from statistics import mode

from get_run_events import get_total_events_for_run


# -------------------------------------------------------
# Utility to load config
# -------------------------------------------------------
def load_run_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)


def find_elog_id_for_run(run_id, logbook="SPS H4 2025", host="localhost", port="8080",
                         encoding_flag="-n", encoding_val="2", max_lookback=5000):
    """
    Find an elog entry id corresponding to RunID=<run_id>.

    Strategy (tries in order):
      1. New-style search (--search) if available.
      2. Old-style attribute-search: `-a RunID=<run_id> -m ""` (may fail on some elog clients).
      3. Sequential scan: download the "last" entry to discover the latest id,
         then iterate backward and `-w <id>` each entry looking for RunID or a Title run_<N>.

    Returns:
      string elog id (e.g. "12345") or None if not found.
    """

    base_common = ["elog", "-h", host, "-p", port, encoding_flag, encoding_val, "-l", logbook]

    # --- Helper: run a command and return (success, stdout, stderr) ---
    def run_cmd(cmd):
        try:
            r = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, r.stdout, r.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout or "", e.stderr or ""

    # --- 1) Try new-style --search if available ---
    try_search_cmd = base_common + ["--search", f"RunID={run_id}"]
    ok, out, err = run_cmd(try_search_cmd)
    if ok and out.strip():
        ids = _parse_ids_from_elog_search_output(out)
        if ids:
            if len(ids) > 1:
                print(f"Warning: multiple matches for RunID={run_id}: {ids}; using first.")
            return ids[0]

    # --- 2) Try old-style attribute search with empty message (some elog versions use this) ---
    old_style_cmd = base_common + ["-a", f"RunID={run_id}", "-m", ""]
    ok, out, err = run_cmd(old_style_cmd)
    # If successful and produced output, try to parse it.
    if ok and out.strip():
        ids = _parse_ids_from_elog_search_output(out)
        if ids:
            if len(ids) > 1:
                print(f"Warning: multiple matches for RunID={run_id}: {ids}; using first.")
            return ids[0]
    # If it failed and stderr indicated missing Title, fall through to scan.
    if not ok and ("Missing required attribute" in (err or "") or "Missing required attribute" in (out or "")):
        # fall through to sequential scan
        pass
    else:
        # If it failed for some other reason (eg. --search not recognized), keep going to fallback
        pass

    # --- 3) Sequential scan fallback ---
    # Get the latest entry via "-w last"
    ok, out, err = run_cmd(base_common + ["-w", "last"])
    if not ok:
        # Could not retrieve last entry; give up
        print("Could not fetch 'last' entry from elog; aborting search fallback.")
        if out or err:
            print("elog stdout/stderr:", out, err)
        return None

    # Try to parse an id number from the 'last' output
    last_id = _parse_id_from_elog_download(out)
    if last_id is None:
        # If we couldn't parse id from output, attempt a few heuristic patterns in stderr too
        last_id = _parse_id_from_elog_download(err)
    if last_id is None:
        print("Unable to determine the latest elog entry ID from 'elog -w last' output.")
        # Optionally print sample output for debugging
        # print("Sample output:\n", out)
        return None

    last_id = int(last_id)
    lower_bound = max(1, last_id - int(max_lookback))

    # iterate from last_id downwards
    # We look for either:
    #   - RunID=<run_id> somewhere in the entry text (RunID="138", RunID=138)
    #   - Title containing run_<run_id> (Title="run_138" or similar)
    runid_regexes = [
        re.compile(r'\bRunID\s*=\s*"?{}"?\b'.format(re.escape(str(run_id)))),
        re.compile(r'\bRunID\s*[:=]\s*"?{}"?\b'.format(re.escape(str(run_id)))),
        re.compile(r'Title\s*=\s*"?run_{}"?'.format(re.escape(str(run_id))), re.IGNORECASE),
        re.compile(r'\brun[_-]?{}[\b"_]'.format(re.escape(str(run_id))), re.IGNORECASE),
    ]

    for candidate in range(last_id, lower_bound - 1, -1):
        ok, out, err = run_cmd(base_common + ["-w", str(candidate)])
        if not ok:
            # skip missing/forbidden ids
            continue

        combined_text = (out or "") + "\n" + (err or "")

        # quick check for run id
        for rx in runid_regexes:
            if rx.search(combined_text):
                return str(candidate)

    # nothing found
    print(f"No ELOG entry found with RunID={run_id} in last {max_lookback} entries (scanned {last_id}-{lower_bound}).")
    return None


# -------------------------
# Helper parsing functions
# -------------------------
def _parse_ids_from_elog_search_output(output_text):
    """
    Parse lines like:
      12345: Title="Run_0138" RunID="138" ...
    or other similar formats; return list of numeric ids as strings.
    """
    ids = []
    for line in output_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # If line begins with digits followed by colon, take that as id
        m = re.match(r'^(\d+)\s*:', line)
        if m:
            ids.append(m.group(1))
            continue
        # Sometimes the output contains 'Entry <id>' or 'Message <id>'
        m = re.search(r'\b(?:Entry|Message|ID)\s*[:=]?\s*(\d{3,})\b', line, re.IGNORECASE)
        if m:
            ids.append(m.group(1))
    return ids

def _parse_id_from_elog_download(text):
    """
    Parse elog entry ID from the output of `elog -w <id>` or `elog -w last`
    for elog installations that print the ID using the format:
        $@MID@$: 231
    """
    if not text:
        return None

    # Preferred pattern: $@MID@$: <number>
    m = re.search(r'\$@MID@\$\s*:\s*(\d+)', text)
    if m:
        return m.group(1)

    # Fallback pattern: a line beginning with digits + colon (rare on your system)
    m = re.search(r'^(\d+)\s*:', text, flags=re.MULTILINE)
    if m:
        return m.group(1)

    # Fallback: "ID: 123"
    m = re.search(r'\bID\s*:\s*(\d+)\b', text)
    if m:
        return m.group(1)

    return None


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
    run_id = run_config['run_name'].split('_')[1]

    updates = {
        'Gas': run_config['gas'],
        'HBanco': run_config['bench_geometry']['banco_moveable_y_position'],
        'BeamInfo': run_config.get('beam_type', 'muons'),
        'StartTime': run_config.get('start_time', ''),
        'Sampling': run_config['dream_daq_info'].get('sampling_period', '60'),
        'Angle': infer_rotation_angle(run_config) or 0,
        'Ntrigger': get_total_dream_events_for_run(run_id, base_run_dir=run_config['run_out_dir']),
    }

    return updates


# def get_total_events_for_run(run_dir, run_number, csv_name="daq_status_log.csv", event_col="dream_events"):
#     """
#     Given the base run directory (e.g. '/mnt/data/beam_sps_25/Run/')
#     and the run number (e.g. 160),
#     return the total number of Dream events across all subruns.
#     """
#
#     # Format like "run_160"
#     run_name = f"run_{run_number}"
#     run_path = os.path.join(run_dir, run_name)
#
#     if not os.path.exists(run_path):
#         raise FileNotFoundError(f"Run directory does not exist: {run_path}")
#
#     total_events = 0
#     subrun_event_counts = {}  # optional: return per-subrun details if needed
#
#     # Loop over subruns
#     for subrun in os.listdir(run_path):
#         subrun_path = os.path.join(run_path, subrun)
#
#         if not os.path.isdir(subrun_path):
#             continue
#
#         csv_path = os.path.join(subrun_path, csv_name)
#         if not os.path.exists(csv_path):
#             continue
#
#         try:
#             df = pd.read_csv(csv_path)
#
#             if event_col not in df.columns:
#                 continue
#
#             max_events = df[event_col].max()
#             if pd.notna(max_events):
#                 total_events += int(max_events)
#                 subrun_event_counts[subrun] = int(max_events)
#
#         except Exception as e:
#             print(f"Warning: failed reading {csv_path}: {e}")
#
#     return total_events, subrun_event_counts


# -------------------------------------------------------
# Send ELOG update
# -------------------------------------------------------
def submit_elog_update(log_id, attributes, message_text=None):
    # Base command
    elog_cmd = [
        "elog",
        "-h", "localhost",
        "-p", "8080",
        "-n", "2",
        "-l", "SPS H4 2025",
        "-e", str(log_id),
    ]

    # Add attribute arguments
    for key, value in attributes.items():
        value_str = str(value)
        elog_cmd.extend(["-a", f'"{key}={value_str}"'])

    tmp_msg_path = None

    # Optional message
    if message_text:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as tmp:
            tmp.write(message_text)
            tmp_msg_path = tmp.name
        elog_cmd.extend(["-m", tmp_msg_path])

    print("Running:", " ".join(elog_cmd))

    # Run actual command (NO quoting here!)
    try:
        result = subprocess.run(
            elog_cmd,
            check=True,
            capture_output=True,
            text=True
        )
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
    run_nums = []
    if len(sys.argv) >= 2:
        run_nums = [sys.argv[1]]
    if len(sys.argv) >= 3:
        run_nums = list(range(int(sys.argv[1]), int(sys.argv[2]) + 1))
    else:
        print("Usage: python elog_update_from_config.py <run_num> [end_run_num]")
        sys.exit(1)

    for run_num in run_nums:
        try:
            config_path = os.path.join(out_run_dir, f'run_{run_num}', 'run_config.json')

            # Load JSON
            run_config = load_run_config(config_path)
            run_id = int(run_config['run_name'].split('_')[1])

            log_id = find_elog_id_for_run(run_id)
            if log_id is None:
                print("Error: elog ID lookup failed.")
                sys.exit(1)

            # Build updates
            attributes = build_attribute_updates(run_config)

            # Submit update
            submit_elog_update(log_id, attributes)
        except Exception as e:
            print(f"Error processing run {run_num}: {e}")
            continue


if __name__ == "__main__":
    main()

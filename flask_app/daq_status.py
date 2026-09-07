#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 29 9:36 PM 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/daq_status.py

@author: Dylan Neff, Dylan
"""

import subprocess
import re


""" Colors:
- danger (red)
- warning (yellow)
- success (green)
- info (blue)
- primary (dark blue)
- secondary (grey)
- light (light grey)
- dark (black)
"""

# Live Dream DAQ event count, updated by get_dream_daq_status() on every poll and
# read by get_live_dream_daq_event_count() (e.g. from /get_run_events) without
# triggering another tmux capture. "count" tracks the current subrun's live
# nb_of_events (DREAM restarts this counter each subrun, so it can go down across
# subruns). "taking_data" is True only while the pane is showing "_TakeData:", so
# the live count is treated as valid only during a data-taking phase.
_live_events = {"count": 0, "taking_data": False}


def get_dream_daq_status():
    try:
        output = subprocess.check_output(
            ["tmux", "capture-pane", "-pS", "-500", "-t", "dream_daq:0.0"],
            text=True
        )
    except subprocess.CalledProcessError:
        _live_events["taking_data"] = False
        return {
            "status": "ERROR",
            "color": "danger",
            "fields": [{"label": "Details", "value": "dream_daq tmux not running"}]
        }

    fields = []
    if "_TakePedThr" in output:
        status = "Taking Pedestals"
        color = "warning"
        _live_events["taking_data"] = False
    elif "Scan trigger thresholds in process" in output:
        status = "Scanning Trigger Thresholds"
        color = "warning"
        _live_events["taking_data"] = False
    elif "_TakeData:" in output:
        status = "RUNNING"
        color = "success"
        m_rt = re.search(r"RunTime\s+(\d+h\s+\d+m\s+\d+s)", output)
        if m_rt: fields.append({"label": "Run Time", "value": m_rt.group(1)})

        m_ir = re.search(r"IntRate=\s*([\d.]+\s*[A-Za-z]+)", output)
        if m_ir: fields.append({"label": "Int Rate", "value": m_ir.group(1)})

        # Report the current subrun's live nb_of_events directly. DREAM restarts
        # this counter at the start of every subrun, so a high-water-mark/max()
        # across the data-taking phase would freeze the display at the first
        # subrun's peak (the "_TakeData:" substring lingers in the 500-line
        # scrollback between subruns, so the phase never resets). The live status
        # line updates in place, so the current regex match is the reliable value.
        m_ev = re.search(r"nb_of_events=(\d+)", output)
        if m_ev:
            _live_events["count"] = int(m_ev.group(1))
            _live_events["taking_data"] = True
        if _live_events["taking_data"]:
            fields.append({"label": "Events", "value": str(_live_events["count"])})

        # m_wait = re.search(
        #     r"wait for\s*((?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)?)", output
        # )
        # if m_wait:
        #     h, m, s = m_wait.groups()
        #     # Fill in missing values as 0
        #     h = h or "0"
        #     m = m or "0"
        #     s = s or "0"
        #     fields.append({"label": "Wait For", "value": f"{h}h {m}m {s}s"})
    elif "Listening on " in output:
        status = "WAITING"
        color = "secondary"
        _live_events["taking_data"] = False
    elif "Signaling on-the-fly copier to finish soon" in output:
        status = "Copying fdfs"
        color = "info"
        _live_events["taking_data"] = False
    elif "Sent: Dream DAQ stopped" in output:
        status = "DAQ Stopped"
        color = "info"
        _live_events["taking_data"] = False
    else:
        status = "UNKNOWN STATE"
        color = "danger"
        _live_events["taking_data"] = False

    return {"status": status, "color": color, "fields": fields}


def get_live_dream_daq_event_count():
    """
    Cached live event count for the in-progress data-taking phase (updated by
    get_dream_daq_status() on each poll), or None if Dream DAQ is not currently
    taking data.
    """
    return _live_events["count"] if _live_events["taking_data"] else None


def get_hv_control_status():
    try:
        output = subprocess.check_output(
            ["tmux", "capture-pane", "-pS", "-50", "-t", "hv_control:0.0"],
            text=True
        )
    except subprocess.CalledProcessError:
        return {
            "status": "ERROR",
            "color": "danger",
            "fields": [{"label": "Details", "value": "hv_control tmux not running"}]
        }

    # Default status/color rules
    rules = [
        ("Listening on ", "WAITING", "secondary"),
        ("Powering off HV", "HV Off", "secondary"),
        ("HV Powered Off", "HV Off", "secondary"),
        ("Monitoring HV", "Monitoring HV", "success"),
        ("HV Ramped", "HV Ramped", "success"),
        ("Setting HV", "Ramping HV", "warning"),
        ("Checking HV ramp", "Ramping HV", "warning"),
        ("Waiting for HV to ramp", "Ramping HV", "warning"),
    ]

    # Determine overall status/color from most recent matching line
    status, color = "UNKNOWN STATE", "danger"
    for line in reversed(output.splitlines()):
        for flag, s, c in rules:
            if flag in line:
                status, color = s, c
                break
        if status != "UNKNOWN STATE":
            break

    # Parse individual channel lines in the last block
    fields = []

    return {"status": status, "color": color, "fields": fields}



def get_daq_control_status():
    try:
        # -J joins wrapped lines so the long single-line [status] entry (which can
        # exceed the 80-col pane width once run+subrun names are long) is matched
        # by the run/subrun/run_time regex below instead of being split across rows.
        output = subprocess.check_output(
            ["tmux", "capture-pane", "-pJS", "-50", "-t", "daq_control:0.0"],
            text=True
        )
    except subprocess.CalledProcessError:
        return {
            "status": "ERROR",
            "color": "danger",
            "fields": [{"label": "Details", "value": "daq_control tmux not running"}]
        }

    rules = [
        ("Daq control session started",  "WAITING",          "secondary"),
        ("Run complete",                 "Run Complete",     "info"),
        ("donzo",                        "Run Complete",     "info"),
        ("Finished with sub run ",       "Finished Sub Run", "warning"),
        ("Dream DAQ taking pedestals",   "Prepping DAQs",    "warning"),
        ("Prepping DAQs for ",           "Prepping DAQs",    "warning"),
        ("Ramping HVs for ",             "Ramping HV",       "warning"),
        ("Starting DAQ Control",         "STARTING",         "warning"),
        ("Dream DAQ starting",           "RUNNING",          "success"),
        ("Stopping DAQ process",         "Stopping DAQ",     "warning"),
    ]

    fields = []
    for line in reversed(output.splitlines()):
        m = re.search(r'\[status\] run=(\S+)\s+subrun=(\S+)\s+run_time=(\S+)', line)
        if m:
            fields.append({"label": "Run",     "value": m.group(1)})
            fields.append({"label": "Subrun",  "value": m.group(2)})
            fields.append({"label": "Run Time", "value": m.group(3)})
            break

    for line in reversed(output.splitlines()):
        for flag, status, color in rules:
            if flag in line:
                return {"status": status, "color": color, "fields": fields}

    return {"status": "UNKNOWN STATE", "color": "danger", "fields": fields}


def get_processor_status():
    try:
        output = subprocess.check_output(
            ["tmux", "capture-pane", "-pS", "-50", "-t", "processor:0.0"],
            text=True
        )
    except subprocess.CalledProcessError:
        return {"status": "NOT RUNNING", "color": "secondary", "fields": []}

    rules = [
        ("[watcher] Done.",       "DONE",       "info"),
        ("[watcher] Timeout:",    "TIMED OUT",  "warning"),
        ("[m3_track]",            "PROCESSING", "success"),
        ("[m3_filter]",           "PROCESSING", "success"),
        ("[combine]",             "PROCESSING", "success"),
        ("[analyze]",             "PROCESSING", "success"),
        ("[decode]",              "PROCESSING", "success"),
        ("[watcher] Sleeping",    "IDLE",        "info"),
        ("[watcher] runs_dir",    "STARTING",   "warning"),
    ]

    fields = []
    for line in reversed(output.splitlines()):
        m = re.search(r'(\S+/\S+)\s+file_num=(\d+)', line)
        if m and not fields:
            fields = [
                {"label": "Last subrun",   "value": m.group(1).split('/')[-1]},
                {"label": "Last file_num", "value": m.group(2)},
            ]
        for flag, status, color in rules:
            if flag in line:
                return {"status": status, "color": color, "fields": fields}

    return {"status": "UNKNOWN", "color": "secondary", "fields": fields}


def get_qa_watcher_status():
    try:
        output = subprocess.check_output(
            ["tmux", "capture-pane", "-pS", "-50", "-t", "qa_watcher:0.0"],
            text=True
        )
    except subprocess.CalledProcessError:
        return {"status": "STOPPED", "color": "secondary", "fields": []}

    lines = [l for l in output.splitlines() if l.strip()]

    fields = []
    for line in reversed(lines):
        m = re.search(r'\[qa_watcher\] (\S+)/(\S+)', line)
        if m and 'idle' not in line and 'Marked stale' not in line \
                and 'waiting' not in line and 'runs_dir' not in line:
            fields = [
                {"label": "Run",    "value": m.group(1)},
                {"label": "Subrun", "value": m.group(2)},
            ]
            break

    _noise = ("[qa_watcher] Marked stale",)
    for line in reversed(lines):
        if any(n in line for n in _noise):
            continue
        m = re.search(r'\[qa\] (\S+) —', line)
        if m:
            return {"status": "Running QA",  "color": "success", "fields": fields + [{"label": "Detector", "value": m.group(1)}]}
        if "[qa_watcher]" in line and " idle " in line:
            return {"status": "IDLE",        "color": "info",    "fields": fields}
        if "[qa_watcher]" in line and "waiting for runs_dir" in line:
            return {"status": "Waiting for Dir", "color": "warning", "fields": []}
        if "[qa_watcher]" in line:
            return {"status": "RUNNING",     "color": "info",    "fields": fields}

    return {"status": "UNKNOWN", "color": "danger", "fields": []}

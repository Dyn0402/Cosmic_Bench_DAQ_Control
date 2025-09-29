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

def get_dream_daq_status():
    try:
        output = subprocess.check_output(
            ["tmux", "capture-pane", "-pS", "-500", "-t", "dream_daq:0.0"],
            text=True
        )
    except subprocess.CalledProcessError:
        return {
            "status": "ERROR",
            "color": "danger",
            "fields": [{"label": "Details", "value": "dream_daq tmux not running"}]
        }

    fields = []
    if "_TakePedThr" in output:
        status = "Taking Pedestals"
        color = "warning"
    elif "_TakeData:" in output:
        status = "RUNNING"
        color = "success"
        m_rt = re.search(r"RunTime\s+(\d+h\s+\d+m\s+\d+s)", output)
        if m_rt: fields.append({"label": "Run Time", "value": m_rt.group(1)})

        m_ir = re.search(r"IntRate=\s*([\d.]+\s*[A-Za-z]+)", output)
        if m_ir: fields.append({"label": "Int Rate", "value": m_ir.group(1)})

        m_ev = re.search(r"nb_of_events=(\d+)", output)
        if m_ev: fields.append({"label": "Events", "value": m_ev.group(1)})

        m_wait = re.search(r"wait for\s+(\d+h\s+\d+s)", output)
        if m_wait: fields.append({"label": "Wait For", "value": m_wait.group(1)})
    elif "Listening on " in output:
        status = "WAITING"
        color = "secondary"
    else:
        status = "UNKNOWN STATE"
        color = "danger"

    return {"status": status, "color": color, "fields": fields}


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

    fields = []
    if "Listening on " in output:
        status = "WAITING"
        color = "secondary"
    elif "Powering off HV" in output or "HV Powered Off" in output:
        status = "HV Off"
        color = "secondary"
    elif "Monitoring HV " in output:
        status = "Monitoring HV"
        color = "success"
    elif "HV Ramped" in output:
        status = "HV Ramped"
        color = "success"
    elif "Setting HV" in output or "Checking HV ramp" in output or "Waiting for HV to ramp" in output:
        status = "Ramping HV"
        color = "warning"
    else:
        status = "UNKNOWN STATE"
        color = "danger"

    return {"status": status, "color": color, "fields": fields}


def get_daq_control_status():
    try:
        output = subprocess.check_output(
            ["tmux", "capture-pane", "-pS", "-10", "-t", "daq_control:0.0"],
            text=True
        )
    except subprocess.CalledProcessError:
        return {
            "status": "ERROR",
            "color": "danger",
            "fields": [{"label": "Details", "value": "daq_control tmux not running"}]
        }

    fields = []
    if "Run complete" in output or "donzo" in output:
        status = "Run Complete"
        color = "info"
    elif "Finished with sub run " in output:
        status = "Finished Sub Run"
        color = "warning"
    elif "Prepping DAQs for " in output:
        status = "Prepping DAQs"
        color = "warning"
    elif "Ramping HVs for " in output:
        status = "Ramping HV"
        color = "warning"
    elif "Starting DAQ Control" in output:
        status = "STARTING"
        color = "warning"
    else:
        status = "UNKNOWN STATE"
        color = "danger"

    return {"status": status, "color": color, "fields": fields}


# def get_dream_daq_status():
#     try:
#         output = subprocess.check_output(
#             ["tmux", "capture-pane", "-pS", "-500", "-t", "dream_daq:0.0"],
#             text=True
#         )
#     except subprocess.CalledProcessError:
#         return {"status": "error", "details": "dream_daq not running"}
#
#     status = {"status": "waiting"}  # default
#
#     # Detect pedestal taking
#     if "TakePedThr= On" in output:
#         status["status"] = "taking pedestals"
#
#     # Detect data taking
#     if "TakeData= On" in output:
#         status["status"] = "taking data"
#
#         # Extract RunTime
#         match_runtime = re.search(r"RunTime\s+(\d+h\s+\d+m\s+\d+s)", output)
#         if match_runtime:
#             status["runtime"] = match_runtime.group(1)
#
#         # Extract nb_of_events
#         match_events = re.search(r"nb_of_events=(\d+)", output)
#         if match_events:
#             status["events"] = int(match_events.group(1))
#
#         # Extract wait for time
#         match_wait = re.search(r"wait for\s+(\d+h\s+\d+s)", output)
#         if match_wait:
#             status["wait_for"] = match_wait.group(1)
#
#     return status


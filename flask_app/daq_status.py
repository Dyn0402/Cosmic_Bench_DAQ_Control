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

    # define your rules once, ordered by priority
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

    # scan bottom-to-top for the most recent matching line
    for line in reversed(output.splitlines()):
        for flag, status, color in rules:
            if flag in line:
                return {"status": status, "color": color, "fields": []}

    # fallback if nothing matched
    return {"status": "UNKNOWN STATE", "color": "danger", "fields": []}


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

    rules = [
        ("Run complete", "Run Complete", "info"),
        ("donzo", "Run Complete", "info"),
        ("Finished with sub run ", "Finished Sub Run", "warning"),
        ("Prepping DAQs for ", "Prepping DAQs", "warning"),
        ("Ramping HVs for ", "Ramping HV", "warning"),
        ("Starting DAQ Control", "STARTING", "warning"),
    ]

    for line in reversed(output.splitlines()):
        for flag, status, color in rules:
            if flag in line:
                return {"status": status, "color": color, "fields": []}

    return {"status": "UNKNOWN STATE", "color": "danger", "fields": []}


def get_trigger_control_status():
    try:
        output = subprocess.check_output(
            ["tmux", "capture-pane", "-pS", "-10", "-t", "trigger_control:0.0"],
            text=True
        )
    except subprocess.CalledProcessError:
        return {
            "status": "ERROR",
            "color": "danger",
            "fields": [{"label": "Details", "value": "trigger_control tmux not running"}]
        }

    rules = [
        ("Trigger switch turned on'", "Configured", "success"),
        ("Trigger switch turned off", "Configuring", "warning"),
        ("Trigger switch control connected", "STARTING", "warning"),
        ("Listening on ", "WAITING", "secondary"),
    ]

    for line in reversed(output.splitlines()):
        for flag, status, color in rules:
            if flag in line:
                return {"status": status, "color": color, "fields": []}

    return {"status": "UNKNOWN STATE", "color": "danger", "fields": []}


# def get_hv_control_status():
#     try:
#         output = subprocess.check_output(
#             ["tmux", "capture-pane", "-pS", "-50", "-t", "hv_control:0.0"],
#             text=True
#         )
#     except subprocess.CalledProcessError:
#         return {
#             "status": "ERROR",
#             "color": "danger",
#             "fields": [{"label": "Details", "value": "hv_control tmux not running"}]
#         }
#
#     fields = []
#     if "Listening on " in output:
#         status = "WAITING"
#         color = "secondary"
#     elif "Powering off HV" in output or "HV Powered Off" in output:
#         status = "HV Off"
#         color = "secondary"
#     elif "Monitoring HV " in output:
#         status = "Monitoring HV"
#         color = "success"
#     elif "HV Ramped" in output:
#         status = "HV Ramped"
#         color = "success"
#     elif "Setting HV" in output or "Checking HV ramp" in output or "Waiting for HV to ramp" in output:
#         status = "Ramping HV"
#         color = "warning"
#     else:
#         status = "UNKNOWN STATE"
#         color = "danger"
#
#     return {"status": status, "color": color, "fields": fields}


# def get_daq_control_status():
#     try:
#         output = subprocess.check_output(
#             ["tmux", "capture-pane", "-pS", "-10", "-t", "daq_control:0.0"],
#             text=True
#         )
#     except subprocess.CalledProcessError:
#         return {
#             "status": "ERROR",
#             "color": "danger",
#             "fields": [{"label": "Details", "value": "daq_control tmux not running"}]
#         }
#
#     fields = []
#     if "Run complete" in output or "donzo" in output:
#         status = "Run Complete"
#         color = "info"
#     elif "Finished with sub run " in output:
#         status = "Finished Sub Run"
#         color = "warning"
#     elif "Prepping DAQs for " in output:
#         status = "Prepping DAQs"
#         color = "warning"
#     elif "Ramping HVs for " in output:
#         status = "Ramping HV"
#         color = "warning"
#     elif "Starting DAQ Control" in output:
#         status = "STARTING"
#         color = "warning"
#     else:
#         status = "UNKNOWN STATE"
#         color = "danger"
#
#     return {"status": status, "color": color, "fields": fields}
#
#
# def get_trigger_control_status():
#     try:
#         output = subprocess.check_output(
#             ["tmux", "capture-pane", "-pS", "-10", "-t", "trigger_control:0.0"],
#             text=True
#         )
#     except subprocess.CalledProcessError:
#         return {
#             "status": "ERROR",
#             "color": "danger",
#             "fields": [{"label": "Details", "value": "trigger_control tmux not running"}]
#         }
#
#     fields = []
#     if "Trigger switch turned on'" in output:
#         status = "Configured"
#         color = "success"
#     elif "Trigger switch turned off" in output:
#         status = "Configuring"
#         color = "warning"
#     elif "Trigger switch control connected" in output:
#         status = "STARTING"
#         color = "warning"
#     elif "Listening on " in output:
#         status = "WAITING"
#         color = "secondary"
#     else:
#         status = "UNKNOWN STATE"
#         color = "danger"
#
#     return {"status": status, "color": color, "fields": fields}


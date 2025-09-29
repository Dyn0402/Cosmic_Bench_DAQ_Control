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

def get_dream_daq_status():
    try:
        output = subprocess.check_output(
            ["tmux", "capture-pane", "-pS", "-500", "-t", "dream_daq:0.0"],
            text=True
        )
    except subprocess.CalledProcessError:
        return {"status": "error", "details": "dream_daq not running"}

    status = {"status": "waiting"}  # default

    # Detect pedestal taking
    if "TakePedThr= On" in output:
        status["status"] = "taking pedestals"

    # Detect data taking
    if "TakeData= On" in output:
        status["status"] = "taking data"

        # Extract RunTime
        match_runtime = re.search(r"RunTime\s+(\d+h\s+\d+m\s+\d+s)", output)
        if match_runtime:
            status["runtime"] = match_runtime.group(1)

        # Extract nb_of_events
        match_events = re.search(r"nb_of_events=(\d+)", output)
        if match_events:
            status["events"] = int(match_events.group(1))

        # Extract wait for time
        match_wait = re.search(r"wait for\s+(\d+h\s+\d+s)", output)
        if match_wait:
            status["wait_for"] = match_wait.group(1)

    return status


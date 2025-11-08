#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 08 01:12 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/desync_watcher

@author: Dylan Neff
"""

import os
import re
import csv
import time
import threading
import subprocess
from datetime import datetime

from Server import Server


def main():
    port = 1105
    monitor_thread = None
    monitor_stop_event = threading.Event()

    while True:
        try:
            with Server(port=port) as server:
                server.receive()
                server.send('Desync monitor connected')
                desync_monitor_info = server.receive_json()
                run_out_dir = desync_monitor_info['run_out_dir']

                res = server.receive()
                while 'Finished' not in res:
                    if 'Start Monitoring' in res:
                        server.send('Desync monitoring ready to start')
                        sub_run = server.receive_json()
                        sub_run_dir = os.path.join(run_out_dir, sub_run['sub_run_name'])
                        csv_out_path = os.path.join(sub_run_dir, "daq_status_log.csv")

                        # If already running, stop the previous one
                        if monitor_thread and monitor_thread.is_alive():
                            monitor_stop_event.set()
                            monitor_thread.join()

                        monitor_stop_event.clear()
                        monitor = DeSyncMonitor(
                            stop_event=monitor_stop_event,
                            interval=desync_monitor_info.get('check_interval', 2),
                            csv_path=csv_out_path,
                            min_points=desync_monitor_info.get('min_points', 5),
                            min_duration=desync_monitor_info.get('min_duration', 6)
                        )
                        monitor_thread = threading.Thread(target=monitor.run, daemon=True)
                        monitor_thread.start()
                        server.send(f'Desync monitoring started for {sub_run["sub_run_name"]}')

                    elif 'End Monitoring' in res:
                        server.send('Stopping desync monitoring')
                        if monitor_thread and monitor_thread.is_alive():
                            monitor_stop_event.set()
                            monitor_thread.join()
                            server.send('Desync monitoring stopped')
                        else:
                            server.send('No monitor running')

                    else:
                        server.send('Unknown Command')

                    res = server.receive()

        except Exception as e:
            print(f'Error: {e}\nRestarting desync monitor server...')
            # ensure monitor stops on crash
            monitor_stop_event.set()
            if monitor_thread and monitor_thread.is_alive():
                monitor_thread.join()

        finally:
            # Cleanup if the script exits or restarts
            monitor_stop_event.set()
            if monitor_thread and monitor_thread.is_alive():
                monitor_thread.join()

    print('donzo')


class DeSyncMonitor:
    def __init__(self, stop_event, interval=5, csv_path="daq_status_log.csv",
                 min_points=5, min_duration=10):
        """
        interval: seconds between checks
        csv_path: output CSV file
        stop_event: threading.Event() to signal stop
        min_points: minimum number of consecutive samples with constant diff
        min_duration: minimum number of seconds diff must be constant and non-zero
        """
        self.interval = interval
        self.csv_path = csv_path
        self.stop_event = stop_event
        self.min_points = min_points
        self.min_duration = min_duration
        self.headers = [
            "timestamp",
            "dream_status",
            "banco_status",
            "dream_events",
            "banco_triggers",
            "difference",
        ]

        # For desync tracking
        self.last_diffs = []       # (timestamp, diff)
        self.desync_triggered = False

        # Initialize CSV header if needed
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def get_dream_status(self):
        try:
            output = subprocess.check_output(
                ["tmux", "capture-pane", "-pS", "-500", "-t", "dream_daq:0.0"],
                text=True
            )
        except subprocess.CalledProcessError:
            return {"status": "ERROR", "events": None}

        if "_TakeData:" in output:
            status = "RUNNING"
            m_ev = re.search(r"nb_of_events=(\d+)", output)
            events = int(m_ev.group(1)) if m_ev else None
        elif "Listening on " in output:
            status = "WAITING"
            events = None
        elif "_TakePedThr" in output or "Scan trigger thresholds" in output:
            status = "BUSY"
            events = None
        else:
            status = "UNKNOWN"
            events = None

        return {"status": status, "events": events}

    def get_banco_status(self):
        try:
            output = subprocess.check_output(
                ["tmux", "capture-pane", "-pS", "-20", "-t", "banco_tracker:0.0"],
                text=True
            )
        except subprocess.CalledProcessError:
            return {"status": "ERROR", "triggers": None}

        rules = [
            "Waiting for trigger...",
            "Triggers to the MOSAIC (trgCount)",
            "ROOT files ready to be closed",
            "- trains: ",
        ]

        status = "UNKNOWN"
        for flag in rules:
            if flag in output:
                status = "RUNNING"
                break
        if "Banco DAQ stopped" in output:
            status = "STOPPED"
        elif "Listening on " in output:
            status = "WAITING"

        m_trg = re.search(r"Triggers to the MOSAIC \(trgCount\)\s*:\s*(\d+)", output)
        triggers = int(m_trg.group(1)) if m_trg else None

        return {"status": status, "triggers": triggers}

    def log_status(self):
        dream = self.get_dream_status()
        banco = self.get_banco_status()

        diff = None
        if dream["events"] is not None and banco["triggers"] is not None:
            diff = banco["triggers"] - dream["events"]

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            dream["status"],
            banco["status"],
            dream["events"],
            banco["triggers"],
            diff,
        ]

        with open(self.csv_path, "a", newline="") as f:
            csv.writer(f).writerow(row)

        return row

    def check_desync(self, diff):
        """Track differences and trigger stop_run.sh if persistent desync detected."""
        now = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Keep small buffer
        if diff is not None:
            self.last_diffs.append((now, diff))
        # Trim old entries beyond needed points
        if len(self.last_diffs) > self.min_points * 2:
            self.last_diffs = self.last_diffs[-self.min_points * 2:]

        # Need enough data to evaluate
        if len(self.last_diffs) < self.min_points:
            print(f"[{timestamp}] Waiting for enough data points... ({len(self.last_diffs)}/{self.min_points})")
            return False

        diffs = [d for _, d in self.last_diffs[-self.min_points:]]
        times = [t for t, _ in self.last_diffs[-self.min_points:]]
        duration = times[-1] - times[0]

        current_diff = diffs[-1]

        # Check if all diffs are the same and non-zero
        if all(d == diffs[0] for d in diffs) and diffs[0] != 0:
            time_remaining = max(0, self.min_duration - duration)
            print(f"[{timestamp}] Δ={current_diff} constant for {duration:.1f}s "
                  f"({time_remaining:.1f}s until stop if persists)")

            # Persistent desync condition met
            if duration >= self.min_duration:
                if not self.desync_triggered:
                    self.desync_triggered = True
                    print(f"⚠️  Persistent desync detected (Δ={current_diff} for {duration:.1f}s). Stopping run.")
                    try:
                        subprocess.run(
                            ["/bash_scripts/stop_run.sh"],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        print("✅ stop_run.sh executed successfully.")
                    except subprocess.CalledProcessError as e:
                        print(f"❌ Error executing stop_run.sh: {e}")
                return True
        else:
            # If difference changed or returned to zero, reset trigger
            if self.desync_triggered:
                print(f"[{timestamp}] Desync resolved or changing (Δ={current_diff}). Resetting trigger.")
            self.desync_triggered = False
            print(f"[{timestamp}] Δ={current_diff} (no persistent desync)")

        return False

    def run(self):
        print(f"Starting DeSyncMonitor thread (interval={self.interval}s)...")
        while not self.stop_event.is_set():
            row = self.log_status()
            diff = row[-1]
            self.check_desync(diff)
            if self.stop_event.wait(self.interval):
                break
        print("DeSyncMonitor thread stopped.")




if __name__ == "__main__":
    main()

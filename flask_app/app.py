#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 29 3:45 PM 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/app.py

@author: Dylan Neff, Dylan
"""

import os
import subprocess
import pty
import select
import threading
import json
import pandas as pd
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO

from daq_status import (get_dream_daq_status, get_hv_control_status, get_daq_control_status, get_trigger_control_status,
                        get_decoder_status, get_banco_tracker_status)

CONFIG_TEMPLATE_DIR = "/local/home/banco/dylan/Cosmic_Bench_DAQ_Control/config/json_templates"
CONFIG_RUN_DIR = "/local/home/banco/dylan/Cosmic_Bench_DAQ_Control/config/json_run_configs"
BASH_DIR = "/local/home/banco/dylan/Cosmic_Bench_DAQ_Control/bash_scripts"
HV_TAIL = 1000  # number of most recent rows to show
current_subrun_name = None


app = Flask(__name__)
socketio = SocketIO(app)

TMUX_SESSIONS = ["hv_control", "dream_daq", "decoder", "daq_control", "trigger_control", "banco_tracker"]
sessions = {}

@app.route("/")
def index():
    configs = [f for f in os.listdir(CONFIG_RUN_DIR) if f.endswith(".json")]
    return render_template("index.html", screens=TMUX_SESSIONS, run_configs=configs)


@app.route("/status")
def status_all():
    statuses = {}
    for s in TMUX_SESSIONS:
        if s == "dream_daq":
            statuses[s] = get_dream_daq_status()
            # If Subrun has changed, reset current_subrun_name
            current_subrun_name = ''
        elif s == "hv_control":
            statuses[s] = get_hv_control_status()
        elif s == "daq_control":
            statuses[s] = get_daq_control_status()
        elif s == "trigger_control":
            statuses[s] = get_trigger_control_status()
        elif s == "decoder":
            statuses[s] = get_decoder_status()
        elif s == "banco_tracker":
            statuses[s] = get_banco_tracker_status()
        else:
            statuses[s] = {
                "status": "READY",
                "color": "secondary",
                "fields": []
            }
    return jsonify(statuses)


@app.route("/start_run", methods=["POST"])
def start_run():
    data = request.get_json()
    config_file = data.get("config")

    if not config_file:
        return jsonify({"message": "No config selected"}), 400

    config_path = os.path.join(CONFIG_RUN_DIR, config_file)
    if not os.path.exists(config_path):
        return jsonify({"message": f"Config not found: {config_path}"}), 404

    script_path = f"{BASH_DIR}/start_run.sh"
    result = subprocess.run(
        [script_path, config_path],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return jsonify({"message": f"Run started with {config_file}"})
    else:
        return jsonify({"message": f"Error: {result.stderr}"}), 500

@app.route("/stop_run", methods=["POST"])
def stop_run():
    try:
        subprocess.Popen([f"{BASH_DIR}/stop_run.sh"])
        return jsonify({"success": True, "message": "Run stopped"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/restart_all", methods=["POST"])
def restart_all():
    try:
        subprocess.Popen([f"{BASH_DIR}/restart_all_tmux_processes.sh"])
        return jsonify({"success": True, "message": "All processes restarted"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/get_runs")
def get_runs():
    runs = []
    for f in os.listdir(CONFIG_RUN_DIR):
        if f.endswith(".json"):
            runs.append(f)
    return jsonify(runs)

@app.route("/get_subruns")
def get_subruns():
    run_name = request.args.get("run")
    if not run_name:
        return jsonify([])

    config_path = os.path.join(CONFIG_RUN_DIR, run_name)
    if not os.path.isfile(config_path):
        return jsonify([])

    try:
        with open(config_path) as f:
            cfg = json.load(f)
        output_dir = cfg.get("run_out_dir")
        if not output_dir or not os.path.isdir(output_dir):
            return jsonify([])

        subruns = sorted(
            os.listdir(output_dir),
            key=lambda f: os.path.getmtime(os.path.join(output_dir, f)),
            reverse=True
        )

        # Ensure it matches item in cfg['subruns'][i]['sub_run_name'] if that key exists
        if "sub_runs" in cfg:
            valid_subruns = {sr.get("sub_run_name") for sr in cfg["sub_runs"] if "sub_run_name" in sr}
            subruns = [sr for sr in subruns if sr in valid_subruns]

        return jsonify(subruns)
    except Exception as e:
        print("Error reading subruns:", e)
        return jsonify([])


@app.route("/hv_data")
def hv_data():
    try:
        run_name = request.args.get("run")
        subrun_name = request.args.get("subrun")
        hv_file_name = request.args.get("hv_file", "hv_monitor.csv")

        config_path = os.path.join(CONFIG_RUN_DIR, run_name)
        if not os.path.isfile(config_path):
            return jsonify([])

        with open(config_path) as f:
            cfg = json.load(f)
        output_dir = cfg.get("run_out_dir")
        hv_csv_path = os.path.join(output_dir, subrun_name, hv_file_name)

        df = pd.read_csv(hv_csv_path)
        df = df.tail(HV_TAIL)

        # Extract timestamps
        time = df["timestamp"].astype(str).tolist()

        voltage_data = {}
        current_data = {}

        # Loop through columns to find slot:channel prefixes
        for col in df.columns:
            if "vmon" in col:
                key = col.replace(" vmon", "")
                voltage_data[key] = df[col].tolist()
            elif "imon" in col:
                key = col.replace(" imon", "")
                current_data[key] = df[col].tolist()

        return jsonify({
            "success": True,
            "time": time,
            "voltage": voltage_data,
            "current": current_data
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/json_templates")
def list_json_templates():
    try:
        files = [f for f in os.listdir(CONFIG_TEMPLATE_DIR) if f.endswith(".json")]
        return jsonify({"success": True, "templates": files})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/json_templates/<template_name>")
def load_json_template(template_name):
    try:
        path = os.path.join(CONFIG_TEMPLATE_DIR, template_name)
        if not os.path.isfile(path):
            return jsonify({"success": False, "message": "File not found"}), 404
        with open(path, "r") as f:
            data = json.load(f)
        return jsonify({"success": True, "content": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/save_run_config", methods=["POST"])
def save_run_config():
    try:
        data = request.get_json()
        content = data.get("content")

        if not isinstance(content, dict):
            return jsonify({"success": False, "message": "Invalid JSON content"}), 400

        run_name = content.get("run_name")
        if not run_name:
            return jsonify({"success": False, "message": "Missing 'run_name' field in config"}), 400

        os.makedirs(CONFIG_RUN_DIR, exist_ok=True)

        filename = f"{run_name}.json"
        path = os.path.join(CONFIG_RUN_DIR, filename)
        with open(path, "w") as f:
            json.dump(content, f, indent=4)

        return jsonify({"success": True, "message": f"Run config saved as {filename}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/list_json_configs')
def list_json_configs():
    folder = "./config/json_run_configs"
    files = [f for f in os.listdir(folder) if f.endswith('.json')]
    return jsonify(files)

@app.route('/load_json_config/<filename>')
def load_json_config(filename):
    path = os.path.join("./config/json_run_configs", filename)
    with open(path) as f:
        return jsonify(json.load(f))

@app.route('/save_json_config', methods=['POST'])
def save_json_config():
    data = request.get_json()
    run_name = data.get('run_name', 'unnamed')
    path = f"./config/json_run_configs/{run_name}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    return f"Saved to {path}"

@app.route('/save_json_template', methods=['POST'])
def save_json_template():
    req = request.get_json()
    name = req.get('name')
    data = req.get('data')
    path = f"./config/json_templates/{name}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    return f"Template saved to {path}"


@socketio.on("start")
def start(data):
    name = data.get("name")
    if name in sessions:
        return  # already attached

    pid, fd = pty.fork()
    if pid == 0:
        # Child: attach to tmux session
        os.execvp("tmux", ["tmux", "attach-session", "-t", name])
    else:
        # Parent: keep FD for reading/writing
        sessions[name] = fd

        def read_fd(fd, session_name):
            while True:
                try:
                    r, _, _ = select.select([fd], [], [], 0.1)
                    if fd in r:
                        output = os.read(fd, 1024).decode(errors="ignore")
                        socketio.emit(f"output-{session_name}", output)
                except OSError:
                    break

        threading.Thread(target=read_fd, args=(fd, name), daemon=True).start()

# Generic input handler for all sessions
for s in TMUX_SESSIONS:
    @socketio.on(f"input-{s}")
    def make_input(session_name=s):
        def handle_input(data):
            os.write(sessions[session_name], data.encode())
        return handle_input

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001)

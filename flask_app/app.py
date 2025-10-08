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
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO

from daq_status import get_dream_daq_status, get_hv_control_status, get_daq_control_status

TEMPLATE_DIR = "/local/home/banco/dylan/Cosmic_Bench_DAQ_Control/config/json_templates"

app = Flask(__name__)
socketio = SocketIO(app)

TMUX_SESSIONS = ["hv_control", "dream_daq", "decoder", "daq_control", "trigger_control", "banco_alpide_control"]
sessions = {}

@app.route("/")
def index():
    return render_template("index.html", screens=TMUX_SESSIONS)

# @app.route("/status/dream_daq")
# def dream_daq_status():
#     return jsonify(get_dream_daq_status())

@app.route("/status")
def status_all():
    statuses = {}
    for s in TMUX_SESSIONS:
        if s == "dream_daq":
            statuses[s] = get_dream_daq_status()
        elif s == "hv_control":
            statuses[s] = get_hv_control_status()
        elif s == "daq_control":
            statuses[s] = get_daq_control_status()
        else:
            statuses[s] = {
                "status": "READY",
                "color": "secondary",
                "fields": []
            }
    return jsonify(statuses)


@app.route("/start_run", methods=["POST"])
def start_run():
    try:
        # Run your bash script in the background
        subprocess.Popen(["/local/home/banco/dylan/Cosmic_Bench_DAQ_Control/bash_scripts/start_run.sh"])
        return jsonify({"success": True, "message": "Run started"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/stop_run", methods=["POST"])
def stop_run():
    try:
        subprocess.Popen(["/local/home/banco/dylan/Cosmic_Bench_DAQ_Control/bash_scripts/stop_run.sh"])
        return jsonify({"success": True, "message": "Run stopped"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/json_templates")
def list_json_templates():
    try:
        files = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith(".json")]
        return jsonify({"success": True, "templates": files})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/json_templates/<template_name>")
def load_json_template(template_name):
    try:
        path = os.path.join(TEMPLATE_DIR, template_name)
        if not os.path.isfile(path):
            return jsonify({"success": False, "message": "File not found"}), 404
        with open(path, "r") as f:
            data = json.load(f)
        return jsonify({"success": True, "content": data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


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

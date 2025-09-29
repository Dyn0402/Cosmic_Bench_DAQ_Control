#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 29 3:45 PM 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/app.py

@author: Dylan Neff, Dylan
"""


import subprocess
import threading
import time

from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

TMUX_SESSIONS = ["hv_control", "dream_daq", "decoder", "daq_control"]

def read_tmux_output(session_name):
    """
    Continuously read the visible output of the tmux session and emit via socketio.
    """
    while True:
        try:
            # Capture last 50 lines from tmux pane 0
            output = subprocess.check_output(
                ["tmux", "capture-pane", "-pt0", "-S", "-50"],
                stderr=subprocess.DEVNULL,
            ).decode(errors="ignore")
            socketio.emit(f"output-{session_name}", output)
            time.sleep(1)
        except Exception as e:
            print(f"Error reading tmux {session_name}: {e}")
            time.sleep(1)

@app.route("/")
def index():
    return render_template("index.html", screens=TMUX_SESSIONS)

# Start background threads for each tmux session
for session in TMUX_SESSIONS:
    threading.Thread(target=read_tmux_output, args=(session,), daemon=True).start()

# Input handlers for interactive panes
for session in TMUX_SESSIONS:
    @socketio.on(f"input-{session}")
    def make_input(s=session):
        def handle_input(data):
            subprocess.run(["tmux", "send-keys", "-t", s, data, "Enter"])
        return handle_input

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001)



# from flask import Flask, render_template, jsonify
# from flask_socketio import SocketIO
# import os, pty, select, threading
# import random
#
# app = Flask(__name__)
# socketio = SocketIO(app)
#
# SCREENS = ["hv_control", "dream_daq", "decoder", "daq_control"]
# sessions = {}
# STATUS_KEYS = ["HV Control", "DAQ", "Decoder", "Other Module"]
#
# @app.route("/")
# def index():
#     return render_template("index.html", screens=SCREENS)
#
# @app.route("/status")
# def status():
#     return jsonify({k: random.choice(["RUNNING", "ERROR", "READY", "STOPPED"]) for k in STATUS_KEYS})
#
# # --- SocketIO handlers ---
# @socketio.on("start")
# def start(data):
#     name = data.get("name")
#     if name in sessions:
#         return
#
#     pid, fd = pty.fork()
#     if pid == 0:
#         os.execvp("screen", ["screen", "-x", name])
#     else:
#         sessions[name] = fd
#         def read_from_fd(fd, screen_name):
#             while True:
#                 try:
#                     r, _, _ = select.select([fd], [], [], 0.1)
#                     if fd in r:
#                         output = os.read(fd, 1024).decode(errors="ignore")
#                         socketio.emit(f"output-{screen_name}", output)
#                 except OSError:
#                     break
#         threading.Thread(target=read_from_fd, args=(fd, name), daemon=True).start()
#
# for name in SCREENS:
#     @socketio.on(f"input-{name}")
#     def make_input(n):
#         return lambda data: os.write(sessions[n], data.encode())
#     make_input(name)
#
# if __name__ == "__main__":
#     socketio.run(app, host="0.0.0.0", port=5001)


# import os
# import pty
# import select
# import threading
#
# from flask import Flask, render_template_string
# from flask_socketio import SocketIO
#
# app = Flask(__name__)
# socketio = SocketIO(app)
#
# # Define the screen sessions you want to expose
# SCREENS = ["hv_control", "dream_daq", "decoder", "daq_control"]
#
# # Keep PTY fds per screen
# sessions = {}
#
#
# @app.route("/")
# def index():
#     template = """
#     <html>
#     <head>
#         <link rel="stylesheet" href="/static/xterm.css" />
#         <script src="/static/xterm.js"></script>
#         <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
#         <style>
#             body { background: #222; color: #eee; font-family: monospace; }
#             .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1em; }
#             .term-container { background: #111; border: 1px solid #555; border-radius: 6px; }
#             h2 { margin: 0; padding: 0.3em; font-size: 1.1em; background: #333; }
#             .terminal { width: 100%; height: 400px; }
#         </style>
#     </head>
#     <body>
#         <h1>Live Screen Sessions</h1>
#         <div class="grid">
#         {% for name in screens %}
#           <div class="term-container">
#             <h2>{{name}}</h2>
#             <div id="terminal-{{name}}" class="terminal"></div>
#           </div>
#         {% endfor %}
#         </div>
#
#         <script>
#         {% for name in screens %}
#           (function() {
#             var term = new Terminal();
#             term.open(document.getElementById("terminal-{{name}}"));
#
#             var socket = io();
#             socket.on("output-{{name}}", function(data) {
#                 term.write(data);
#             });
#
#             term.onData(function(data) {
#                 socket.emit("input-{{name}}", data);
#             });
#
#             socket.emit("start", {name: "{{name}}"});
#           })();
#         {% endfor %}
#         </script>
#     </body>
#     </html>
#     """
#     return render_template_string(template, screens=SCREENS)
#
#
# @socketio.on("start")
# def start(data):
#     name = data.get("name")
#     if name in sessions:
#         return
#
#     pid, fd = pty.fork()
#     if pid == 0:
#         # Child process: attach to screen session
#         os.execvp("screen", ["screen", "-x", name])
#     else:
#         sessions[name] = fd
#
#         def read_from_fd(fd, screen_name):
#             while True:
#                 try:
#                     r, _, _ = select.select([fd], [], [], 0.1)
#                     if fd in r:
#                         output = os.read(fd, 1024).decode(errors="ignore")
#                         socketio.emit(f"output-{screen_name}", output)
#                 except OSError:
#                     break
#
#         thread = threading.Thread(target=read_from_fd, args=(fd, name), daemon=True)
#         thread.start()
#
#
# @socketio.on("input-hv_control")
# def input_hv(data):
#     os.write(sessions["hv_control"], data.encode())
#
#
# @socketio.on("input-dream_daq")
# def input_dreamdaq(data):
#     os.write(sessions["dream_daq"], data.encode())
#
#
# @socketio.on("input-decoder")
# def input_decoder(data):
#     os.write(sessions["decoder"], data.encode())
#
#
# @socketio.on("input-daq_control")
# def input_daq(data):
#     os.write(sessions["daq_control"], data.encode())


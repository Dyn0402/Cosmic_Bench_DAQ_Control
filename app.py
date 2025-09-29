#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 29 12:46 PM 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/app.py

@author: Dylan Neff, Dylan
"""

import time
from flask import Flask, Response, render_template_string, stream_with_context

app = Flask(__name__)

# Map screen names to their log files
LOG_FILES = {
    "hv_control": "/local/home/banco/dylan/Cosmic_Bench_DAQ_Control/logs/hv_control.log",
    "dream_daq": "/local/home/banco/dylan/Cosmic_Bench_DAQ_Control/logs/dream_daq.log",
}

@app.route("/")
def index():
    # Show links to each log
    links = "".join(f'<li><a href="/view/{name}">{name}</a></li>' for name in LOG_FILES)
    return f"<h1>Available Logs</h1><ul>{links}</ul>"

@app.route("/view/<name>")
def view_log(name):
    if name not in LOG_FILES:
        return "No such log", 404

    # Basic HTML page that connects to the stream
    template = """
    <h1>Log: {{name}}</h1>
    <pre id="log" style="white-space: pre-wrap; background: #111; color: #eee; padding: 1em; height: 80vh; overflow-y: scroll;"></pre>
    <script>
    var logElem = document.getElementById("log");
    var evtSource = new EventSource("/stream/{{name}}");
    evtSource.onmessage = function(e) {
        logElem.textContent += e.data + "\\n";
        logElem.scrollTop = logElem.scrollHeight; // auto-scroll
    }
    </script>
    <a href="/">Back</a>
    """
    return render_template_string(template, name=name)

@app.route("/stream/<name>")
def stream_log(name):
    path = LOG_FILES.get(name)
    if not path:
        return "No such log", 404

    def generate():
        with open(path, "r") as f:
            # Seek to end of file to show only new content
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    yield f"data: {line.rstrip()}\n\n"
                else:
                    time.sleep(0.5)

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


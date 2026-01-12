#!/bin/bash

# Function to start a screen session safely
start_screen() {
    local name=$1
    local cmd=$2

    # Check if screen session already exists
    if screen -list | grep -q "[[:space:]]$name"; then
        echo "❌ Screen session '$name' already exists!"
        return 1
    fi

    if [ -z "$cmd" ]; then
        # Start an empty interactive screen session
        screen -dmS "$name"
        echo "✅ Started empty screen session: $name"
    else
        # Start screen session and run command
        screen -dmS "$name" bash -lc "$cmd"
        echo "✅ Started $name running: $cmd"
    fi
}

# Start sessions
start_screen hv_control "python hv_control.py"
start_screen dream_daq "python dream_daq_control.py"
start_screen decoder "source /local/home/usernsw/dylan/root/obj/bin/thisroot.sh && python processing_control.py"
start_screen m3_tracking "python m3_tracking_control.py"
start_screen daq_control "echo 'Daq control session started'"
#start_screen flask_server "flask_app/start_flask.sh"

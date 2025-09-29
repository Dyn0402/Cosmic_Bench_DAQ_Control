#!/bin/bash

# Function to start a screen safely
start_screen() {
    local name=$1
    local cmd=$2
    local logfile="logs/${name}.log"

    # Check if screen session already exists
    if screen -list | grep -q "[.]${name}[[:space:]]"; then
        echo "❌ Screen session '$name' already exists!"
        return 1
    fi

    mkdir -p logs

    if [ -z "$cmd" ]; then
        # Start an empty interactive screen
        screen -dmS "$name"
        echo "✅ Started empty screen: $name"
    else
        # Run command inside screen, redirecting output to log
        screen -dmL -Logfile "$logfile" -S "$name" bash -c "$cmd; exec bash"
        echo "✅ Started $name running: $cmd"
        sleep 1  # Give it a moment to start

        # Check log for port error
        if grep -q "Address already in use" "$logfile"; then
            echo "⚠️  $name: Port already in use error detected!"
        fi
    fi
}

# Start sessions
start_screen hv_control "python hv_control.py"
start_screen dream_daq "python dream_daq_control.py"
start_screen decoder "python processing_control.py"
start_screen daq_control 'echo "DAQ Control Interface"'
start_screen flask_server 'export FLASK_APP=app.py; flask run --host=0.0.0.0 --port=5001'

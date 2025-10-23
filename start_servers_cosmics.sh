#!/bin/bash

# Function to start a tmux session safely
start_tmux() {
    local name=$1
    local cmd=$2

    # Check if tmux session already exists
    if tmux has-session -t "$name" 2>/dev/null; then
        echo "❌ Tmux session '$name' already exists!"
        return 1
    fi

    if [ -z "$cmd" ]; then
        # Start an empty interactive tmux session
        tmux new-session -d -s "$name"
        echo "✅ Started empty tmux session: $name"
    else
        # Start tmux session and run command
        tmux new-session -d -s "$name"
        tmux send-keys -t "$name" "$cmd" Enter
        echo "✅ Started $name running: $cmd"
    fi
}

# Start sessions
start_tmux hv_control "python hv_control.py"
start_tmux dream_daq "python dream_daq_control.py"
start_tmux decoder 'bash -lc "source /local/home/usernsw/dylan/root/obj/bin/thisroot.sh && python processing_control.py"'
start_tmux m3_tracking "python m3_tracking_control.py"
start_tmux daq_control "echo 'Daq control session started'"
#start_tmux flask_server "flask_app/start_flask.sh"

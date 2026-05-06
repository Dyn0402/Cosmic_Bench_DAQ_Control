#!/bin/bash

# Function to start a tmux session safely
#start_tmux() {
#    local name=$1
#    local cmd=$2
#
#    # Check if tmux session already exists
#    if tmux has-session -t "$name" 2>/dev/null; then
#        echo "❌ Tmux session '$name' already exists!"
#        return 1
#    fi
#
#    if [ -z "$cmd" ]; then
#        # Start an empty interactive tmux session
#        tmux new-session -d -s "$name"
#        echo "✅ Started empty tmux session: $name"
#    else
#        # Start tmux session and run command
#        tmux new-session -d -s "$name"
#        tmux send-keys -t "$name" "$cmd" Enter
#        echo "✅ Started $name running: $cmd"
#    fi
#}

# Start sessions
bash_scripts/start_tmux hv_control "python hv_control.py"
bash_scripts/start_tmux dream_daq "python dream_daq_control.py"
#PROCESSOR_CONFIG="/local/home/usernsw/Cosmic_Bench_DAQ_Control/config/processor_config.json"
#start_tmux processor "python processor_watcher.py $PROCESSOR_CONFIG"
bash_scripts/start_tmux m3_tracking "python m3_tracking_control.py"
bash_scripts/start_tmux daq_control "echo 'Daq control session started'"
bash_scripts/start_tmux flask_server "flask_app/start_flask.sh"

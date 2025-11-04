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
#
#start_tmux hv_control "python hv_control.py"
#start_tmux dream_daq "python dream_daq_control.py"
#start_tmux decoder "python processing_control.py"
#start_tmux processor "python processor_server.py"
#start_tmux daq_control "echo 'Daq control session started'"
#start_tmux trigger_veto_control "bash_scripts/start_trigger_veto_control.sh"
#start_tmux trigger_gen_control "bash_scripts/start_trigger_gen_control.sh"
#start_tmux banco_tracker "bash_scripts/start_banco_alpide_control.sh"
#start_tmux flask_server "flask_app/start_flask.sh"


# Start sessions
bash_scripts/start_tmux.sh hv_control "python hv_control.py"
bash_scripts/start_tmux.sh dream_daq "python dream_daq_control.py"
#bash_scripts/start_tmux.sh decoder "python processing_control.py"
#bash_scripts/start_tmux.sh processor "python processor_server.py"
bash_scripts/start_tmux.sh daq_control "echo 'Daq control session started'"
bash_scripts/start_tmux.sh trigger_veto_control "bash_scripts/start_trigger_veto_control.sh"
bash_scripts/start_tmux.sh trigger_gen_control "bash_scripts/start_trigger_gen_control.sh"
bash_scripts/start_tmux.sh banco_tracker "bash_scripts/start_banco_alpide_control.sh"
bash_scripts/start_tmux.sh flask_server "flask_app/start_flask.sh"

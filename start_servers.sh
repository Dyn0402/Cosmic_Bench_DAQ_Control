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
start_tmux decoder "python processing_control.py"
start_tmux daq_control   # empty interactive session
#start_tmux flask_server 'export FLASK_APP=app.py; flask run --host=0.0.0.0 --port=5001'
start_tmux flask_server 'flask_app/start_flask.sh'


##!/bin/bash
#
## Function to start a screen safely
#start_screen() {
#    local name=$1
#    local cmd=$2
#
#    # Check if screen session already exists
#    if screen -list | grep -q "[.]${name}[[:space:]]"; then
#        echo "❌ Screen session '$name' already exists!"
#        return 1
#    fi
#
#    if [ -z "$cmd" ]; then
#        # Start an empty interactive screen
#        screen -dmS "$name"
#        echo "✅ Started empty screen: $name"
#    else
#        # Start interactive shell, then inject command
#        screen -dmS "$name"
#        # Send command into the screen, with a newline
#        screen -S "$name" -X stuff $"$cmd\n"
#        echo "✅ Started $name running: $cmd"
#    fi
#}
#
## Start sessions
#start_screen hv_control "python hv_control.py"
#start_screen dream_daq "python dream_daq_control.py"
#start_screen decoder "python processing_control.py"
#start_screen daq_control
#start_screen flask_server 'export FLASK_APP=app.py; flask run --host=0.0.0.0 --port=5001'

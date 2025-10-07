#!/bin/bash
SESSION="daq_control"
COMMAND="python daq_control_new.py"

# Send the command to the session and execute it
tmux send-keys -t "$SESSION" "$COMMAND" C-m
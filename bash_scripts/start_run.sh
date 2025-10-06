#!/bin/bash
SESSION="daq_control"
COMMAND="python daq_control_new.py"

# Send the command to the session and execute it in background (&)
tmux send-keys -t "$SESSION" "$COMMAND &" C-m

# (Optional) detach from the session (no effect if you weren't attached)
tmux detach -s "$SESSION"

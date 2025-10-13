#!/bin/bash
SESSION="daq_control"
CONFIG_PATH="$1"

if [ -z "$CONFIG_PATH" ]; then
  echo "Usage: $0 <config_path>"
  exit 1
fi

COMMAND="python daq_control.py \"$CONFIG_PATH\""

# Send command to the tmux session
tmux send-keys -t "$SESSION" "$COMMAND" C-m


##!/bin/bash
#SESSION="daq_control"
#COMMAND="python daq_control.py"
#
## Send the command to the session and execute it
#tmux send-keys -t "$SESSION" "$COMMAND" C-m
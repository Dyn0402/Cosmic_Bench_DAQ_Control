#!/bin/bash
SESSION="daq_control"
CONFIG_FILE="$1"

if [ -z "$CONFIG_FILE" ]; then
  echo "Usage: $0 <config_file_name>"
  exit 1
fi

COMMAND="python daq_control.py \"$CONFIG_FILE\""

# Send command to the tmux session
tmux send-keys -t "$SESSION" "$COMMAND" C-m

# Send config to processor
python send_run_config_to_processor.py "$CONFIG_FILE"

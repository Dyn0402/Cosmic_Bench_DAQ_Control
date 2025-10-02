#!/bin/bash

PI_USER="pi"
PI_HOST="192.168.10.101"
REMOTE_DIR="dylan/Cosmic_Bench_DAQ_Control"
SCRIPT="trigger_switch_control.py"
SCREEN_NAME="trigger_control"

ssh -t "$PI_USER@$PI_HOST" << EOF
cd "$REMOTE_DIR"
# Start a new screen session if it doesn't exist, or attach
screen -S "$SCREEN_NAME" -X quit 2>/dev/null  # optional: kill existing session
screen -dmS "$SCREEN_NAME" bash -c "python3 '$SCRIPT'; exec bash"
screen -r "$SCREEN_NAME"
EOF

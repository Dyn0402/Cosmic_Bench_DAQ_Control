#!/bin/bash

PI_USER="pi"
PI_HOST="192.168.10.198"
REMOTE_DIR="dylan/Cosmic_Bench_DAQ_Control"
SCRIPT="trigger_switch_control.py"
SCREEN_NAME="trigger_control"

ssh "$PI_USER@$PI_HOST" << EOF
cd "$REMOTE_DIR"
# Attach to existing screen or create a new one and run the Python script
screen -S "$SCREEN_NAME" -X quit 2>/dev/null  # Optional: kill existing session
screen -dmS "$SCREEN_NAME" bash -c "python '$SCRIPT'; exec bash"
# Now attach so you can monitor it
screen -r "$SCREEN_NAME"
EOF
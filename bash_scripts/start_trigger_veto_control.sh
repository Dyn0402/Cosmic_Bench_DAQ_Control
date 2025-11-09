#!/bin/bash

PI_USER="pi"
PI_HOST="192.168.10.101"
REMOTE_DIR="dylan/Cosmic_Bench_DAQ_Control"
SCRIPT="trigger_switch_control.py"
PORT="1100"
GPIO_PIN="17"

SCREEN_NAME="trigger_veto_control"

ssh -t "$PI_USER@$PI_HOST" "
cd '$REMOTE_DIR'
# Start screen session (detached) and run Python
screen -S "$SCREEN_NAME" -X quit 2>/dev/null  # optional: kill existing session
screen -dmS '$SCREEN_NAME' bash -c 'sleep 1.0; python3 $SCRIPT $PORT $GPIO_PIN; exec bash'
# Attach to the screen to see output
screen -r '$SCREEN_NAME'
"
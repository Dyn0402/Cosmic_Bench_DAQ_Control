#!/bin/bash

PI_USER="pi"
PI_HOST="192.168.10.101"
REMOTE_DIR="dylan/Cosmic_Bench_DAQ_Control"
SCRIPT="trigger_switch_control.py"
SCREEN_NAME="trigger_control"

ssh -t "$PI_USER@$PI_HOST" "
cd '$REMOTE_DIR'
# Start screen session (detached) and run Python
screen -dmS '$SCREEN_NAME' bash -c 'python3 $SCRIPT; exec bash'
# Attach to the screen to see output
screen -r '$SCREEN_NAME'
"

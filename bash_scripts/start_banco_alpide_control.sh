#!/bin/bash

USER="banco"
HOST="alicemftsac.extra.cea.fr"
REMOTE_DIR="dylan/Cosmic_Bench_DAQ_Control"
SCRIPT="banco_daq_control.py"
SCREEN_NAME="banco_alpide_control"

ssh -t "$USER@$HOST" "
cd '$REMOTE_DIR'
# Start screen session (detached) and run Python
screen -S "$SCREEN_NAME" -X quit 2>/dev/null  # optional: kill existing session
screen -dmS '$SCREEN_NAME' bash -c 'setup-o2-root && python3 $SCRIPT; exec bash'
# Attach to the screen to see output
screen -r '$SCREEN_NAME'
"

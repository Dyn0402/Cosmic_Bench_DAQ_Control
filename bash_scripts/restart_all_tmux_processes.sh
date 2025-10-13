#!/bin/bash

# Start a detached screen that will handle the restart
screen -dmS restart_tmux bash -c '
  sleep 2
  /local/home/banco/dylan/Cosmic_Bench_DAQ_Control/start_all_servers.sh
'

# Kill tmux server
tmux kill-server

#!/bin/bash

# Start the restart in background with a small delay
nohup bash -c "sleep 2 && /local/home/banco/dylan/Cosmic_Bench_DAQ_Control/start_all_servers.sh" >/dev/null 2>&1 &

# Kill tmux server
tmux kill-server
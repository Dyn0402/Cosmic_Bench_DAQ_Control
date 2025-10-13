#!/bin/bash

# Schedule restart after tmux exits
echo "/local/home/banco/dylan/Cosmic_Bench_DAQ_Control/start_servers.sh" | at now + 2 seconds

# Kill tmux server
tmux kill-server
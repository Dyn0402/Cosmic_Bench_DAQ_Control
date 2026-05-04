#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_SERVERS="$SCRIPT_DIR/../start_servers.sh"

 #Launch start_servers.sh in a new session so it survives the tmux kill below
 setsid bash -c "sleep 2; $START_SERVERS" > /tmp/restart_tmux.log 2>&1 &

# Restart servers in detached screen
#screen -dmS restart_tmux bash -c "
#  sleep 2
#  $START_SERVERS
#  sleep 20
#"
# Kill tmux server
tmux kill-server
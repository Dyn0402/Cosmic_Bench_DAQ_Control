#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_SERVERS="$SCRIPT_DIR/../start_servers.sh"
LOGFILE="/tmp/restart_daq_debug.log"

{
  echo "=== $(date) ==="
  echo "Called by PID $$, PPID $PPID"
  echo "USER=$USER, HOME=$HOME"
  echo "TERM=${TERM:-<unset>}, STY=${STY:-<unset>}"
  echo "SCRIPT_DIR=$SCRIPT_DIR"
  echo "START_SERVERS=$START_SERVERS"
  echo "start_servers.sh exists: $([ -f "$START_SERVERS" ] && echo yes || echo NO)"
  echo "start_servers.sh executable: $([ -x "$START_SERVERS" ] && echo yes || echo NO)"
  echo "screen path: $(which screen 2>&1)"
} >> "$LOGFILE" 2>&1

# Restart servers in detached screen
screen -dmS restart_tmux bash -c "
  echo 'screen started at \$(date)' >> $LOGFILE
  sleep 2
  echo 'running $START_SERVERS' >> $LOGFILE
  $START_SERVERS >> $LOGFILE 2>&1
  echo 'start_servers.sh exited with code \$?' >> $LOGFILE
"
SCREEN_EXIT=$?
echo "screen launch exit code: $SCREEN_EXIT" >> "$LOGFILE"
echo "screen -ls output: $(screen -ls 2>&1)" >> "$LOGFILE"
# Kill tmux server
sessions=(
  daq_control
  dream_daq
  hv_control
  flask_server
)

for s in "${sessions[@]}"; do
  if tmux has-session -t "$s" 2>/dev/null; then
    tmux kill-session -t "$s"
  fi
done

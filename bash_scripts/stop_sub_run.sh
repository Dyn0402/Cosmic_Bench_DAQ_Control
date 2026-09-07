#!/bin/bash
# Stop the CURRENT sub-run but let the run continue to the next sub-run.
#
# Drop a .stop_subrun flag (so daq_control does NOT mark this cut-short sub-run
# complete — resume should re-run it), then stop the DAQ. RunCtrl exits, the
# dream server reports the sub-run done, and daq_control advances. No Ctrl-C.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

touch "$REPO_DIR/.stop_subrun"
"$SCRIPT_DIR/stop_dream.sh"

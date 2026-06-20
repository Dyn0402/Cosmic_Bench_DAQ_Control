#!/bin/bash

# NOTE: make_dream_ped_cfg.py is legacy beam-setup machinery (hardcoded to
# /mnt/data/beam_sps_25/.../TbSPS25.cfg) and its output is unused here. The MX17
# pedestal cfg is generated on the fly by dream_daq_control.py from the
# do_pedestal_threshold_run flag in run_config_pedestals.py, so it is disabled.
# python make_dream_ped_cfg.py

python run_config_pedestals.py

CONFIG_PATH="run_config_pedestals.json"

bash_scripts/start_run.sh "$CONFIG_PATH"

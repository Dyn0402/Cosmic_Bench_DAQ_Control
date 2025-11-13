#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 13 09:17 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/get_config_py

@author: Dylan Neff, dn277127
"""

import importlib
import json
import run_config_beam

def main():
    importlib.reload(run_config_beam)   # FORCE fresh read from disk

    config = run_config_beam.Config()
    run_name = config.run_name
    banco_position = config.bench_geometry['banco_moveable_y_position']

    print(json.dumps({
        "run_name": run_name,
        "banco_position": banco_position
    }))

if __name__ == "__main__":
    main()

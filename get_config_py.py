#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 13 09:17 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/get_config_py

@author: Dylan Neff, dn277127
"""

import json
from run_config_beam import Config

def main():
    config = Config()
    run_name = config.run_name
    banco_position = config.bench_geometry['banco_moveable_y_position']

    # Print as JSON so the Flask app can easily parse it
    print(json.dumps({
        "run_name": run_name,
        "banco_position": banco_position
    }))

if __name__ == "__main__":
    main()
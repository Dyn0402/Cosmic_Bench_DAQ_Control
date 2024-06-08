#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 14 8:19 AM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/run_processor.py

@author: Dylan Neff, Dylan
"""

from Client import Client
from run_config import Config


def main():
    # run_m3_tracking_hv7()
    run_m3_filtering_max_hv_stats()
    print('donzo')


def run_m3_filtering_max_hv_stats():
    config = Config()
    dedip196_ip, dedip196_port = config.dedip196_processor_info['ip'], config.dedip196_processor_info['port']
    with Client(dedip196_ip, dedip196_port) as processor_client:
        processor_client.send('Connected to run_processor')
        processor_client.receive()
        processor_client.send_json(config.dedip196_processor_info)
        processor_client.send_json({'included_detectors': config.included_detectors})
        processor_client.send_json({'detectors': config.detectors})

        processor_client.send('Filter By M3 max_hv_stats')
        processor_client.receive()


def run_m3_tracking_hv7():
    config = Config()
    sedip28_ip, sedip28_port = config.sedip28_processor_info['ip'], config.sedip28_processor_info['port']
    with Client(sedip28_ip, sedip28_port) as processor_client:
        processor_client.send('Connected to run_processor')
        processor_client.receive()
        processor_client.send_json(config.sedip28_processor_info)

        processor_client.send('Run M3 Tracking HV7')
        processor_client.receive()


if __name__ == '__main__':
    main()

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
    config = Config()
    dedip196_ip, dedip196_port = config.processor_info['ip'], config.processor_info['port']
    dedip196_port = 1200
    with Client(dedip196_ip, dedip196_port) as processor_client:
        processor_client.send('Connected to run_processor')
        processor_client.receive()
        processor_client.send_json(config.processor_info)

        processor_client.send('Run M3 Tracking HV7')
        processor_client.receive()
    print('donzo')


if __name__ == '__main__':
    main()

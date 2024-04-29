#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 8:58 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/daq_control.py

@author: Dylan Neff, Dylan
"""

import time

from Client import Client
from DAQController import DAQController


def main():
    server_ip, port = '192.168.10.1', 1100
    with Client(server_ip, port=port) as client:
        client.send('Hello')
        # res = client.wait_for_response()
        res = client.receive()
        print(res)
    print('donzo')


if __name__ == '__main__':
    main()

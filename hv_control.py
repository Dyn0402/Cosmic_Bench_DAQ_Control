#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 8:39 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/hv_control.py

@author: Dylan Neff, Dylan
"""

from Server import Server
from caen_hv_py.CAENHVController import CAENHVController


def main():
    port = 1100
    with Server(port=port) as server:
        res = server.wait_for_response()
        print(res)
        server.send('Hello there')
    print('donzo')


if __name__ == '__main__':
    main()

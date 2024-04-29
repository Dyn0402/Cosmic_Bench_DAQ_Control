#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 8:48 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/Client.py

@author: Dylan Neff, Dylan
"""

import socket
import time


class Client:
    def __init__(self, host, port=1100):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        print('Client closed')

    def start(self):
        while True:
            try:
                self.client.connect((self.host, self.port))
                print(f"Connected to {self.host}:{self.port}")
                break
            except ConnectionRefusedError:
                print(f"Failed to connect to {self.host}:{self.port}. Retrying...")
                time.sleep(1)

    def receive(self):
        data = self.client.recv(1024).decode()
        print(f"Received: {data}")
        return data

    def send(self, data):
        self.client.send(data.encode())
        print(f"Sent: {data}")

    def wait_for_response(self, timeout=100, check_interval=1):
        start = time.time()
        while time.time() - start < timeout:
            data = self.receive()
            if data != '':
                return data
            time.sleep(check_interval)
        return None
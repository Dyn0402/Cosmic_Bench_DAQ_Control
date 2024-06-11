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
import json


class Client:
    def __init__(self, host, port=1100):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.max_recv = 1024 * 1000  # Max bytes to receive
        self.silent = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        if not self.silent:
            print('Client closed')

    def start(self):
        # while True:
        try:
            self.client.connect((self.host, self.port))
            if not self.silent:
                print(f"Connected to {self.host}:{self.port}")
            # break
        except (ConnectionRefusedError, OSError) as e:
            # print(f"Failed to connect to {self.host}:{self.port}. Retrying...")
            # time.sleep(1)
            if not self.silent:
                print(f"Failed to connect to {self.host}:{self.port}. {e}")

    def receive(self):
        data = self.client.recv(self.max_recv).decode()
        if not self.silent:
            print(f"Received: {data}")
        return data

    def receive_json(self):
        data = b''
        while True:
            packet = self.client.recv(self.max_recv)
            data += packet
            if len(data) > self.max_recv:
                print(f'Max packet size of {self.max_recv} exceeded with {len(data)}, breaking early!!')
                break
        data = json.loads(data.decode())
        if not self.silent:
            print(f"Received: {data}")
        return data

    def send(self, data):
        self.client.send(data.encode())
        if not self.silent:
            print(f"Sent: {data}")

    def send_json(self, data):
        self.client.sendall(json.dumps(data).encode())
        if not self.silent:
            print(f"Sent: {data}")

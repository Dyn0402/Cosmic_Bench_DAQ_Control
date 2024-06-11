#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 8:41 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/Server.py

@author: Dylan Neff, Dylan
"""

import socket
import time
import json


class Server:
    def __init__(self, port=1100):
        self.port = port
        self.server_host = '0.0.0.0'
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket = None
        self.client_address = None
        self.max_recv = 1024 * 1000  # Max bytes to receive

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client_socket is not None:
            self.client_socket.close()
        self.server.close()
        print('Server closed')

    def start(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow immediate reuse of address
        self.server.bind((self.server_host, self.port))
        self.server.listen(1)
        print(f"Listening on {self.server_host}:{self.port}")
        self.accept_connection()

    def accept_connection(self):
        while True:
            try:
                self.client_socket, self.client_address = self.server.accept()
                print(f"{self.client_address[0]}:{self.client_address[1]} Connected")
                break
            except socket.error:
                print("Connection error. Retrying...")
                time.sleep(1)

    def receive(self):
        data = self.client_socket.recv(self.max_recv).decode()
        print(f"Received: {data}")
        return data

    def receive_json(self):
        data = b''
        while True:
            packet = self.client_socket.recv(self.max_recv)
            data += packet
            if len(data) > self.max_recv:
                print(f'Max packet size of {self.max_recv} exceeded with {len(data)}, breaking early!!')
                break
        data = json.loads(data.decode())
        print(f"Received: {data}")
        return data

    def send(self, data):
        self.client_socket.send(data.encode())
        print(f"Sent: {data}")

    def send_json(self, data):
        self.client_socket.sendall(json.dumps(data).encode())
        print(f"Sent: {data}")

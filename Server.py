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


class Server:
    def __init__(self, port=1100):
        self.port = port
        self.server_host = '0.0.0.0'
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket = None
        self.client_address = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client_socket is not None:
            self.client_socket.close()
        self.server.close()
        print('Server closed')

    def start(self):
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
        data = self.client_socket.recv(1024).decode()
        print(f"Received: {data}")
        return data

    def send(self, data):
        self.client_socket.send(data.encode())
        print(f"Sent: {data}")

    def wait_for_response(self, timeout=100, check_interval=1):
        start = time.time()
        while time.time() - start < timeout:
            data = self.receive()
            if data != '':
                return data
            time.sleep(check_interval)
        return None

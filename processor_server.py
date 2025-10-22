#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on October 22 7:35 PM 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/processor_server.py

@author: Dylan Neff, Dylan
"""

import sys
import threading
import queue
import time
from Processor import Processor
from Server import Server

# Global state
processor_thread = None
stop_event = threading.Event()
config_queue = queue.Queue()
current_config = None
current_config_lock = threading.Lock()


def processor_worker():
    """Background worker to process configs sequentially."""
    global stop_event, config_queue, current_config

    while True:
        config_path = config_queue.get()
        if config_path is None:
            with current_config_lock:
                current_config = None
            print("[Processor] Server shutting down.")
            break

        with current_config_lock:
            current_config = config_path

        print(f"[Processor] Starting new Processor for config: {config_path}")
        stop_event.clear()
        proc = Processor(config_path, stop_event)

        try:
            proc.process_on_the_fly()
        except Exception as e:
            print(f"[Processor] Error: {e}")
        finally:
            print(f"[Processor] Finished for config: {config_path}\n")
            with current_config_lock:
                current_config = None


def queue_monitor(interval: float = 10.0):
    """Prints queue and processor status periodically."""
    while True:
        with current_config_lock:
            curr = current_config
        running = not stop_event.is_set()
        qsize = config_queue.qsize()
        print(f"[Monitor] Queue size: {qsize}, Running: {running}, Current config: {curr}")
        time.sleep(interval)


def main():
    global processor_thread, stop_event, config_queue

    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        port = 1250

    # Start background processor and monitor threads
    processor_thread = threading.Thread(target=processor_worker, daemon=True)
    processor_thread.start()

    monitor_thread = threading.Thread(target=queue_monitor, args=(10.0,), daemon=True)
    monitor_thread.start()

    print(f"[Server] Processor Server started on port {port}")

    while True:
        try:
            with Server(port=port) as server:
                server.receive()
                server.send("Processor server connected")

                msg = server.receive()
                while msg and msg.lower() != "finished":
                    if msg.startswith("config "):
                        config_path = msg.replace("config ", "").strip()
                        print(f"[Server] Received config: {config_path}")

                        # Stop current processing if needed
                        if not config_queue.empty() or current_config:
                            print("[Server] Signaling current Processor to stop before switching configs...")
                            stop_event.set()

                        config_queue.put(config_path)
                        server.send(f"Queued new config for processing: {config_path}")

                    elif msg == "stop":
                        stop_event.set()
                        server.send("Stop signal sent to current processor")

                    elif msg == "status":
                        with current_config_lock:
                            curr = current_config
                        running = not stop_event.is_set()
                        qsize = config_queue.qsize()
                        server.send(f"Processor running: {running}, Queue size: {qsize}, Current config: {curr}")

                    else:
                        server.send("Unknown command. Try 'config <path>', 'stop', or 'status'.")

                    msg = server.receive()
        except Exception as e:
            print(f"[Server] Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()

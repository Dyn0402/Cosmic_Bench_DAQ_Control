#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 01 11:37 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/trigger_switch_control.py

@author: Dylan Neff, Dylan
"""

import sys
import time
import threading
import RPi.GPIO as GPIO
from Server import Server

# Globals for background trigger control
trigger_thread = None
stop_event = threading.Event()


def main():
    global trigger_thread, stop_event

    if len(sys.argv) == 3:
        port = int(sys.argv[1])
        gpio_pin = int(sys.argv[2])
    else:
        port, gpio_pin = 1100, 17
    while True:  # Keep the server listening forever
        try:  # If there is some error, just restart the server
            with Server(port=port) as server:  # Initialize server on specified port
                server.receive()  # Wait for client to connect
                server.send('Trigger switch control connected')

                res = server.receive()
                while 'Finished' not in res:
                    if 'on' in res:
                        trigger_switch('on', pin=gpio_pin)
                        server.send(f'Trigger switch turned on')
                    elif 'off' in res:
                        trigger_switch('off', pin=gpio_pin)
                        server.send(f'Trigger switch turned off')

                    elif 'send triggers' in res:
                        # Stop any currently running trigger thread first
                        if trigger_thread and trigger_thread.is_alive():
                            stop_event.set()
                            trigger_thread.join()

                        try:
                            parts = res.replace('send triggers', '').strip().split()
                            num_triggers = int(parts[0])
                            freq_hz = float(parts[1])
                            pulse_freq_ratio = float(parts[2])

                            stop_event.clear()
                            trigger_thread = threading.Thread(
                                target=send_triggers,
                                kwargs=dict(
                                    num_triggers=num_triggers,
                                    freq_hz=freq_hz,
                                    pulse_freq_ratio=pulse_freq_ratio,
                                    pin=gpio_pin,
                                    stop_event=stop_event,
                                ),
                                daemon=True
                            )
                            trigger_thread.start()
                            server.send(
                                f'Started sending {num_triggers} triggers at {freq_hz} Hz with pulse ratio {pulse_freq_ratio}')

                        except (IndexError, ValueError) as e:
                            server.send(f'Error parsing send triggers command: {e}')

                    elif 'stop triggers' in res:
                        if trigger_thread and trigger_thread.is_alive():
                            stop_event.set()
                            trigger_thread.join()
                            server.send('Stopped sending triggers')
                        else:
                            server.send('No trigger process is running')
                    # elif 'send triggers' in res:
                    #     try:
                    #         parts = res.replace('send triggers', '').strip().split()
                    #         num_triggers = int(parts[0])
                    #         freq_hz = float(parts[1])
                    #         pulse_freq_ratio = float(parts[2])
                    #         send_triggers(num_triggers=num_triggers, freq_hz=freq_hz,
                    #                       pulse_freq_ratio=pulse_freq_ratio, pin=gpio_pin)
                    #         server.send(f'Sent {num_triggers} triggers at {freq_hz} Hz with pulse ratio {pulse_freq_ratio}')
                    #     except (IndexError, ValueError) as e:
                    #         server.send(f'Error parsing send triggers command: {e}')
                    else:
                        server.send('Unknown Command')
                    res = server.receive()
        except Exception as e:
            print(f'Error: {e}')
        # if trigger_thread and trigger_thread.is_alive():
        #     stop_event.set()
        #     trigger_thread.join()
        # trigger_switch('on', pin=gpio_pin)  # Make sure to leave trigger on by default
        # GPIO.cleanup(gpio_pin)
    print('donzo')


def trigger_switch(state, pin=17):
    """
    Turn trigger switch on or off. Will invert the logic such that 0V allows trigger to fire while 3.3V blocks trigger.
    :param state: Either on or off
    :param pin: GPIO pin number to use
    :return:
    """
    if state == 'on':
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        # GPIO.output(pin, GPIO.LOW)
        GPIO.output(pin, GPIO.HIGH)
    elif state == 'off':
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        # GPIO.output(pin, GPIO.HIGH)
        GPIO.output(pin, GPIO.LOW)
    else:
        print('Unknown trigger switch state')


def send_triggers(num_triggers=100, freq_hz=10, pulse_freq_ratio=1, pulse_level='low', pin=17, stop_event=None,
                  report_interval=1.0):
    """
    Send a number of triggers at a given frequency.

    :param num_triggers: Number of triggers to send
    :param freq_hz: Frequency in Hz to send triggers
    :param pulse_freq_ratio: Ratio of pulse width to frequency period (0 < ratio <= 1)
    :param pulse_level: Level of the pulse, either 'low' or 'high'
    :param pin: GPIO pin number to use
    :param stop_event: threading.Event to allow early stop (optional)
    :param report_interval: seconds between printing the current trigger number (None or <=0 to disable)
    :return:
    """
    period = 1.0 / freq_hz
    pulse_length = period * pulse_freq_ratio / (pulse_freq_ratio + 1)
    delay = period - pulse_length
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)

    last_report = time.perf_counter()
    try:
        for i in range(1, num_triggers + 1):
            if stop_event and stop_event.is_set():
                break

            if pulse_level == 'low':
                GPIO.output(pin, GPIO.LOW)
            else:
                GPIO.output(pin, GPIO.HIGH)

            time.sleep(pulse_length)

            if pulse_level == 'low':
                GPIO.output(pin, GPIO.HIGH)
            else:
                GPIO.output(pin, GPIO.LOW)

            time.sleep(delay)

            if report_interval and report_interval > 0 and (time.perf_counter() - last_report) >= report_interval:
                print(f'Trigger {i}')
                last_report = time.perf_counter()
    finally:
        GPIO.cleanup(pin)


if __name__ == '__main__':
    main()

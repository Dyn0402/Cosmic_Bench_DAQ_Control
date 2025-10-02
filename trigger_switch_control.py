#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 01 11:37 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/trigger_switch_control.py

@author: Dylan Neff, Dylan
"""

import time
import RPi.GPIO as GPIO
from Server import Server


def main():
    port, gpio_pin = 1100, 17
    while True:
        try:
            with Server(port=port) as server:
                server.receive()
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
                        try:
                            parts = res.strip().split()
                            num_triggers = int(parts[2])
                            freq_hz = float(parts[3])
                            pulse_freq_ratio = float(parts[4])
                            pulse_level = parts[5]
                            send_triggers(num_triggers=num_triggers, freq_hz=freq_hz,
                                          pulse_freq_ratio=pulse_freq_ratio, pulse_level=pulse_level, pin=gpio_pin)
                            server.send(f'Sent {num_triggers} triggers at {freq_hz} Hz with pulse ratio {pulse_freq_ratio} and level {pulse_level}')
                        except (IndexError, ValueError) as e:
                            server.send(f'Error parsing send triggers command: {e}')
                    else:
                        server.send('Unknown Command')
                    res = server.receive()
        except Exception as e:
            print(f'Error: {e}')
        trigger_switch('on', pin=gpio_pin)  # Make sure to leave trigger on by default
        GPIO.cleanup()
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


def send_triggers(num_triggers=100, freq_hz=10, pulse_freq_ratio=1, pulse_level='low', pin=17):
    """
    Send a number of triggers at a given frequency
    :param num_triggers: Number of triggers to send
    :param freq_hz: Frequency in Hz to send triggers
    :param pulse_freq_ratio: Ratio of pulse width to frequency period (0 < ratio <= 1)
    :param pulse_level: Level of the pulse, either 'low' or 'high'
    :param pin: GPIO pin number to use
    :return:
    """
    period = 1.0 / freq_hz
    pulse_length = period * pulse_freq_ratio / (pulse_freq_ratio + 1)
    delay = period - pulse_length
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    for _ in range(num_triggers):
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
    GPIO.cleanup()


if __name__ == '__main__':
    main()

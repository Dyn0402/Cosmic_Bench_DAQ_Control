#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 01 11:37 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/trigger_switch_control.py

@author: Dylan Neff, Dylan
"""

from Server import Server
import RPi.GPIO as GPIO


def main():
    port, gpio_pin = 1100, 17
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
            else:
                server.send('Unknown Command')
            res = server.receive()
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
        GPIO.output(pin, GPIO.LOW)
    elif state == 'off':
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
    else:
        print('Unknown trigger switch state')


if __name__ == '__main__':
    main()

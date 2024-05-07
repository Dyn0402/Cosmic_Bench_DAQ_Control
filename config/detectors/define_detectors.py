#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 07 12:21 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/define_detectors.py

@author: Dylan Neff, Dylan
"""

import json


def main():
    detectors = define_dets()
    write_detectors(detectors)
    print('donzo')


def define_dets():
    detectors = [
        {
            'name': 'banco',
            'strip_map_type': 'banco',
            'resist_map_type': 'banco',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'name': 'urw_strip',
            'strip_map_type': 'strip',
            'resist_map_type': 'plein',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'name': 'urw_inter',
            'strip_map_type': 'inter',
            'resist_map_type': 'plein',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'name': 'asacusa_strip_1',
            'strip_map_type': 'asacusa',
            'resist_map_type': 'strip',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'name': 'asacusa_strip_2',
            'strip_map_type': 'asacusa',
            'resist_map_type': 'strip',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'name': 'asacusa_plein_1',
            'strip_map_type': 'asacusa',
            'resist_map_type': 'plein',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'name': 'm3_bot_bot',
            'strip_map_type': 'm3',
            'resist_map_type': 'm3',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 500,  # mm
                'y': 500,  # mm
                'z': 4,  # mm  Guess
            },
        },
        {
            'name': 'm3_bot_top',
            'strip_map_type': 'm3',
            'resist_map_type': 'm3',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 500,  # mm
                'y': 500,  # mm
                'z': 4,  # mm  Guess
            },
        },
        {
            'name': 'm3_top_bot',
            'strip_map_type': 'm3',
            'resist_map_type': 'm3',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 500,  # mm
                'y': 500,  # mm
                'z': 4,  # mm  Guess
            },
        },
        {
            'name': 'm3_top_top',
            'strip_map_type': 'm3',
            'resist_map_type': 'm3',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 500,  # mm
                'y': 500,  # mm
                'z': 4,  # mm  Guess
            },
        },
    ]

    return detectors


def write_detectors(detectors):
    for detector in detectors:
        with open(f'{detector["name"]}.json', 'w') as file:
            json.dump(detector, file, indent=4)


if __name__ == '__main__':
    main()

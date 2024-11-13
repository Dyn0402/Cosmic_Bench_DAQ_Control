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
            'det_type': 'banco',
            'strip_map_type': 'banco',
            'resist_map_type': 'banco',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 15,  # mm
                'y': 150,  # mm
                'z': 2,  # mm
            },
        },
        {
            'det_type': 'urw_strip',
            'strip_map_type': 'strip',
            'resist_map_type': 'plein',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'urw_inter',
            'strip_map_type': 'inter',
            'resist_map_type': 'plein',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'asacusa_grid',
            'strip_map_type': 'asacusa',
            'resist_map_type': 'grid',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'asacusa_strip',
            'strip_map_type': 'asacusa',
            'resist_map_type': 'strip',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'asacusa_plein',
            'strip_map_type': 'asacusa',
            'resist_map_type': 'plein',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'strip_grid',
            'strip_map_type': 'strip',
            'resist_map_type': 'grid',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'strip_strip',
            'strip_map_type': 'strip',
            'resist_map_type': 'strip',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'strip_plein',
            'strip_map_type': 'strip',
            'resist_map_type': 'plein',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'inter_grid',
            'strip_map_type': 'inter',
            'resist_map_type': 'grid',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'inter_strip',
            'strip_map_type': 'inter',
            'resist_map_type': 'strip',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'inter_plein',
            'strip_map_type': 'inter',
            'resist_map_type': 'plein',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 130,  # mm
                'y': 130,  # mm
                'z': 4,  # mm
            },
        },
        {
            'det_type': 'm3',
            'strip_map_type': 'm3',
            'resist_map_type': 'm3',
            'det_size': {  # Size of detector based on the extent of the readout pads (active area may be smaller)
                'x': 500,  # mm
                'y': 500,  # mm
                'z': 4,  # mm  Guess
            },
        },
        {
            'det_type': 'scintillator',
            'strip_map_type': 'scintillator',
            'resist_map_type': 'scintillator',
            'det_size': {  # Roughly
                'x': 600,  # mm
                'y': 600,  # mm
                'z': 4,  # mm  Guess
            },
        },
    ]

    return detectors


def write_detectors(detectors):
    for detector in detectors:
        with open(f'{detector["det_type"]}.json', 'w') as file:
            json.dump(detector, file, indent=4)


if __name__ == '__main__':
    main()

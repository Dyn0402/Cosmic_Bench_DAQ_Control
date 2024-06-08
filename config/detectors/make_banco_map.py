#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on June 07 1:31 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/make_banco_map.py

@author: Dylan Neff, Dylan
"""

import numpy as np


def main():
    print('donzo')


def make_banco_map_file():
    """
    Make map file for banco detector to convert pixel rows and columns to x and y coordinates.
    y corresponds to long dimension (columns) and x to short (rows)
    chips are stacked in long dimension
    :return:
    """
    n_pix_x = 512
    n_pix_y = 1024
    n_chips = 5

    lines = [f'N Chip (0-{n_chips - 1})\tRow (0-{n_pix_x - 1}\tColumn (0-{n_pix_y - 1}\tx (mm)\ty (mm)\n']
    for chip in range(n_chips):
        for col in range(n_pix_y):
            for row in range(n_pix_x):
                x, y = convert_row_col_to_xy(row, col, chip)
                lines.append(f'{chip}\t{row}\t{col}\t{x}\t{y}\n')


def convert_row_col_to_xy(row, col, chip):
    """
    Given a row, column, and chip number, return the x and y coordinates of the pixel.
    :param row: Row pixel number, 0-511
    :param col: Column pixel number, 0-1023
    :param chip: Chip number, 0-4
    :return:
    """
    # n_pix_x = 512
    n_pix_y = 1024
    # n_chips = 5
    chip_space = 15  # um Space between chips
    pix_size_x = 30  # um
    pix_size_y = 30  # um

    x = row * pix_size_x
    y = col * pix_size_y + chip * n_pix_y * pix_size_y + chip_space * chip


if __name__ == '__main__':
    main()

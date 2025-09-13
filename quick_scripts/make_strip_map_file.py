#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 11 17:47 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/make_strip_map_file

@author: Dylan Neff, dn277127
"""

import numpy as np
import pandas as pd


def main():
    # Load your original file
    # df = pd.read_csv("strip_map_template.txt")
    #
    # # Reset pitches according to axis
    # df.loc[df["axis"] == "y", "pitch(mm)"] = 1.0
    # df.loc[df["axis"] == "y", "interpitch(mm)"] = 0.7
    # df.loc[df["axis"] == "x", "pitch(mm)"] = 1.2
    # df.loc[df["axis"] == "x", "interpitch(mm)"] = 0.125
    #
    # # For Gerber coordinates, regenerate systematically
    # # Group by (connector, axis) so each connector orientation gets consistent spacing
    # new_rows = []
    # for (conn, axis), group in df.groupby(["connector", "axis"]):
    #     group = group.sort_values("connectorChannel")  # ensure order
    #     if axis == "y":
    #         start_x = group.iloc[0]["xGerber"]  # keep first as reference
    #         for i, row in enumerate(group.itertuples()):
    #             row_dict = row._asdict()
    #             row_dict["xGerber"] = start_x + i * 1.0  # pitch = 1.0 mm
    #             new_rows.append(row_dict)
    #     else:  # axis == "x"
    #         start_y = group.iloc[0]["yGerber"]
    #         for i, row in enumerate(group.itertuples()):
    #             row_dict = row._asdict()
    #             row_dict["yGerber"] = round(start_y + i * 1.2, 2)  # pitch = 1.2 mm
    #             new_rows.append(row_dict)
    #
    # # Convert back to DataFrame
    # new_df = pd.DataFrame(new_rows)
    #
    # # Drop index column (from _asdict)
    # new_df = new_df.drop(columns=["Index"], errors="ignore")
    # print(new_df.head())
    # print(new_df.columns)
    #
    # # Save
    # # new_df.to_csv("rd542_map.txt", index=False)

    # Load original file
    df = pd.read_csv("strip_map_template.txt")

    # Reset pitches according to axis
    df.loc[df["axis"] == "y", ["pitch(mm)", "interpitch(mm)"]] = [1.0, 0.7]
    df.loc[df["axis"] == "x", ["pitch(mm)", "interpitch(mm)"]] = [1.2, 0.125]

    # Y-axis strips → step xGerber
    mask_y = df["axis"] == "y"
    start_x = df.loc[mask_y, "xGerber"].min()
    df.loc[mask_y, "xGerber"] = start_x + np.arange(mask_y.sum()) * 1.0

    # X-axis strips → step yGerber
    mask_x = df["axis"] == "x"
    start_y = df.loc[mask_x, "yGerber"].min()
    df.loc[mask_x, "yGerber"] = start_y + np.arange(mask_x.sum()) * 1.2

    df = df.round(3)

    # # Update Gerber coordinates systematically
    # for axis, group in df.groupby(["axis"]):
    #     # group = group.sort_values("connectorChannel")  # order within group
    #     if axis == "y":
    #         new_vals = start_x + np.arange(len(group)) * 1.0
    #         df.loc[group.index, "xGerber"] = new_vals
    #     else:  # axis == "x"
    #         new_vals = start_y + np.arange(len(group)) * 1.2
    #         df.loc[group.index, "yGerber"] = new_vals

    # Save to CSV
    df.to_csv("rd542_map.txt", index=False)

    print('donzo')


if __name__ == '__main__':
    main()

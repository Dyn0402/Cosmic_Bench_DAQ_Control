#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3 filtering functions for cosmic bench processor.
Filters decoded ROOT files to keep only events with tracks traversing the DUT.
"""

import os
import json
import shutil
import numpy as np

from common_functions import get_file_num_from_fdf_file_name, get_run_name_from_fdf_file_name
from M3RefTracking import M3RefTracking


def filter_decoded_by_m3(out_dir, m3_tracking_dir, decoded_dir, detectors, det_info_dir,
                          included_detectors=None, file_num=None):
    """
    Filter decoded ROOT files by events with M3 tracks traversing any included detector.
    Writes filtered ROOT files to out_dir.
    """
    import ROOT

    for m3_file in os.listdir(m3_tracking_dir):
        if not m3_file.endswith('_rays.root') or '_datrun_' not in m3_file:
            continue
        fnum = get_file_num_from_fdf_file_name(m3_file, -1)
        if file_num is not None and fnum != file_num:
            continue

        print(f'\n\nFiltering decoded files by M3 tracking in {m3_file}')
        run_name = get_run_name_from_fdf_file_name(m3_file)
        detector_geometries = get_detector_geometries(detectors, det_info_dir, included_detectors)
        traversing_event_ids = get_m3_det_traversing_events(m3_tracking_dir, detector_geometries, file_nums=[fnum])

        for det_file in os.listdir(decoded_dir):
            if not det_file.endswith('.root') or '_datrun_' not in det_file:
                continue
            if get_file_num_from_fdf_file_name(det_file, -2) != fnum:
                continue
            if get_run_name_from_fdf_file_name(det_file) != run_name:
                continue
            out_file_name = det_file.replace('.root', '_filtered.root')
            if os.path.exists(os.path.join(out_dir, out_file_name)):
                continue
            print(f'Filtering {det_file} -> {out_file_name}')
            filter_dream_file_pyroot(
                os.path.join(decoded_dir, det_file),
                traversing_event_ids,
                os.path.join(out_dir, out_file_name),
                event_branch_name='eventId'
            )


def copy_decoded_to_filtered(out_dir, decoded_dir, file_num=None):
    """When not filtering, copy decoded files to filtered directory (rename with _filtered suffix)."""
    for det_file in os.listdir(decoded_dir):
        if not det_file.endswith('.root') or '_datrun_' not in det_file:
            continue
        if file_num is not None and get_file_num_from_fdf_file_name(det_file, -2) != file_num:
            continue
        out_file_name = det_file.replace('.root', '_filtered.root')
        out_path = os.path.join(out_dir, out_file_name)
        if os.path.exists(out_path):
            continue
        shutil.copy(os.path.join(decoded_dir, det_file), out_path)


def get_m3_det_traversing_events(ray_directory, detector_geometries, file_nums=None, det_bound_cushion=0.08):
    """
    Return event IDs of events with tracks traversing any detector in detector_geometries.
    """
    m3_track_data = M3RefTracking(ray_directory, file_nums=file_nums)
    masks = []
    for detector in detector_geometries:
        x, y, event_nums = m3_track_data.get_xy_positions(detector['z'])
        x_range = detector['x_max'] - detector['x_min']
        y_range = detector['y_max'] - detector['y_min']
        x_min = detector['x_min'] - x_range * det_bound_cushion
        x_max = detector['x_max'] + x_range * det_bound_cushion
        y_min = detector['y_min'] - y_range * det_bound_cushion
        y_max = detector['y_max'] + y_range * det_bound_cushion
        masks.append((x > x_min) & (x < x_max) & (y > y_min) & (y < y_max))
    mask = np.any(masks, axis=0)
    return m3_track_data.ray_data['evn'][mask]


def get_detector_geometries(detectors, det_info_dir, included_detectors=None):
    """
    Build detector geometry list from run config detectors for M3 traversal check.
    """
    if included_detectors is None:
        included_detectors = [det['name'] for det in detectors]
    detector_geometries = []
    for det in detectors:
        if det['name'] not in included_detectors:
            continue
        if det['det_type'] in ('m3', 'scintillator'):
            continue
        det_info_path = os.path.join(det_info_dir, f'{det["det_type"]}.json')
        with open(det_info_path, 'r') as f:
            det_info = json.load(f)
        x_size = det_info['det_size']['x']
        y_size = det_info['det_size']['y']
        z = det['det_center_coords']['z']
        x_center = det['det_center_coords']['x']
        y_center = det['det_center_coords']['y']
        x_angle = det['det_orientation']['x']
        y_angle = det['det_orientation']['y']
        z_angle = det['det_orientation']['z']
        x_min, x_max, y_min, y_max = get_xy_max_min(x_size, y_size, x_center, y_center, x_angle, y_angle, z_angle)
        detector_geometries.append({
            'z': z, 'x_min': x_min, 'x_max': x_max, 'y_min': y_min, 'y_max': y_max,
            'det_name': det['name']
        })
    return detector_geometries


def filter_dream_file_pyroot(file_path, events, out_file_path, event_branch_name='evn'):
    """Filter a decoded ROOT file, keeping only events whose ID is in events."""
    import ROOT
    in_file = ROOT.TFile.Open(file_path, 'READ')
    in_tree_name = [x.ReadObj().GetName() for x in in_file.GetListOfKeys()][0]
    in_tree = in_file.Get(in_tree_name)

    out_file = ROOT.TFile(out_file_path, 'RECREATE')
    out_tree = in_tree.CloneTree(0)

    events = sorted(list(events))
    event_num_branch = in_tree.GetBranch(event_branch_name)
    event_num_leaf = event_num_branch.GetLeaf(event_branch_name)

    for i in range(in_tree.GetEntries()):
        if not events:
            break
        in_tree.GetEntry(i)
        event_num = int(event_num_leaf.GetValue())
        while events and events[0] < event_num:
            events.pop(0)
        if events and events[0] == event_num:
            out_tree.Fill()
            events.pop(0)

    out_file.Write()
    out_file.Close()
    in_file.Close()


def get_xy_max_min(x_size, y_size, x_center, y_center, x_angle, y_angle, z_angle):
    x_corners = np.array([-x_size / 2, x_size / 2, x_size / 2, -x_size / 2])
    y_corners = np.array([-y_size / 2, -y_size / 2, y_size / 2, y_size / 2])
    z_corners = np.zeros(4)
    x_corners, y_corners, z_corners = _rotate_3d(x_corners, y_corners, z_corners, x_angle, y_angle, z_angle)
    x_corners += x_center
    y_corners += y_center
    return np.min(x_corners), np.max(x_corners), np.min(y_corners), np.max(y_corners)


def _rotate_3d(x, y, z, x_angle, y_angle, z_angle):
    y, z = _rotate_2d(y, z, x_angle)
    x, z = _rotate_2d(x, z, y_angle)
    x, y = _rotate_2d(x, y, z_angle)
    return x, y, z


def _rotate_2d(x, y, angle):
    x_rot = x * np.cos(angle) - y * np.sin(angle)
    y_rot = x * np.sin(angle) + y * np.cos(angle)
    return x_rot, y_rot

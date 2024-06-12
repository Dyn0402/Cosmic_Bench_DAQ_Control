#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 09 17:11 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/dedip196_processing_control

@author: Dylan Neff, dn277127
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime
import numpy as np
import json

import uproot
import awkward as ak

from Server import Server
from common_functions import *
from M3RefTracking import M3RefTracking

print('Importing pyROOT...')
import ROOT
print('pyROOT imported')


def main():
    port = 1200
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f'Invalid port number {sys.argv[1]}. Using default port {port}')
    options = ['Decode FDFs', 'Run M3 Tracking', 'Filter By M3', 'Clean Up Unfiltered']
    while True:
        try:
            with Server(port=port) as server:
                server.receive()
                server.send('Processing control connected')
                run_info = server.receive_json()
                server.send('Received run info')
                run_info.update(server.receive_json())  # Update run info with included detectors
                server.send('Received included detectors')
                run_info.update(server.receive_json())  # Update run info with detector info
                server.send('Received detector info')

                res = server.receive()
                while 'Finished' not in res:
                    run_options = [option for option in options if option in res]
                    if len(run_options) == 0:
                        server.send('Unknown Command')
                    else:
                        server.send(f"{' and '.join(run_options)} Started...")
                        sub_run = res.strip().split()[-1]
                        sub_run_dir = f"{run_info['run_dir']}/{sub_run}/"
                        fdf_dir = f"{sub_run_dir}{run_info['raw_daq_inner_dir']}/"
                        if 'Decode FDFs' in run_options:
                            out_dir = f"{sub_run_dir}{run_info['decoded_root_inner_dir']}/"
                            create_dir_if_not_exist(out_dir)
                            print(f'\n\nDecoding FDFs in {fdf_dir} to {out_dir}')
                            decode_fdfs(fdf_dir, run_info['decode_path'], run_info['convert_path'], out_dir,
                                        out_type=run_info['out_type'])
                            print('Decoding Complete')
                        if 'Run M3 Tracking' in run_options:
                            out_dir = f"{sub_run_dir}{run_info['m3_tracking_inner_dir']}/"
                            create_dir_if_not_exist(out_dir)
                            print(f'\n\nRunning M3 Tracking on FDFs in {fdf_dir} to {out_dir}')
                            m3_tracking(fdf_dir, run_info['tracking_sh_path'], run_info['tracking_run_dir'], out_dir)
                            print('M3 Tracking Complete')
                        if 'Filter By M3' in run_options:
                            decoded_dir = f"{sub_run_dir}{run_info['decoded_root_inner_dir']}/"
                            m3_tracking_dir = f"{sub_run_dir}{run_info['m3_tracking_inner_dir']}/"
                            out_dir = f"{sub_run_dir}{run_info['filtered_root_inner_dir']}/"
                            create_dir_if_not_exist(out_dir)
                            print(f'\n\nFiltering decoded files in {decoded_dir} by M3 tracking in {out_dir}')
                            filter_by_m3(out_dir, m3_tracking_dir, decoded_dir, run_info['detectors'],
                                         run_info['detector_info_dir'], run_info['included_detectors'])
                            print('Filtering Complete')
                        if 'Clean Up Unfiltered' in run_options:
                            decoded_dir = f"{sub_run_dir}{run_info['decoded_root_inner_dir']}/"
                            remove_files(fdf_dir, 'fdf')  # Raw dream fdfs
                            remove_files(decoded_dir)  # Decoded but unfiltered root files
                    res = server.receive()
        except TypeError as e:
            print(f'Error: {e}\nRestarting processing control server...')
    print('donzo')


def decode_fdfs(fdf_dir, decode_path, convert_path=None, out_dir=None, feu_nums='all', fdf_type='all', out_type='vec'):
    """
    Decode fdfs from a directory.
    :param fdf_dir: Directory containing fdf files
    :param decode_path:
    :param convert_path:
    :param out_dir:
    :param feu_nums:
    :param fdf_type:
    :param out_type: 'vec', 'array', or both
    :return:
    """
    og_dir = os.getcwd()
    if out_dir is None:
        os.chdir(fdf_dir)
    else:
        os.chdir(out_dir)

    for file in os.listdir(fdf_dir):
        if not file.endswith('.fdf'):
            continue
        if isinstance(feu_nums, list):
            fdf_num = get_feu_num_from_fdf_file_name(file)
            if fdf_num not in feu_nums:
                continue
        if fdf_type != 'all':
            if fdf_type not in file.split('_'):
                continue
        out_name = file.replace('.fdf', '_decoded.root')
        command = f"{decode_path} {fdf_dir}{file} {out_name}"
        print(f'\nDecoding {file} to {out_name}')
        print(command)
        os.system(command)
        os.chmod(out_name, 0o777)
        if out_type in ['array', 'both']:
            if convert_path is None:
                print('Error! Need convert path for vec->array! Skipping')
            else:
                array_out_name = out_name.replace('.root', '_array.root')
                command = f"{convert_path} {out_name} {array_out_name}"
                print(command)
                os.system(command)
                os.chmod(array_out_name, 0o777)
            if out_type == 'array':  # Remove vector formatted root file
                os.remove(out_name)

    os.chdir(og_dir)


def m3_tracking(fdf_dir, tracking_sh_ref_path, tracking_run_dir, out_dir=None, m3_fdf_num=1):
    """

    :param fdf_dir:
    :param tracking_sh_ref_path:
    :param tracking_run_dir:
    :param out_dir:
    :param m3_fdf_num:
    :return:
    """
    for file in os.listdir(fdf_dir):
        if not file.endswith('.fdf') or '_datrun_' not in file:
            continue
        feu_num = get_feu_num_from_fdf_file_name(file)
        if feu_num != m3_fdf_num:
            continue
        run_name = get_run_name_from_fdf_file_name(file)
        file_num = get_file_num_from_fdf_file_name(file, -1)
        out_dir = fdf_dir if out_dir is None else out_dir
        get_rays_from_fdf(run_name, tracking_sh_ref_path, [file_num], out_dir, tracking_run_dir, verbose=True,
                          fdf_dir=fdf_dir)


def filter_by_m3(out_dir, m3_tracking_dir, decoded_dir, detectors, det_info_dir, included_detectors=None):
    for m3_file in os.listdir(m3_tracking_dir):
        if not m3_file.endswith('_rays.root') or '_datrun_' not in m3_file:
            continue
        print(f'\n\nFiltering decoded files by M3 tracking in {m3_file}')
        run_name = get_run_name_from_fdf_file_name(m3_file)
        file_num = get_file_num_from_fdf_file_name(m3_file, -1)
        detector_geometries = get_detector_geometries(detectors, det_info_dir, included_detectors)
        traversing_event_ids = get_m3_det_traversing_events(m3_tracking_dir, detector_geometries, file_nums=[file_num])
        for det_file in os.listdir(decoded_dir):
            if not det_file.endswith('_array.root') or '_datrun_' not in det_file:
                continue
            if get_file_num_from_fdf_file_name(det_file, -2) != file_num:
                continue
            if get_run_name_from_fdf_file_name(det_file) != run_name:
                continue
            print(f'Filtering {det_file} to {det_file.replace("_array", "_traversing")}')
            filter_dream_file_pyroot(f'{decoded_dir}{det_file}', traversing_event_ids,
                                     f'{out_dir}{det_file.replace("_array", "_traversing")}',
                                     event_branch_name='eventId')


def get_m3_det_traversing_events(ray_directory, detector_geometries, file_nums=None, det_bound_cushion=0.08):
    """
    Get event ids of events traversing any of the detectors in detector_geometries.
    :param ray_directory: Path to directory containing m3 tracking files
    :param detector_geometries: List of detector geometries to check for traversing events
    :param file_nums: List of file numbers to check for traversing events. If 'all', check all files in directory.
    :param det_bound_cushion: Fractional cushion to add to detector bounds
    :return: List of event ids of events traversing any of the detectors
    """
    m3_track_data = M3RefTracking(ray_directory, file_nums=file_nums)
    masks = []
    for detector in detector_geometries:
        x, y, event_nums = m3_track_data.get_xy_positions(detector['z'])
        x_range, y_range = detector['x_max'] - detector['x_min'], detector['y_max'] - detector['y_min']
        x_min, x_max = detector['x_min'] - x_range * det_bound_cushion, detector['x_max'] + x_range * det_bound_cushion
        y_min, y_max = detector['y_min'] - y_range * det_bound_cushion, detector['y_max'] + y_range * det_bound_cushion
        masks.append((x > x_min) & (x < x_max) & (y > y_min) & (y < y_max))
    mask = np.any(masks, axis=0)
    event_ids = m3_track_data.ray_data['evn'][mask]
    return event_ids


def get_detector_geometries(detectors, det_info_dir, included_detectors=None):
    """
    Get detector geometries from run data in a format easier to check for traversing tracks.
    :param detectors: List of all detectors in config file with all run info, including geometry
    :param det_info_dir: Directory containing detector info files
    :param included_detectors: List of detectors to include in check. If None, all detectors are included.
    :return:
    """
    if included_detectors is None:
        included_detectors = [det['name'] for det in detectors]
    detector_geometries = []
    for det in detectors:
        if det['name'] in included_detectors and det['det_type'] != 'm3':
            det_info_path = f'{det_info_dir}{det["det_type"]}.json'
            with open(det_info_path, 'r') as file:
                det_info = json.load(file)
            x_size, y_size = det_info['det_size']['x'], det_info['det_size']['y']
            z = det['det_center_coords']['z']
            x_center, y_center = det['det_center_coords']['x'], det['det_center_coords']['y']
            x_angle, y_angle, z_angle = [det['det_orientation'][key] for key in ['x', 'y', 'z']]
            x_min, x_max, y_min, y_max = get_xy_max_min(x_size, y_size, x_center, y_center, x_angle, y_angle, z_angle)
            det_geom = {'z': z, 'x_min': x_min, 'x_max': x_max, 'y_min': y_min, 'y_max': y_max, 'det_name': det['name']}
            detector_geometries.append(det_geom)
    return detector_geometries


def get_xy_max_min(x_size, y_size, x_center, y_center, x_angle, y_angle, z_angle):
    """
    Get the min and max x and y values of a detector given its size, center, and orientation.
    :param x_size: Size of detector in x direction
    :param y_size: Size of detector in y direction
    :param x_center: Center of detector in x direction
    :param y_center: Center of detector in y direction
    :param x_angle: Angle of detector in x direction
    :param y_angle: Angle of detector in y direction
    :param z_angle: Angle of detector in z direction
    :return:
    """
    # Calculate x, y, z coordinates of detector corners
    x_corners = np.array([-x_size / 2, x_size / 2, x_size / 2, -x_size / 2])
    y_corners = np.array([-y_size / 2, -y_size / 2, y_size / 2, y_size / 2])
    z_corners = np.array([0, 0, 0, 0])
    x_corners, y_corners, z_corners = rotate_3d(x_corners, y_corners, z_corners, x_angle, y_angle, z_angle)
    x_corners += x_center
    y_corners += y_center
    # Get min and max x, y values
    x_min, x_max = np.min(x_corners), np.max(x_corners)
    y_min, y_max = np.min(y_corners), np.max(y_corners)
    return x_min, x_max, y_min, y_max


def rotate_3d(x, y, z, x_angle, y_angle, z_angle):
    """
    Rotate 3d coordinates about the x, y, and z axes.
    :param x: x coordinates
    :param y: y coordinates
    :param z: z coordinates
    :param x_angle: Angle to rotate about x axis
    :param y_angle: Angle to rotate about y axis
    :param z_angle: Angle to rotate about z axis
    :return: Rotated x, y, z coordinates
    """
    # Rotate about x axis
    y, z = rotate_2d(y, z, x_angle)
    # Rotate about y axis
    x, z = rotate_2d(x, z, y_angle)
    # Rotate about z axis
    x, y = rotate_2d(x, y, z_angle)
    return x, y, z


def rotate_2d(x, y, angle):
    """
    Rotate 2d coordinates about the z axis.
    :param x: x coordinates
    :param y: y coordinates
    :param angle: Angle to rotate about z axis
    :return: Rotated x, y coordinates
    """
    x_rot = x * np.cos(angle) - y * np.sin(angle)
    y_rot = x * np.sin(angle) + y * np.cos(angle)
    return x_rot, y_rot


def filter_dream_file_uproot(file_path, events, out_file_path, event_branch_name='evn'):
    """
    DOESN'T WORK. Uproot can't write trees it reads.
    :param file_path: Path to dream file to filter
    :param events: List of events to keep
    :param out_file_path: Path to write filtered dream file
    :param event_branch_name: Name of event branch in dream file
    :return:
    """
    with uproot.open(file_path) as file:
        tree_name = f"{file.keys()[0].split(';')[0]};{max([int(key.split(';')[-1]) for key in file.keys()])}"
        tree = file[tree_name]
        data = tree.arrays(library='ak')
        tree_events = ak.to_numpy(data[event_branch_name])
        mask = np.isin(events, tree_events)
        data = data[mask]
        # for key in data.keys():
        #     data[key] = data[key][mask]
        with uproot.recreate(out_file_path) as out_file:
            out_file[tree_name] = data


def filter_dream_file_pyroot(file_path, events, out_file_path, event_branch_name='evn'):
    """
    Filter a decoded dream file based on a list of events. Shame that uproot doesn't work, because this is a slow
    python loop.
    :param file_path: Path to dream file to filter
    :param events: List of events to keep
    :param out_file_path: Path to write filtered dream file
    :param event_branch_name: Name of event branch in dream file
    :return:
    """
    in_file = ROOT.TFile.Open(file_path, 'READ')
    in_tree_name = [x.ReadObj().GetName() for x in in_file.GetListOfKeys()][0]
    in_tree = in_file.Get(in_tree_name)

    out_file = ROOT.TFile(out_file_path, 'RECREATE')
    out_tree = in_tree.CloneTree(0)

    event_num_branch = in_tree.GetBranch(event_branch_name)

    for i in range(in_tree.GetEntries()):
        in_tree.GetEntry(i)
        event_id = event_num_branch.GetLeaf(event_branch_name).GetValue()
        if event_id in events:
            out_tree.Fill()

    out_file.Write()
    out_file.Close()
    in_file.Close()


def get_rays_from_fdf(fdf_run, tracking_sh_file, file_nums, output_root_dir, run_dir, verbose=False, fdf_dir=None):
    """
    Get rays from fdf files and write to root file.
    :param fdf_run:
    :param tracking_sh_file:
    :param file_nums:
    :param output_root_dir:
    :param run_dir:
    :param verbose:
    :param fdf_dir:
    :return:
    """
    og_dir = os.getcwd()
    os.chdir(run_dir)
    for i in file_nums:
        print(f'Processing file {i} of {len(file_nums)} for run {fdf_run}...')
        ped_in_dir = fdf_dir if fdf_dir is not None else None
        data_in_dir = fdf_dir if fdf_dir is not None else None
        temp_sh_file = make_temp_sh_file(fdf_run, tracking_sh_file, i, 'tracking',
                                         ped_in_dir=ped_in_dir, data_in_dir=data_in_dir)

        # Construct the final command based on verbosity
        if not verbose:
            cmd = f'{temp_sh_file} > /dev/null'
        else:
            cmd = f'{temp_sh_file}'

        print(f'Running command: {cmd}')

        # os.system(cmd)
        subprocess.run(cmd, shell=True)

        out_root_path = f'{output_root_dir}{fdf_run}_{i:03d}_rays.root'
        shutil.move(f'output_{i:03d}.root', out_root_path)
        os.chmod(out_root_path, 0o777)
    os.chdir(og_dir)


def make_temp_sh_file(fdf_run, ref_sh_file, file_num, sh_file_type='tracking', feu='01',
                      ped_in_dir=None, data_in_dir=None):
    """
    Make the tracking shell script file to run the tracking program from reference file.
    :param fdf_run:
    :param ref_sh_file:
    :param file_num:
    :param sh_file_type:
    :param feu:
    :param ped_in_dir:
    :param data_in_dir:
    :return:
    """
    # Copy tracking_sh_file to new file
    temp_file_name = ref_sh_file.replace('.sh', f'_{sh_file_type}_temp.sh')
    if os.path.exists(temp_file_name):
        os.remove(temp_file_name)
    shutil.copy(ref_sh_file, temp_file_name)
    with open(temp_file_name, 'r') as file:
        file_text = file.read()
    # Replace reference fdf file in tracking_sh_file with ref_fdf_file
    file_text = file_text.replace('CosTb_380V_stats_datrun_240212_11H42', fdf_run)
    file_text = file_text.replace('CosTb_380V_stats_pedthr_240212_11H42',
                                  fdf_run.replace('_datrun_', '_pedthr_'))
    file_text = file_text.replace('file_num=0', f'file_num={file_num}')
    if ped_in_dir is not None:
        file_text = file_text.replace('/mnt/nas_clas12/DATA/CosmicBench/2024/W05/', ped_in_dir)
    if data_in_dir is not None:
        file_text = file_text.replace('/mnt/nas_clas12/DATA/CosmicBench/2024/W05/', data_in_dir)
    if 'feu="03"' in file_text:
        file_text = file_text.replace('feu="03"', f'feu="{feu}"')
    # Write new file
    with open(temp_file_name, 'w') as file:
        file.write(file_text)
    # Make file executable
    os.system(f'chmod +x {temp_file_name}')
    return temp_file_name


def remove_files(directory, extension=None):
    """
    Remove all files in directory with given file extension
    :param directory: Directory from which to remove files
    :param extension: Only remove files with given extension. Remove all files if extension is None
    :return:
    """
    for file_name in os.listdir(directory):
        if extension is not None and not file_name.endswith(extension):
            continue
        print(f'Removing {directory}{file_name}')
        os.remove(f'{directory}{file_name}')


if __name__ == '__main__':
    main()

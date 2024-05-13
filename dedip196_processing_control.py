#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 09 17:11 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/dedip196_processing_control

@author: Dylan Neff, dn277127
"""

import os
import shutil
from datetime import datetime

from Server import Server


def main():
    port = 1100
    with Server(port=port) as server:
        server.receive()
        server.send('Processing control connected')
        run_info = server.receive_json()

        res = server.receive()
        while 'Finished' not in res:
            if 'Decode FDFs' in res:
                sub_run = res.strip().split()[-1]
                sub_run_dir = f"{run_info['run_dir']}{sub_run}/"
                fdf_dir = f"{sub_run_dir}{run_info['raw_daq_inner_dir']}"
                out_dir = f"{sub_run_dir}{run_info['decoded_root_inner_dir']}"
                decode_fdfs(fdf_dir, run_info['decode_path'], run_info['convert_path'], out_dir,
                            out_type=run_info['out_type'])
                server.send('FDFs Decoded')
            elif 'Run M3 Tracking' in res:
                pass
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
        out_name = file.replace('.fdf', 'decoded')
        command = f"{decode_path} {fdf_dir}{file.replace('.fdf', '')} {out_name}"
        print(command)
        os.system(command)
        if out_type in ['array', 'both']:
            if convert_path is None:
                print('Error! Need convert path for vec->array! Skipping')
            else:
                command = f"{convert_path} {out_name} {out_name}_array"
                print(command)
                os.system(command)
            if out_type == 'array':  # Remove vector formatted root file
                os.remove(f'{out_name}.root')

    os.chdir(og_dir)


def m3_tracking(fdf_dir, tracking_sh_ref_path, out_dir=None, m3_fdf_num=1):
    """

    :param fdf_dir:
    :param tracking_sh_ref_path:
    :param out_dir:
    :param m3_fdf_num:
    :return:
    """
    for file in os.listdir(fdf_dir):
        if not file.endswith('.fdf'):
            continue
        feu_num = get_feu_num_from_fdf_file_name(file)
        if feu_num != m3_fdf_num:
            continue
        run_name = get_run_name_from_fdf_file_name(file)
        file_num = get_file_num_from_fdf_file_name(file)
        out_dir = fdf_dir if out_dir is None else out_dir
        get_rays_from_fdf(run_name, tracking_sh_ref_path, [file_num], out_dir, fdf_dir)


def get_rays_from_fdf(fdf_run, tracking_sh_file, file_nums, output_root_dir, run_dir, verbose=False):
    """
    Get rays from fdf files and write to root file.
    :param fdf_run:
    :param tracking_sh_file:
    :param file_nums:
    :param output_root_dir:
    :param run_dir:
    :param verbose:
    :return:
    """
    og_dir = os.getcwd()
    os.chdir(run_dir)
    for i in file_nums:
        print(f'Processing file {i}')
        temp_sh_file = make_temp_sh_file(fdf_run, tracking_sh_file, i, 'tracking')
        cmd = f'{temp_sh_file}'
        if not verbose:
            cmd += ' > /dev/null'
        os.system(cmd)
        shutil.move(f'output_{i:03d}.root', f'{output_root_dir}{fdf_run}_{i:03d}_rays.root')
    os.chdir(og_dir)


def make_temp_sh_file(fdf_run, ref_sh_file, file_num, sh_file_type='tracking', feu='01'):
    """
    Make the tracking shell script file to run the tracking program from reference file.
    :param fdf_run:
    :param ref_sh_file:
    :param file_num:
    :param sh_file_type:
    :param feu:
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
    if 'feu="03"' in file_text:
        file_text = file_text.replace('feu="03"', f'feu="{feu}"')
    # Write new file
    with open(temp_file_name, 'w') as file:
        file.write(file_text)
    # Make file executable
    os.system(f'chmod +x {temp_file_name}')
    return temp_file_name


def get_date_from_fdf_file_name(file_name):
    """
    Get date from file name with format ...xxx_xxx_240212_11H42_000_01.xxx
    :param file_name:
    :return:
    """
    date_str = file_name.split('_')[-4] + ' ' + file_name.split('_')[-3]
    date = datetime.strptime(date_str, '%y%m%d %HH%M')
    return date


def get_feu_num_from_fdf_file_name(file_name):
    """
    Get fdf style feu number from file name with format ...xxx_xxx_240212_11H42_000_01.xxx
    :param file_name:
    :return:
    """
    fdf_num = int(file_name.split('_')[-1].split('.')[0])
    return fdf_num


def get_file_num_from_fdf_file_name(file_name):
    """
    Get fdf style file number from file name with format ...xxx_xxx_240212_11H42_000_01.xxx
    :param file_name:
    :return:
    """
    file_num = int(file_name.split('_')[-2])
    return file_num


def get_run_name_from_fdf_file_name(file_name):
    # Should work for fdfs, maybe other file types
    run_name = file_name[:file_name.rfind('_', 0, file_name.rfind('_'))].split('/')[-1]
    return run_name


if __name__ == '__main__':
    main()

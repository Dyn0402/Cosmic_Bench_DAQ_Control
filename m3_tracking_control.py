#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 09 17:11 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/dedip196_processing_control

@author: Dylan Neff, dn277127
"""

import sys
import subprocess
import shutil

from Server import Server
from common_functions import *


def main():
    port = 1200
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f'Invalid port number {sys.argv[1]}. Using default port {port}')
    options = ['Run M3 Tracking']
    while True:
        try:
            with Server(port=port) as server:
                server.receive()
                server.send('M3 Tracking connected')
                run_info = server.receive_json()
                server.send('Received run info')

                res = server.receive()
                while 'Finished' not in res:
                    run_options = [option for option in options if option in res]
                    if len(run_options) == 0:
                        server.send('Unknown Command')
                    else:
                        server.send(f"{' and '.join(run_options)} Started...")
                        sub_run = res.strip().split()[-1]
                        file_num = None
                        if 'file_num=' in res.strip().split()[-2]:
                            file_num = int(res.strip().split()[-2].replace('file_num=', ''))
                        sub_run_dir = f"{run_info['run_dir']}/{sub_run}/"
                        fdf_dir = f"{sub_run_dir}{run_info['raw_daq_inner_dir']}/"
                        if 'Run M3 Tracking' in run_options:
                            out_dir = f"{sub_run_dir}{run_info['m3_tracking_inner_dir']}/"
                            create_dir_if_not_exist(out_dir)
                            print(f'\n\nRunning M3 Tracking on FDFs in {fdf_dir} to {out_dir} file_num={file_num}')
                            m3_tracking(fdf_dir, run_info['tracking_sh_path'], run_info['tracking_run_dir'], out_dir,
                                        m3_feu_num=run_info['m3_feu_num'], file_num=file_num)
                            server.send(f'M3 Tracking Complete for {sub_run} file_num={file_num}')
                    res = server.receive()
        except Exception as e:
            print(f'Error: {e}\nRestarting processing control server...')
    print('donzo')


def m3_tracking(fdf_dir, tracking_sh_ref_path, tracking_run_dir, out_dir=None, m3_feu_num=1, file_num=None):
    """

    :param fdf_dir:
    :param tracking_sh_ref_path:
    :param tracking_run_dir:
    :param out_dir:
    :param m3_feu_num:
    :param file_num:
    :return:
    """
    for file in os.listdir(fdf_dir):
        if not file.endswith('.fdf') or '_datrun_' not in file:
            continue
        feu_num = get_feu_num_from_fdf_file_name(file)
        if feu_num != m3_feu_num:
            continue
        run_name = get_run_name_from_fdf_file_name(file)
        file_num_i = get_file_num_from_fdf_file_name(file, -2)
        if file_num is not None and file_num_i != file_num:
            continue
        out_dir = fdf_dir if out_dir is None else out_dir
        get_rays_from_fdf(run_name, tracking_sh_ref_path, [file_num_i], out_dir, tracking_run_dir, verbose=True,
                          fdf_dir=fdf_dir)


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


if __name__ == '__main__':
    main()

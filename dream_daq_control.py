#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 08 13:57 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/dream_daq_control

@author: Dylan Neff, dn277127
"""

import os
import re
import subprocess
from time import sleep
from datetime import datetime
import traceback
import shutil
import threading

from Server import Server
from common_functions import *


def main():
    port = 1101
    while True:
        try:
            clear_terminal()
            with Server(port=port) as server:
                server.receive()
                server.send('Dream DAQ control connected')
                dream_info = server.receive_json()
                original_working_directory = os.getcwd()

                create_dir_if_not_exist(dream_info['run_directory'])

                res = server.receive()
                while 'Finished' not in res:
                    if 'Start' in res:
                        subrun = server.receive_json()
                        effective_info = {**dream_info, **subrun}

                        sub_run_name = subrun['sub_run_name']
                        run_time = float(subrun['run_time'])
                        print(f'Sub-run name: {sub_run_name}, Run time: {run_time} minutes')

                        effective_cfg_template_path = effective_info['daq_config_template_path']
                        effective_out_directory = effective_info['data_out_dir']
                        effective_raw_daq_inner_dir = effective_info['raw_daq_inner_dir']
                        effective_run_directory = effective_info['run_directory']
                        effective_copy_on_fly = effective_info['copy_on_fly']
                        effective_zero_suppress = effective_info.get('zero_suppress', False)
                        effective_samples_per_waveform = effective_info.get('n_samples_per_waveform', None)
                        effective_pedestals_dir = effective_info.get('pedestals_dir', None)
                        effective_pedestals = effective_info.get('pedestals', None)
                        effective_pedestal_subtraction = effective_info.get('pedestal_subtraction', None)
                        effective_common_noise_subtraction = effective_info.get('common_noise_subtraction', None)
                        effective_zs_type = effective_info.get('zs_type', None)
                        effective_zs_check_sample = effective_info.get('zs_check_sample', None)
                        effective_latency = effective_info.get('latency', None)

                        sub_run_out_raw_inner_dir = f'{effective_out_directory}/{sub_run_name}/{effective_raw_daq_inner_dir}/'
                        create_dir_if_not_exist(sub_run_out_raw_inner_dir)

                        if effective_run_directory is not None:
                            sub_run_dir = f'{effective_run_directory}{sub_run_name}/'
                            create_dir_if_not_exist(sub_run_dir)
                            os.chdir(sub_run_dir)
                        else:
                            sub_run_dir = os.getcwd()

                        cfg_run_path = make_config_from_template(
                            sub_run_dir, effective_cfg_template_path, run_time,
                            effective_zero_suppress, effective_samples_per_waveform,
                            effective_pedestal_subtraction, effective_common_noise_subtraction,
                            effective_zs_type, effective_zs_check_sample, effective_latency)
                        shutil.copy(cfg_run_path, sub_run_out_raw_inner_dir)

                        if effective_pedestals_dir is not None:
                            print(f'Getting pedestal files from {effective_pedestals_dir}...')
                            get_pedestals(effective_pedestals_dir, effective_pedestals, sub_run_dir, sub_run_out_raw_inner_dir)

                        run_command = ['RunCtrl', '-c', cfg_run_path, '-f', sub_run_name, '-b']

                        if effective_copy_on_fly:
                            daq_finished = threading.Event()
                            copy_files_on_the_fly_thread = threading.Thread(
                                target=copy_files_on_the_fly,
                                args=(sub_run_dir, sub_run_out_raw_inner_dir, daq_finished),
                                daemon=True,
                            )
                            copy_files_on_the_fly_thread.start()

                        server.send('Dream DAQ starting')
                        print(f'Starting Dream DAQ with command: {run_command}')
                        subprocess.call(run_command)

                        if effective_copy_on_fly:
                            print('Signaling on-the-fly copier to finish soon (but not waiting).')
                            daq_finished.set()

                        for log_file in os.listdir(sub_run_dir):
                            if log_file.endswith('.log'):
                                shutil.copy(os.path.join(sub_run_dir, log_file), sub_run_out_raw_inner_dir)
                                print(f'Copied log file {log_file} to {sub_run_out_raw_inner_dir}')

                        os.chdir(original_working_directory)
                        server.send('Dream DAQ stopped')
                    else:
                        server.send('Unknown Command')
                    res = server.receive()
        except Exception as e:
            traceback.print_exc()
            print(f'Error: {e}')
            sleep(30)
    print('donzo')


def copy_files_on_the_fly(sub_run_dir, sub_out_dir, daq_finished_event, check_interval=5, extra_minutes_after_finish=3):
    """
    Copies new .fdf files during the run, and continues for extra_minutes_after_finish
    after DAQ finishes, then exits cleanly without blocking the main thread.
    """
    create_dir_if_not_exist(sub_out_dir)
    sleep(60)  # Give DAQ time to start writing before first scan

    file_num = 0

    # Phase 1: DAQ running
    while not daq_finished_event.is_set():
        if not file_num_still_running(sub_run_dir, file_num, silent=True):
            for file_name in os.listdir(sub_run_dir):
                if (
                    file_name.endswith('.fdf') and
                    get_file_num_from_fdf_file_name(file_name, -2) == file_num
                ):
                    shutil.copy(
                        os.path.join(sub_run_dir, file_name),
                        os.path.join(sub_out_dir, file_name),
                    )
            file_num += 1
        sleep(check_interval)

    # Phase 2: DAQ has ended — keep copying stragglers
    print("DAQ finished — continuing file copy for cleanup window.")
    end_time = time.time() + extra_minutes_after_finish * 60
    already_seen = set()

    while time.time() < end_time:
        for file_name in os.listdir(sub_run_dir):
            if file_name.endswith('.fdf') and file_name not in already_seen:
                src = os.path.join(sub_run_dir, file_name)
                dst = os.path.join(sub_out_dir, file_name)
                try:
                    shutil.copy(src, dst)
                    already_seen.add(file_name)
                except Exception:
                    pass
        sleep(check_interval)

    print("On-the-fly copy thread exiting.")


def file_num_still_running(fdf_dir, file_num, wait_time=30, silent=False):
    """
    Check if dream DAQ is still writing to a file by seeing if its size increases over wait_time.
    Returns True if size increased (still running), False if not.
    """
    file_paths = []
    for file in os.listdir(fdf_dir):
        if not file.endswith('.fdf') or '_datrun_' not in file:
            continue
        if get_file_num_from_fdf_file_name(file) == file_num:
            file_paths.append(f'{fdf_dir}{file}')

    if len(file_paths) == 0:
        if not silent:
            print(f'No fdfs with file num {file_num} found in {fdf_dir}')
        return False

    old_sizes = [os.path.getsize(p) for p in file_paths]
    sleep(wait_time)
    new_sizes = [os.path.getsize(p) for p in file_paths]

    return any(new > old for new, old in zip(new_sizes, old_sizes))


def clear_terminal():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        pass


def _to_bit(val):
    """Convert bool/int/str (0, 1, True, False, 'true', 'false') to integer 0 or 1."""
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int):
        return int(bool(val))
    s = str(val).strip().lower()
    if s in ('1', 'true', 'yes'):
        return 1
    if s in ('0', 'false', 'no'):
        return 0
    raise ValueError(f"Cannot convert {val!r} to 0/1")


def _to_zs_typ(val):
    """Convert ZsTyp value: 0/'tracker' → 0, 1/'tpc' → 1."""
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int):
        return val
    s = str(val).strip().lower()
    if s in ('tpc', '1'):
        return 1
    if s in ('tracker', '0'):
        return 0
    raise ValueError(f"Cannot convert {val!r} to ZsTyp (0=tracker, 1=tpc)")


def make_config_from_template(run_dir, cfg_template_file_path, cfg_file_run_time, zero_suppress_mode=False,
                              samples_per_waveform=None, pedestal_subtraction=None,
                              common_noise_subtraction=None, zs_type=None, zs_check_sample=None,
                              latency=None):
    print('Making config file from template...')
    dest = run_dir
    cfg_file_name = os.path.basename(cfg_template_file_path)
    cfg_file_path = f'{dest}{cfg_file_name}'
    shutil.copy(cfg_template_file_path, cfg_file_path)

    template_dir = os.path.dirname(cfg_template_file_path)
    for file in os.listdir(template_dir):
        if file.startswith('Grace_'):
            shutil.copy(f'{template_dir}/{file}', f'{dest}{file}')

    updates = {
        "Sys DaqRun Time": cfg_file_run_time * 60,  # Seconds
        "Sys DaqRun Mode": 'ZS' if zero_suppress_mode else 'Raw',
        "Feu * Feu_RunCtrl_ZS": _to_bit(zero_suppress_mode),
    }
    if samples_per_waveform is not None:
        updates["Sys NbOfSamples"] = samples_per_waveform
    if pedestal_subtraction is not None:
        updates["Feu * Feu_RunCtrl_Pd"] = _to_bit(pedestal_subtraction)
    if common_noise_subtraction is not None:
        updates["Feu * Feu_RunCtrl_CM"] = _to_bit(common_noise_subtraction)
    if zs_type is not None:
        updates["Feu * Feu_RunCtrl_ZsTyp"] = _to_zs_typ(zs_type)
    if zs_check_sample is not None:
        val = int(zs_check_sample)
        if not (0 <= val <= 4):
            raise ValueError(f"zs_check_sample must be between 0 and 4, got {val}")
        updates["Feu * Feu_RunCtrl_ZsChkSmp"] = val
    if latency is not None:
        updates["Feu * Dream * 12"] = f'0x{int(latency):04X}'
    update_config_value(cfg_file_path, updates)

    return cfg_file_path


def update_config_value(filepath, updates, output_path=None):
    """
    Updates parameters in a free-form config file without changing spacing/comments.
    """
    output_path = output_path or filepath
    with open(filepath, 'r') as f:
        lines = f.readlines()

    updates = {re.escape(k.strip()): str(v) for k, v in updates.items()}
    new_lines = []

    for line in lines:
        if re.match(r'^\s*#', line) or not line.strip():
            new_lines.append(line)
            continue

        for flag_pattern, new_value in updates.items():
            pattern = rf"^(\s*{flag_pattern}\s+)([^\s#]+)"
            if re.search(pattern, line):
                line = re.sub(pattern, lambda m: f"{m.group(1)}{new_value}", line)
                break

        new_lines.append(line)

    with open(output_path, 'w') as f:
        f.writelines(new_lines)


def get_pedestals(pedestals_dir, pedestals, run_dir, out_dir=None):
    """
    Get pedestal files from specified directory and copy to run directory with proper naming.
    """
    sub_run_name = 'pedestals'  # Standard name for cosmic bench pedestal runs
    if not os.path.isdir(pedestals_dir):
        print(f'Pedestals directory `{pedestals_dir}` does not exist.')
        return None

    if pedestals == 'latest':
        valid_dirs = []
        for item in os.listdir(pedestals_dir):
            print(f'Checking pedestal item: {item}')
            full_path = os.path.join(pedestals_dir, item)
            if not os.path.isdir(full_path) or not item.startswith('pedestals_'):
                continue

            date_part = item[len('pedestals_'):]
            parsed_dt = None
            for fmt in ('%m-%d-%y_%H-%M-%S', '%m-%d-%Y_%H-%M-%S'):
                try:
                    parsed_dt = datetime.strptime(date_part, fmt)
                    break
                except ValueError:
                    continue

            if parsed_dt is None:
                continue

            valid_dirs.append((parsed_dt, item))

        if not valid_dirs:
            print('No pedestal directories found matching the expected datetime format.')
            return None

        valid_dirs.sort(key=lambda x: x[0])
        latest_pedestal_dir = valid_dirs[-1][1]
        pedestals_prg_dir = os.path.join(pedestals_dir, latest_pedestal_dir, sub_run_name) + os.sep
    else:
        pedestals_prg_dir = os.path.join(pedestals_dir, pedestals, sub_run_name) + os.sep

    for file in os.listdir(pedestals_prg_dir):
        print(f'Checking pedestal file: {file}')
        if file.endswith('.prg'):
            feu_num_search = re.search(r'_(\d{2})_', file)
            if feu_num_search:
                feu_num = feu_num_search.group(1)
                if '_ped.prg' in file:
                    dest_file_name = f'dream_pedestals_{feu_num}_ped.prg'
                elif '_thr.prg' in file:
                    dest_file_name = f'dream_thresholds_{feu_num}_thr.prg'
                else:
                    print(f'Unknown pedestal file type for {file}, skipping.')
                    continue
                print(f'Copying pedestal file {file} for FEU {feu_num}...')
                shutil.copy(f'{pedestals_prg_dir}{file}', f'{run_dir}{dest_file_name}')
                if out_dir:
                    shutil.copy(f'{pedestals_prg_dir}{file}', f'{out_dir}{file}')
                ped_run = pedestals_prg_dir.strip('/').split('/')[-2]
                with open(f'{run_dir}pedestal_run.txt', 'w') as f:
                    f.write(ped_run)
                if out_dir:
                    with open(f'{out_dir}pedestal_run.txt', 'w') as f:
                        f.write(ped_run)
                print(f'Copied pedestal file {file} to {dest_file_name}')
            else:
                print(f'Could not find FEU number in pedestal file name {file}, skipping.')
        elif file.endswith('.fdf'):
            feu_num_search = re.search(r'_(\d{2})_', file)
            if feu_num_search:
                print(f'Copying pedestal fdf file {file}...')
                shutil.copy(f'{pedestals_prg_dir}{file}', f'{run_dir}{file}')
                if out_dir:
                    shutil.copy(f'{pedestals_prg_dir}{file}', f'{out_dir}{file}')
            else:
                print(f'Could not find FEU number in pedestal fdf file name {file}, skipping.')


if __name__ == '__main__':
    main()

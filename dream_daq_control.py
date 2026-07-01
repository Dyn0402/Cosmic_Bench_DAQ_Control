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
import logging
import subprocess
from time import sleep
from datetime import datetime
import traceback
import shutil
import threading

from Server import Server
from common_functions import *


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )
    port = 1101
    while True:
        run_log_handler = None
        subrun_log_handler = None
        try:
            clear_terminal()
            with Server(port=port) as server:
                server.receive()
                server.send('Dream DAQ control connected')
                dream_info = server.receive_json()
                original_working_directory = os.getcwd()

                create_dir_if_not_exist(dream_info['data_out_dir'])
                run_log_handler = setup_logging(
                    os.path.join(dream_info['data_out_dir'], 'dream_daq.log'))
                logging.info('Run started')

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
                        effective_do_ped_thr_run = effective_info.get('do_pedestal_threshold_run', None)
                        effective_do_trg_thr_run = effective_info.get('do_trigger_threshold_run', None)
                        effective_do_data_run = effective_info.get('do_data_run', None)
                        effective_included_feus = effective_info.get('included_feus', None)
                        effective_feu_connectors = effective_info.get('feu_connectors', None)
                        effective_trigger_feu = effective_info.get('trigger_feu', None)

                        sub_run_out_raw_inner_dir = f'{effective_out_directory}/{sub_run_name}/{effective_raw_daq_inner_dir}/'
                        create_dir_if_not_exist(sub_run_out_raw_inner_dir)
                        subrun_log_handler = setup_logging(
                            os.path.join(sub_run_out_raw_inner_dir, 'dream_daq.log'))
                        logging.info(f'Subrun started: {sub_run_name}  run_time={run_time}min')

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
                            effective_zs_type, effective_zs_check_sample, effective_latency,
                            effective_do_ped_thr_run, effective_do_trg_thr_run, effective_do_data_run,
                            effective_included_feus, effective_feu_connectors, effective_trigger_feu)
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
                        logging.info(f'Subrun finished: {sub_run_name}')
                        teardown_logging(subrun_log_handler)
                        subrun_log_handler = None
                    else:
                        server.send('Unknown Command')
                    res = server.receive()
                logging.info('Run finished normally')
                if run_log_handler is not None:
                    teardown_logging(run_log_handler)
                    run_log_handler = None
        except Exception as e:
            logging.exception(f'Unhandled error: {e}')
            if subrun_log_handler is not None:
                teardown_logging(subrun_log_handler)
                subrun_log_handler = None
            if run_log_handler is not None:
                teardown_logging(run_log_handler)
                run_log_handler = None
            try:
                os.chdir(original_working_directory)
            except Exception:
                pass
            try:
                server.send(f'Dream DAQ error: {e}')
            except Exception:
                pass
            sleep(30)
    print('donzo')


def copy_files_on_the_fly(sub_run_dir, sub_out_dir, daq_finished_event, check_interval=5, settle_time=15):
    """
    Copy raw .fdf files from sub_run_dir into sub_out_dir as they complete.

    A file is copied once it is 'stable' (its size stopped growing between two
    polls), which naturally skips the file RunCtrl is still writing. Files are
    tracked by name so each is copied exactly once, regardless of file number.
    After the DAQ finishes every remaining file is complete, so a final sweep
    copies whatever is left, then the thread exits.

    This replaces the previous version, whose monotonic file-number counter
    raced ahead of the data (file_num_still_running() returns False for numbers
    that don't exist yet), so it incremented past the real files and copied
    nothing but the very first (pedestal) set.
    """
    create_dir_if_not_exist(sub_out_dir)

    copied = set()
    last_sizes = {}

    def sweep(require_stable):
        for file_name in os.listdir(sub_run_dir):
            if not file_name.endswith('.fdf') or file_name in copied:
                continue
            src = os.path.join(sub_run_dir, file_name)
            try:
                size = os.path.getsize(src)
            except OSError:
                continue
            if size == 0:
                continue
            if require_stable and last_sizes.get(file_name) != size:
                # First sighting or still growing -> record size, wait for it to settle.
                last_sizes[file_name] = size
                continue
            try:
                _atomic_copy(src, os.path.join(sub_out_dir, file_name))
                copied.add(file_name)
            except Exception as e:
                print(f'On-the-fly copy failed for {file_name}: {e}')

    # Phase 1: DAQ running -- copy only files whose size has settled.
    while not daq_finished_event.is_set():
        sweep(require_stable=True)
        sleep(check_interval)

    # Phase 2: DAQ finished -- everything is complete. Sweep for a short settle
    # window to catch files flushed at the very end, then a final unconditional
    # sweep guarantees nothing is left behind.
    print('DAQ finished -- final copy sweep for remaining files.')
    deadline = time.time() + settle_time
    while time.time() < deadline:
        sweep(require_stable=False)
        sleep(check_interval)
    sweep(require_stable=False)
    print(f'On-the-fly copy thread exiting ({len(copied)} files copied).')


def _atomic_copy(src, dst):
    """Copy src to dst so the destination only ever appears once fully written.

    The data is copied to a hidden '.part' temp file in the destination directory,
    then atomically renamed onto dst with os.replace (same filesystem -> atomic).
    This prevents the processor_watcher from seeing partially-copied FDFs: it globs
    '*.fdf', so the '.part' temp name is ignored until the rename completes."""
    tmp = os.path.join(os.path.dirname(dst), f'.{os.path.basename(dst)}.part')
    try:
        shutil.copy(src, tmp)
        os.replace(tmp, dst)
    except Exception:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


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
                              latency=None, do_pedestal_threshold_run=None,
                              do_trigger_threshold_run=None, do_data_run=None, included_feus=None,
                              feu_connectors=None, trigger_feu=None):
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
    if do_pedestal_threshold_run is not None:
        updates["Sys Action PedThrRun"] = _to_bit(do_pedestal_threshold_run)
    if do_trigger_threshold_run is not None:
        updates["Sys Action TrgThrRun"] = _to_bit(do_trigger_threshold_run)
    if do_data_run is not None:
        updates["Sys Action DataRun"] = _to_bit(do_data_run)
    update_config_value(cfg_file_path, updates)

    if included_feus is not None:
        set_active_feus(cfg_file_path, included_feus, feu_connectors=feu_connectors, trigger_feu=trigger_feu)

    return cfg_file_path


# Connectors in dream_feus are 1-based (1..8) and map to FEU Dream indices 0..7.
CONNECTOR_DREAM_OFFSET = 1  # connector = dream_index + CONNECTOR_DREAM_OFFSET


def set_active_feus(filepath, included_feus, feu_connectors=None, trigger_feu=None, output_path=None):
    """
    Enable only the given FEUs in a Dream .cfg, and set per-Dream roles, by editing lines in place.

    For each FEU-specific hardware line (``Feu N Feu_RunCtrl_Id ...``, ``Feu N NetChan_Ip ...``) and
    the ``Sys Topo Feu N ...`` topology line, the line is left active when its FEU number N is in
    ``included_feus`` and commented out otherwise.

    For an active ``Sys Topo`` line, the per-Dream roles are also rewritten when ``feu_connectors`` is
    given (a ``{feu_number: [used connectors]}`` map): each Dream becomes ``Dat`` when its connector is
    used by an included detector, else ``Msk``. The ``trigger_feu`` (e.g. the M3 FEU) is left untouched
    so it keeps its template roles (all ``Trg``).

    Wildcard ``Feu * ...`` lines and per-FEU register overrides (e.g. ``Feu 1 Dream * ...``) are left
    untouched, so the template remains the source of truth for hardware Id/IP and Dream registers.
    """
    output_path = output_path or filepath
    included = {int(f) for f in included_feus}
    feu_connectors = {int(k): set(v) for k, v in (feu_connectors or {}).items()}
    trigger_feu = int(trigger_feu) if trigger_feu is not None else None

    topo_pat = re.compile(
        r'^(?P<indent>\s*)#*\s*(?P<head>Sys\s+Topo\s+Feu\s+(?P<num>\d+)\s+Dream\s+)(?P<dreams>.*)$')
    hw_pats = [
        re.compile(r'^(?P<indent>\s*)#*\s*(?P<body>Feu\s+(?P<num>\d+)\s+Feu_RunCtrl_Id\b.*)$'),
        re.compile(r'^(?P<indent>\s*)#*\s*(?P<body>Feu\s+(?P<num>\d+)\s+NetChan_Ip\b.*)$'),
    ]

    def set_dream_roles(dreams_str, connectors):
        # Replace each "<dream_index> <whitespace> <role>" triplet's role, preserving spacing.
        def repl(m):
            dream_idx = int(m.group(1))
            role = 'Dat' if (dream_idx + CONNECTOR_DREAM_OFFSET) in connectors else 'Msk'
            return f'{m.group(1)}{m.group(2)}{role}'
        return re.sub(r'(\d+)(\s+)(?:Trg|Dat|Msk)', repl, dreams_str)

    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    activated, deactivated = set(), set()
    for line in lines:
        raw = line.rstrip('\n')

        m = topo_pat.match(raw)
        if m:
            feu_num = int(m.group('num'))
            indent, head, dreams = m.group('indent'), m.group('head'), m.group('dreams')
            if feu_num in included:
                # Rewrite roles for active data FEUs; leave the trigger FEU's roles as-is.
                if feu_num != trigger_feu and feu_num in feu_connectors:
                    dreams = set_dream_roles(dreams, feu_connectors[feu_num])
                new_lines.append(f'{indent}{head}{dreams}\n')
                activated.add(feu_num)
            else:
                new_lines.append(f'{indent}#{head}{dreams}\n')
                deactivated.add(feu_num)
            continue

        for pat in hw_pats:
            hm = pat.match(raw)
            if not hm:
                continue
            feu_num = int(hm.group('num'))
            indent, body = hm.group('indent'), hm.group('body')
            new_lines.append(f'{indent}{body}\n' if feu_num in included else f'{indent}#{body}\n')
            break
        else:
            new_lines.append(line)

    with open(output_path, 'w') as f:
        f.writelines(new_lines)

    print(f'Set active FEUs from detectors: enabled {sorted(activated)}, disabled {sorted(deactivated)}')
    missing = included - activated
    if missing:
        print(f'WARNING: requested FEUs {sorted(missing)} have no Sys Topo lines in the template '
              f'and could not be enabled.')


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
    Copy pedestal files from the selected pedestal run into the run directory.

    The raw pedestal FDFs are read from the nested ``<ped_run>/pedestals/raw_daq_data/``
    (falling back to the flat ``<ped_run>/pedestals/`` for older layouts), and ONLY the
    ``*_pedthr_*`` FDFs are copied -- never the ``*_datrun_*`` files, which would otherwise
    be picked up by the processor as data. Any ``*_ped.prg``/``*_thr.prg`` threshold files
    (used by the DAQ for zero suppression) are copied too, and a ``pedestal_run.txt`` pointer
    is written for processors using ``pedestal_loc='find'``.
    """
    sub_run_name = 'pedestals'  # Standard name for cosmic bench pedestal runs
    if not os.path.isdir(pedestals_dir):
        print(f'Pedestals directory `{pedestals_dir}` does not exist.')
        return None

    # --- select which pedestal run to use ---
    if pedestals == 'latest':
        valid_dirs = []
        for item in os.listdir(pedestals_dir):
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
        ped_run = valid_dirs[-1][1]
    else:
        ped_run = pedestals

    ped_base_dir = os.path.join(pedestals_dir, ped_run, sub_run_name)
    if not os.path.isdir(ped_base_dir):
        print(f'Pedestal run dir `{ped_base_dir}` does not exist.')
        return None

    # Raw FDFs live in the nested raw_daq_data/ (current layout); fall back to the flat dir.
    fdf_src = os.path.join(ped_base_dir, 'raw_daq_data')
    if not os.path.isdir(fdf_src):
        fdf_src = ped_base_dir
    print(f'Using pedestal run {ped_run} (fdf source: {fdf_src})')

    # --- copy ONLY the pedthr FDFs (never datrun) ---
    for file in os.listdir(fdf_src):
        if file.endswith('.fdf') and '_pedthr_' in file and re.search(r'_(\d{3})_(\d{2})\.', file):
            print(f'Copying pedestal fdf file {file}...')
            shutil.copy(os.path.join(fdf_src, file), f'{run_dir}{file}')
            if out_dir:
                shutil.copy(os.path.join(fdf_src, file), f'{out_dir}{file}')

    # --- copy threshold .prg files (for zero suppression) from whichever source has them ---
    for prg_src in (ped_base_dir, fdf_src):
        prg_files = [f for f in os.listdir(prg_src) if f.endswith('.prg')]
        if not prg_files:
            continue
        for file in prg_files:
            feu_num_search = re.search(r'_(\d{2})_', file)
            if not feu_num_search:
                print(f'Could not find FEU number in pedestal file name {file}, skipping.')
                continue
            feu_num = feu_num_search.group(1)
            if '_ped.prg' in file:
                dest_file_name = f'dream_pedestals_{feu_num}_ped.prg'
            elif '_thr.prg' in file:
                dest_file_name = f'dream_thresholds_{feu_num}_thr.prg'
            else:
                print(f'Unknown pedestal file type for {file}, skipping.')
                continue
            print(f'Copying pedestal file {file} for FEU {feu_num}...')
            shutil.copy(os.path.join(prg_src, file), f'{run_dir}{dest_file_name}')
            if out_dir:
                shutil.copy(os.path.join(prg_src, file), f'{out_dir}{file}')
        break  # used the first source that had .prg files

    # --- always drop a pedestal_run.txt pointer (for processor pedestal_loc='find') ---
    with open(f'{run_dir}pedestal_run.txt', 'w') as f:
        f.write(ped_run)
    if out_dir:
        with open(f'{out_dir}pedestal_run.txt', 'w') as f:
            f.write(ped_run)
    print(f'Pedestal files for {ped_run} copied into {run_dir}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on April 29 8:58 PM 2024
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/daq_control.py

@author: Dylan Neff, Dylan
"""

import sys
from time import sleep

from Client import Client
from DAQController import DAQController

from run_config import Config
from common_functions import *
from weiner_ps_monitor import get_pl512_status

RUNCONFIG_REL_PATH = "config/json_run_configs/"


def main():
    print("Starting DAQ Control")

    config = Config()
    if len(sys.argv) == 2:
        config_path = os.path.join(RUNCONFIG_REL_PATH, sys.argv[1]) if not os.path.isabs(sys.argv[1]) else sys.argv[1]
        print(f'Using run config file: {config_path}')
        if not os.path.isfile(config_path):
            print(f'File {config_path} does not exist, exiting')
            return
        if config_path.endswith('.json'):
            config.load_from_file(config_path)
        elif config_path.endswith('.py'):
            pass
    config.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    hv_ip, hv_port = config.hv_control_info['ip'], config.hv_control_info['port']
    dream_daq_ip, dream_daq_port = config.dream_daq_info['ip'], config.dream_daq_info['port']

    hv_client = Client(hv_ip, hv_port)
    dream_daq_client = Client(dream_daq_ip, dream_daq_port)

    with hv_client as hv, dream_daq_client as dream_daq:

        hv.send('Connected to daq_control')
        hv.receive()
        hv.send_json(config.hv_info)

        create_dir_if_not_exist(config.run_out_dir)
        config.write_to_file(f'{config.run_out_dir}run_config.json')

        dream_daq.send('Connected to daq_control')
        dream_daq.receive()
        dream_daq.send_json(config.dream_daq_info)

        sleep(2)  # Give servers time to set up directories
        try:
            for sub_run in config.sub_runs:
                sub_run_name = sub_run['sub_run_name']
                sub_top_out_dir = f'{config.run_out_dir}{sub_run_name}/'
                complete_marker = f'{sub_top_out_dir}.subrun_complete'
                if getattr(config, 'resume', False) and os.path.exists(complete_marker):
                    print(f'[resume] Skipping already-completed sub run {sub_run_name}')
                    continue
                create_dir_if_not_exist(sub_top_out_dir)
                sub_out_dir = f'{sub_top_out_dir}{config.raw_daq_inner_dir}/'
                create_dir_if_not_exist(sub_out_dir)

                if getattr(config, 'weiner_ps_info', None):
                    weiner_ok = check_weiner_lv_status(config.weiner_ps_info)
                    if not weiner_ok:
                        print(f'Weiner Power Supply check failed, skipping sub run {sub_run_name}')
                        continue

                print(f'Ramping HVs for {sub_run_name}')
                if config.hv_info['hv_monitoring']:
                    hv.send('Begin Monitoring')
                    hv.receive()
                    hv.send_json(sub_run)
                    hv.receive()

                hv.send('Start')
                hv.receive()
                hv.send_json(sub_run)
                res = hv.receive()
                if 'HV Set' in res:
                    print(f'[status] run={config.run_name}  subrun={sub_run_name}  run_time={sub_run.get("run_time", "?")}min')
                    print(f'Starting run for sub run {sub_run_name}')
                    run_daq_controller(sub_run, sub_out_dir, dream_daq)

                    if config.hv_info['hv_monitoring']:
                        hv.send('End Monitoring')
                        hv.receive()
                        hv.receive()

                    # Mark this sub-run complete so a future resume run skips it (see config.resume).
                    with open(complete_marker, 'w') as f:
                        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')

                    print(f'Finished with sub run {sub_run_name}, waiting 10 seconds before next run')
                    sleep(10)
        except KeyboardInterrupt:
            print('Run stopping.')
            if config.hv_info['hv_monitoring']:
                hv.send('End Monitoring')
                hv.receive()
                hv.receive()
        finally:
            pass

        print('Run complete, closing down subsystems')
        if config.power_off_hv_at_end:
            hv.send('Power Off')
            hv.receive()
            hv.receive()
        hv.send('Finished')
        dream_daq.send('Finished')
    print('donzo')


def run_daq_controller(sub_run, sub_out_dir, dream_daq_client):
    daq_controller = DAQController(subrun=sub_run, out_dir=sub_out_dir, dream_daq_client=dream_daq_client)
    daq_success = False
    while not daq_success:
        print('Starting DAQ Controller')
        daq_success = daq_controller.run()


def check_weiner_lv_status(weiner_ps_info):
    ps_status = get_pl512_status(f'http://{weiner_ps_info["ip"]}')
    if ps_status['power_supply_status'] != 'ON':
        print('Weiner Power Supply is not ON, exiting sub-run')
        return False
    for channel in weiner_ps_info['channels']:
        channel_status = ps_status['channels'].get(channel, None)
        if channel_status is None:
            print(f'Weiner Power Supply Channel {channel} not found, exiting sub-run')
            return False
        if channel_status['status'] != 'ON':
            print(f'Weiner Power Supply Channel {channel} is not ON, exiting sub-run')
            return False
        channel_info = weiner_ps_info['channels'][channel]

        v_meas = channel_status['measured_sense_voltage']
        v_expected = channel_info['expected_voltage']
        v_tol = channel_info['voltage_tolerance']
        if not (v_expected - v_tol <= float(v_meas) <= v_expected + v_tol):
            print(f'Weiner Power Supply Channel {channel} voltage out of tolerance '
                  f'({v_meas} V measured, {v_expected} +/- {v_tol} V expected), exiting sub-run')
            return False

        i_meas = channel_status['measured_current']
        i_expected = channel_info['expected_current']
        i_tol = channel_info['current_tolerance']
        if not (i_expected - i_tol <= float(i_meas) <= i_expected + i_tol):
            print(f'Weiner Power Supply Channel {channel} current out of tolerance '
                  f'({i_meas} A measured, {i_expected} +/- {i_tol} A expected), exiting sub-run')
            return False
    print('Weiner Power Supply status OK, continuing with sub-run')
    return True


if __name__ == '__main__':
    main()

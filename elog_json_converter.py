#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on November 10 17:32 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/elog_json_converter

@author: Dylan Neff, dn277127
"""

import sys
import json
from textwrap import dedent
import os
import subprocess
import tempfile


def main():
    if len(sys.argv) < 2:
        print("Usage: python elog_json_converter.py input_run_json_path")
        sys.exit(1)
    input_run_json_path = sys.argv[1]
    # input_run_json_path = '/local/home/dn277127/PycharmProjects/Cosmic_Bench_DAQ_Control/config/json_run_configs/run_config_beam.json'

    log_id = None
    if len(sys.argv) == 3:
        log_id = sys.argv[2]

    with open(input_run_json_path, 'r') as f:
        run_config = json.load(f)

    print(run_config)
    run_id = int(run_config['run_name'].split('_')[1])
    print(run_id)

    attributes_dict = {
        'Title': run_config['run_name'],
        'RunID': int(run_config['run_name'].split('_')[1]),
        'Type': 'Run',
        'Author': 'DAQ',
        'Gas': run_config['gas'],
        'HBanco': run_config['bench_geometry']['banco_moveable_y_position'],
        'BeamInfo': run_config.get('beam_type', ''),
    }

    message_str = f"""
    <div style='font-family: sans-serif; font-size: 14px;'>
      <p><b>Output Directory:</b> {run_config['run_out_dir']}</p>

      <p><b>Detectors Included:</b></p>
      <ul style='margin-top: 4px; margin-bottom: 10px;'>
    """
    for det in run_config["included_detectors"]:
        message_str += f"    <li>{det}</li>\n"

    message_str += """
      </ul>
      <p><b>Sub-runs and HV Settings:</b></p>
    </div>
    """

    hv_table_str = generate_elog_hv_table(run_config, html=True)
    message_str += hv_table_str + "\n"

    # --- Write message to a temp file ---
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as tmp_msg:
        tmp_msg.write(message_str)
        tmp_msg_path = tmp_msg.name

    with open(tmp_msg_path, 'r') as f:
        print('Elog message content:')
        print(f.read())

    # --- Build elog command ---
    elog_cmd = [
        "elog",
        "-h", "localhost",
        "-p", "8080",
        "-n", "2",
        "-l", "SPS H4 2025",
    ]

    if log_id is not None:
        elog_cmd.extend(["-e", str(log_id)])

    # Add attributes (-a)
    for key, value in attributes_dict.items():
        elog_cmd.extend(["-a", f"{key}={value}"])

    # Add message file (-m)
    elog_cmd.extend(["-m", tmp_msg_path])

    # --- Execute elog command ---
    try:
        print("Submitting elog entry...")
        result = subprocess.run(elog_cmd, check=True, capture_output=True, text=True)
        print("Elog entry submitted successfully.")
        print("Elog output:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error submitting elog entry!")
        print("Return code:", e.returncode)
        print("Stdout:", e.stdout)
        print("Stderr:", e.stderr)
    finally:
        os.remove(tmp_msg_path)


    print('donzo')


def generate_elog_hv_table(run_config, html=False):
    detectors = {d["name"]: d for d in run_config["detectors"]}
    included = set(run_config["included_detectors"])
    sub_runs = run_config.get("sub_runs", [])

    out = []

    for sub in sub_runs:
        sub_name = sub["sub_run_name"]
        hvs = sub["hvs"]

        if html:
            out.append(f"<h3 style='margin-bottom: 6px; font-family: sans-serif;'>Sub-run: {sub_name}</h3>")
            out.append("""
            <table style="
                border-collapse: collapse;
                margin-bottom: 16px;
                text-align: center;
                font-family: sans-serif;
                font-size: 13px;
                min-width: 300px;
            ">
                <colgroup>
                    <col style="width: auto;">
                    <col style="width: auto;">
                    <col style="width: auto;">
                </colgroup>
                <thead>
                    <tr style='background-color: #f2f2f2;'>
                        <th style='border: 1px solid #ddd; padding: 4px 8px;'>Detector</th>
                        <th style='border: 1px solid #ddd; padding: 4px 8px;'>HV Channel</th>
                        <th style='border: 1px solid #ddd; padding: 4px 8px;'>Voltage (V)</th>
                    </tr>
                </thead>
                <tbody>
            """)
        else:
            out.append(f"### Sub-run: {sub_name}")
            out.append("| Detector | HV Channel | Voltage (V) |")
            out.append("|-----------|-------------|--------------|")

        row_num = 0
        for det_name in included:
            det = detectors.get(det_name)
            if not det or "hv_channels" not in det:
                continue

            hv_channels = det["hv_channels"]
            if isinstance(hv_channels, str):  # skip shorthand mappings
                continue

            for hv_name, (card, channel) in hv_channels.items():
                voltage = hvs.get(str(card), {}).get(str(channel), "—")

                if html:
                    row_color = "#ffffff" if row_num % 2 == 0 else "#fafafa"
                    out.append(
                        f"<tr style='background-color: {row_color};'>"
                        f"<td style='border: 1px solid #ddd; padding: 4px 8px;'>{det_name}</td>"
                        f"<td style='border: 1px solid #ddd; padding: 4px 8px;'>{hv_name}</td>"
                        f"<td style='border: 1px solid #ddd; padding: 4px 8px;'>{voltage}</td>"
                        f"</tr>"
                    )
                    row_num += 1
                else:
                    out.append(f"| {det_name} | {hv_name} | {voltage} |")

        if html:
            out.append("</tbody></table>")
        else:
            out.append("")

    return "\n".join(out)




if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on October 17 17:56 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/weiner_ps_monitor

@author: Dylan Neff, dn277127
"""

import requests
from bs4 import BeautifulSoup


def get_pl512_status(url="http://192.168.10.222"):
    try:
        r = requests.get(url, timeout=3)
        r.raise_for_status()
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}

    soup = BeautifulSoup(r.text, "html.parser")

    # --- Global status ---
    global_status = None
    global_table = soup.find("caption", string="Global Status")
    if global_table:
        parent = global_table.find_parent("table")
        if parent:
            cells = parent.find_all("td")
            if len(cells) >= 2:
                global_status = cells[1].get_text(strip=True)

    # --- Channel status ---
    channels = {}
    channels_table = soup.find("caption", string="Output Channels")
    if channels_table:
        parent = channels_table.find_parent("table")
        rows = parent.find_all("tr")[1:]  # skip header row
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cells) == 7:
                channel_info = {
                    "channel": cells[0],
                    "sense_voltage": cells[1],
                    "current_limit": cells[2],
                    "measured_sense_voltage": cells[3],
                    "measured_current": cells[4],
                    "measured_terminal_voltage": cells[5],
                    "status": cells[6],
                }
                channels.update({cells[0]: channel_info})

    return {
        "status": "ok",
        "power_supply_status": global_status,
        "channels": channels,
    }


if __name__ == "__main__":
    status = get_pl512_status()
    if status["status"] == "ok":
        print("Power Supply Status:", status["power_supply_status"])
        for channel_name, channel in status["channels"].items():
            print(f"Channel {channel['channel']}:")
            print(f"  Sense Voltage: {channel['sense_voltage']}")
            print(f"  Current Limit: {channel['current_limit']}")
            print(f"  Measured Sense Voltage: {channel['measured_sense_voltage']}")
            print(f"  Measured Current: {channel['measured_current']}")
            print(f"  Measured Terminal Voltage: {channel['measured_terminal_voltage']}")
            print(f"  Status: {channel['status']}")
    else:
        print("Error retrieving status:", status["message"])

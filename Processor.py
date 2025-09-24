#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 14 16:26 2025
Created in PyCharm
Created as Cosmic_Bench_DAQ_Control/Processor

@author: Dylan Neff, dn277127
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on September 15 2025
Processor system with separate decoding and tracking managers
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from Client import Client
from common_functions import (get_feu_num_from_fdf_file_name, get_run_name_from_fdf_file_name,
                              get_file_num_from_fdf_file_name)


class DecoderProcessorManager:
    def __init__(self, config: Dict[str, Any], output_dir: Path):
        self.process_prefix = "dedip196_processor_info"
        self.client = Client(config[self.process_prefix]["ip"], config[self.process_prefix]["port"])
        self._config = config
        self.output_dir = output_dir
        self.filtering = config.get("filtering_by_m3", False)
        self.save_fds = config.get("save_fds", False)

        # inner dirs
        self.raw_dirname = config.get("raw_daq_inner_dir", "raw_daq_data")
        self.decoded_dirname = config.get("decoded_root_inner_dir", "decoded_root")
        self.filtered_dirname = config.get("filtered_root_inner_dir", "filtered_root")

    def __enter__(self):
        self.client.__enter__()
        self._setup()
        return self

    def __exit__(self, *args):
        self.client.send('Finished')
        return self.client.__exit__(*args)

    def _setup(self):
        self.client.send("Connected to daq_control")
        self.client.receive()
        self.client.send_json(self._config[self.process_prefix])
        self.client.receive()
        self.client.send_json({"included_detectors": self._config["included_detectors"]})
        self.client.receive()
        self.client.send_json({"detectors": self._config["detectors"]})
        self.client.receive()

    def process_all(self):
        for sub_run in sorted(self.output_dir.iterdir()):
            if 'overnight' in sub_run.name:
                print(f'Skipping overnight run {sub_run.name}')
                continue
            if not sub_run.is_dir():
                continue

            raw_dir = sub_run / self.raw_dirname
            decoded_dir = sub_run / self.decoded_dirname
            filtered_dir = sub_run / self.filtered_dirname

            for raw_file in sorted(raw_dir.glob("*.fdf")):
                base = raw_file.stem
                feu_num = get_feu_num_from_fdf_file_name(raw_file.name)

                if feu_num == self._config["m3_feu_num"]:  # Skip M3 files
                    continue

                already_decoded = any(f.stem.startswith(base) for f in decoded_dir.glob("*"))
                already_filtered = any(f.stem.startswith(base) for f in filtered_dir.glob("*"))

                if already_decoded or already_filtered:
                    print(f'Skipping already processed file {raw_file.name}')
                    continue

                self._process_file(raw_file, sub_run.name)

    def _process_file(self, raw_file: Path, sub_run_name: str):
        # Decode
        self.client.send(f"Decode FDFs {raw_file.name} {sub_run_name}")
        self.client.receive()

        # Filtering or copy
        if self.filtering:
            self.client.send(f"Filter By M3 {raw_file.name} {sub_run_name}")
            self.client.receive()
            self.client.receive()
        else:
            self.client.send(f"Copy To Filtered {raw_file.name} {sub_run_name}")
            self.client.receive()
            self.client.receive()

        # Cleanup
        if not self.save_fds:
            self.client.send(f"Clean Up Unfiltered {raw_file.name} {sub_run_name}")
            self.client.receive()
            self.client.receive()


class TrackerProcessorManager:
    def __init__(self, config: Dict[str, Any], output_dir: Path):
        self.self_config_prefix = "sedip28_processor_info"
        self.client = Client(config["sedip28_processor_info"]["ip"], config["sedip28_processor_info"]["port"])
        self._config = config
        self.output_dir = output_dir
        self.tracking_dirname = config.get("m3_tracking_inner_dir", "m3_tracking_root")

    def __enter__(self):
        self.client.__enter__()
        self._setup()
        return self

    def __exit__(self, *args):
        self.client.send('Finished')
        return self.client.__exit__(*args)

    def _setup(self):
        self.client.send("Connected to daq_control")
        self.client.receive()
        self.client.send_json(self._config["sedip28_processor_info"])
        self.client.receive()

    def process_all(self):
        for sub_run in sorted(self.output_dir.iterdir()):
            if not sub_run.is_dir():
                continue

            tracking_dir = sub_run / self.tracking_dirname
            for fdf_file in sorted(tracking_dir.glob("*.fdf")):
                base = fdf_file.stem
                already_tracked = any(f.stem.startswith(base) for f in tracking_dir.glob("*"))
                if already_tracked:
                    print(f'Skipping already tracked file {fdf_file.name}')
                    continue

                self._process_file(fdf_file, sub_run.name)

    def _process_file(self, fdf_file: Path, sub_run_name: str):
        self.client.send(f"Run M3 Tracking {fdf_file.name} {sub_run_name}")
        self.client.receive()
        self.client.receive()


class Processor:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.output_dir = Path(self.config["run_out_dir"])

        self.decoder: Optional[DecoderProcessorManager] = None
        self.tracker: Optional[TrackerProcessorManager] = None

    def _init_processors(self):
        if "sedip28_processor_info" in self.config:  # Need to also clean up now
            # self.tracker = TrackerProcessorManager(self.config["sedip28_processor_info"], self.output_dir)
            self.tracker = TrackerProcessorManager(self.config, self.output_dir)

        if "dedip196_processor_info" in self.config:
            # self.decoder = DecoderProcessorManager(self.config["dedip196_processor_info"], self.output_dir)
            self.decoder = DecoderProcessorManager(self.config, self.output_dir)

    def _load_config(self, path: str) -> Dict[str, Any]:
        with open(path, "r") as f:
            return json.load(f)

    def process_all(self):
        self._init_processors()
        if self.decoder:
            with self.decoder as dec:
                dec.process_all()

        if self.tracker:
            with self.tracker as trk:
                trk.process_all()

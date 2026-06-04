# Cosmic_Bench_DAQ_Control

Control software for the high-voltage (HV) crate and DREAM DAQ system at the cosmic ray test bench at CEA Saclay.

The system orchestrates multi-detector data acquisition runs: it ramps HV channels on a CAEN crate, starts and stops the DREAM front-end DAQ, optionally runs M3 reference tracking, and drives on-the-fly or post-run data processing (FDF decode → ROOT conversion → hit analysis).

---

## Architecture

The system follows a **client-server model over TCP sockets**. Persistent server processes are started once at the beginning of a session; the main run-control script (`daq_control.py`) acts as the client that sends commands to each server for every run.

| Component | Script | Role |
|---|---|---|
| HV server | `hv_control.py` | Controls the CAEN HV crate (set/ramp voltages, monitor) |
| DREAM DAQ server | `dream_daq_control.py` | Starts/stops the DREAM front-end DAQ, copies raw FDF data |
| M3 tracking server | `m3_tracking_control.py` | Runs the M3 reference tracker reconstruction |
| DAQ orchestrator | `daq_control.py` | Client: coordinates all servers for each sub-run |
| Processor watcher | `processor_watcher.py` | Autonomous pipeline: decode → filter → analyze ROOT files |
| Flask web app | `flask_app/app.py` | Live monitoring dashboard |

All server sessions are managed with **tmux**.

---

## Implemented Detector Types

- **Micromegas** (various geometries: mx17, urw, asacusa_strip, strip_plein, strip_strip, rd5, p2) read out via DREAM FEUs
- **BANCO silicon pixel ladders** (banco_ladder*)
- **M3 Micromegas reference trackers** (4 planes: bot_bot, bot_top, top_bot, top_top)
- **Scintillators** (top and bottom trigger counters)

Adding a new detector instance to an existing type is straightforward — see the [Adding a New Detector](#adding-a-new-detector) section. Adding a completely new detector type is also possible, but requires one additional step: creating a geometry JSON file in `config/detectors/` named after the `det_type` (e.g. `config/detectors/my_new_type.json`). This file describes the physical dimensions and strip map type of the detector and is used by the processing code. It is only strictly required if `filtering_by_m3 = True`, since the M3 filter needs to know the active area of the detector to select tracks that pass through it — without it, basic DAQ and decoding will still work.

---

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd Cosmic_Bench_DAQ_Control

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

The CAEN HV library (`caen_hv_py`) and the DREAM decode binaries (`decode`, `convert_vec_tree_to_array`, `analyze_waveforms`, `combine_feus_hits`) must be installed separately and their paths set in the run config.

---

## Configuration

### Run configuration (`run_config.py`)

Edit `run_config.py` before each session. Key parameters:

```python
self.run_name = 'my_run_name'
self.data_out_dir = '/data/cosmic_data/Run_MX/'   # Output base directory

self.m3_feu_num = 1          # FEU number of the M3 reference tracker DEU
self.power_off_hv_at_end = True   # Power off HV after the last sub-run
self.filtering_by_m3 = False      # Enable M3-based track filtering
self.save_fdfs = True             # Keep raw FDF files after decoding
self.start_time = None            # 'YYYY-MM-DD HH:MM:SS' or None to start immediately
self.gas = 'Ar/CF4 90/10'        # Gas mixture label (written to run metadata)
```

**DREAM DAQ settings** (`self.dream_daq_info`):
- `daq_config_template_path`: path to the `.cfg` file for the DREAM DAQ
- `run_directory`: local scratch directory used by the DAQ during acquisition
- `copy_on_fly`: copy FDF files to `data_out_dir` during the run

**Sub-runs** (`self.sub_runs`): a list of dicts, each specifying a `sub_run_name`, `run_time` (minutes), and `hvs` (dict of `{card: {channel: voltage}}`). The orchestrator loops over sub-runs, ramping HV and acquiring data for each.

**Detector list** (`self.included_detectors`): names of detectors active in this run. Only these are written to the run config JSON and used in processing.

### Processor configuration (`processor_config.py`)

Run `processor_config.py` to generate a JSON config for `processor_watcher.py`. Key fields: paths to decode/analyze/combine binaries, which pipeline steps to run (`do_decode`, `do_analyze`, `do_combine`), and M3 filtering options.

---

## How to Run

### 1. Start the background servers (once per session)

```bash
./start_servers_cosmics.sh
```

This launches five tmux sessions:

| tmux session | Process |
|---|---|
| `hv_control` | `python hv_control.py` |
| `dream_daq` | `python dream_daq_control.py` |
| `m3_tracking` | `python m3_tracking_control.py` |
| `daq_control` | (idle, ready to receive run commands) |
| `flask_server` | Flask monitoring dashboard |

Attach to any session with `tmux attach -t <session_name>`.

### 2. Start a run

Edit `run_config.py` (or prepare a JSON config), then attach to the `daq_control` tmux session and run the script from there:

```bash
tmux attach -t daq_control
python daq_control.py                                             # uses run_config.py directly
python daq_control.py config/json_run_configs/my_run_config.json  # or pass a JSON config
```

This single command handles the full run automatically — no need to interact with the individual servers. It follows these steps:

1. Connects to the HV and DREAM DAQ servers
2. For each sub-run defined in the config:
   - Ramps the HV channels to the specified voltages and waits until stable
   - Starts HV monitoring
   - Starts the DREAM DAQ and acquires data for the configured run time
   - Stops the DAQ and ends HV monitoring
3. Powers off HV at the end (if `power_off_hv_at_end = True`)

Alternatively, if you don't want to attach to the session, `bash_scripts/start_run.sh` sends the command to the `daq_control` tmux session from any terminal:

```bash
bash bash_scripts/start_run.sh <config_path>
```

### 3. Run pedestals

```bash
bash bash_scripts/run_pedestals.sh
```

### 4. Start the processor watcher (optional)

The processor watcher runs independently and watches for new FDF files to process on-the-fly:

```bash
python processor_watcher.py <processor_config_json_path>
```

### 5. Stop a run

```bash
bash bash_scripts/stop_run.sh
```

To stop only the current sub-run without ending the full sequence:

```bash
bash bash_scripts/stop_sub_run.sh
```

To restart all server processes:

```bash
bash bash_scripts/restart_all_tmux_processes.sh
```

---

## Data Directory Structure

```
<data_out_dir>/<run_name>/
├── run_config.json            # Copy of the run configuration
├── raw_daq_data/              # Raw FDF files from DREAM DAQ
├── decoded_root/              # Decoded ROOT files
├── filtered_root/             # M3-filtered ROOT files (if filtering enabled)
├── m3_tracking_root/          # M3 tracking reconstruction output
└── hv_monitor_*.csv           # HV monitoring logs
```

---

## Utility Scripts

| Script | Purpose |
|---|---|
| `quick_scripts/manual_hv_control.py` | Manually set/read HV channels |
| `quick_scripts/cheap_efficiency_plot.py` | Quick efficiency plots from processed data |
| `quick_scripts/cheap_time_res_plot.py` | Quick time resolution plots |
| `quick_scripts/run_config_fixer.py` | Patch existing run config JSON files |
| `elog_updater.py` | Post run summaries to the e-log |
| `get_run_events.py` | Count events in a run |
| `convert_fdf_to_root.py` | Standalone FDF → ROOT conversion |

---

## Adding a New Detector

### 1. Add an entry to `self.detectors`

Every detector that may ever be used must have an entry in the `self.detectors` list in `run_config.py`. Only detectors whose `name` appears in `self.included_detectors` are actually written to the run config JSON and used in processing.

A full detector entry looks like this:

```python
{
    'name': 'my_detector_1',          # unique identifier used everywhere
    'description': 'Notes about this detector build',  # optional, for bookkeeping
    'det_type': 'mx17',               # detector type — must match a type known to the processing code
    'det_center_coords': {            # physical center of the detector in bench coordinates (mm)
        'x': 0,
        'y': 0,
        'z': 232,
    },
    'det_orientation': {              # rotation of the detector about each axis (degrees)
        'x': 0,
        'y': 0,
        'z': 0,
    },
    'hv_channels': {                  # CAEN crate wiring: {electrode: (card, channel)}
        'drift':  (0, 7),
        'resist': (3, 0),
    },
    'dream_feus': {                   # DREAM DAQ wiring: {feu_label: (crate, feu_number)}
        'x_1': (3, 1),                # strips running along x → give hit position in y
        'x_2': (3, 2),
        'y_1': (4, 1),                # strips running along y → give hit position in x
        'y_2': (4, 2),
    },
    'dream_feu_orientation': {        # how the FEU connector is physically plugged in
        'x_1': 'inverted',            # 'normal', 'inverted', 'rotated', or 'rotated_inverted'
        'x_2': 'inverted',
        'y_1': 'inverted',
        'y_2': 'inverted',
    },
},
```

**`hv_channels`** — check the CAEN crate wiring diagram for the card and channel numbers connected to each electrode (drift, resist/mesh).

**`dream_feus`** — check the DREAM DAQ wiring for the crate and FEU numbers. The label convention is `x_N` for strips that run along the x-axis (they measure the y coordinate of a hit) and `y_N` for strips that run along the y-axis (they measure the x coordinate).

**`dream_feu_orientation`** — depends on the physical direction the FEU connector is inserted. If strips appear mirrored in the data, try `'inverted'`.

### 2. Set the position and alignment

The bench coordinate system has **z along the cosmic axis** (vertical, increasing upward), with x and y transverse. The origin is defined by the M3 reference trackers. Coordinates are in mm.

All z positions are measured relative to the physical reference points of the bench (P1, P2, stand levels, etc.) defined in `self.bench_geometry`. Use these constants rather than hardcoded absolute values so that the geometry stays consistent if the bench is reconfigured:

```python
# Detector sitting at the P1 level
'z': self.bench_geometry['p1_z'] + self.bench_geometry['board_thickness']

# Detector on stand level N (N=0 is the bottom level)
'z': self.bench_geometry['p1_z']
    + self.bench_geometry['bottom_level_z']
    + N * self.bench_geometry['level_z_spacing']
    + self.bench_geometry['board_thickness']
```

If the detector position has been measured precisely from an alignment run, use that measured value directly instead:

```python
'z': 712.7  # mm, from alignment
```

x and y offsets relative to the M3 telescope centre are also set from alignment. If the detector is centred on the telescope, use `x: 0, y: 0`.

`det_orientation` is the physical rotation of the detector about each axis in degrees. For a standard flat detector with no rotation, all three are `0`.

### 3. Add the name to `self.included_detectors`

```python
self.included_detectors = [
    'my_detector_1',
    'm3_bot_bot', 'm3_bot_top', 'm3_top_bot', 'm3_top_top',  # always include M3 reference trackers
]
```

Only detectors in this list are active in the run. The M3 reference trackers should always be included as they provide the reference tracks for efficiency and alignment measurements.

---

## Running an HV Scan

An HV scan is just a normal run where multiple sub-runs are defined, each with a different HV voltage. `daq_control.py` steps through them automatically.

### 1. Find the HV card and channel for your detector

Each detector in `run_config.py` has an `hv_channels` entry that maps the logical electrode names to `(card, channel)` pairs on the CAEN crate:

```python
'hv_channels': {
    'drift': (0, 7),   # card 0, channel 7
    'resist': (3, 0),  # card 3, channel 0
},
```

Use these card/channel numbers when building the `hvs` dict in your sub-runs.

### 2. Set the run metadata

```python
self.run_name = 'det_name_HV_scan_date'
self.gas = 'Ar/CF4 90/10'
self.power_off_hv_at_end = True
self.included_detectors = ['your_detector', 'm3_bot_bot', 'm3_bot_top', 'm3_top_bot', 'm3_top_top']
```

### 3. Define the sub-runs

The `sub_runs` list drives the scan. Each entry sets the voltages for all active channels and the acquisition time. You can write them explicitly or generate them in a loop:

```python
# Explicit list
self.sub_runs = [
    {
        'sub_run_name': 'resist_450V_drift_900V',
        'run_time': 45,   # minutes
        'hvs': {
            0: {7: 900},  # drift voltage  (card: {channel: voltage})
            3: {0: 450},  # resist voltage
        }
    },
    {
        'sub_run_name': 'resist_460V_drift_900V',
        'run_time': 45,
        'hvs': {
            0: {7: 900},
            3: {0: 460},
        }
    },
    # ...
]

# Or generate programmatically (as in the current run_config.py)
drifts = [900]
resists = [450, 460, 470, 480, 490, 500]
for drift in drifts:
    for resist in resists:
        self.sub_runs.append({
            'sub_run_name': f'resist_{resist}V_drift_{drift}V',
            'run_time': 45,
            'hvs': {
                0: {7: drift},
                3: {0: resist},
            }
        })
```

> **Note:** The `hvs` dict only needs to list channels that should be actively set for that sub-run. Any channel not listed keeps whatever voltage it was last set to. Make sure to include all channels that need to be at specific values (e.g. M3 tracker HV if the M3 is running).

### 4. Run

Start the servers if not already running, then from the `daq_control` tmux session:

```bash
python daq_control.py
```

The scan runs fully automatically — HV is ramped, data is acquired, and the next voltage step starts until all sub-runs are done.

---

## Flask Monitoring Dashboard

The Flask app serves a live DAQ status page. Once `flask_server` is running, open a browser and navigate to the host address on the configured port (default `http://localhost:5000`).
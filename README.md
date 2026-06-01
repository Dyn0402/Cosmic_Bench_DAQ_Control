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

## Supported Detectors

- **Micromegas** (various geometries: mx17, urw, asacusa_strip, strip_plein, strip_strip, rd5, p2) read out via DREAM FEUs
- **BANCO silicon pixel ladders** (banco_ladder*)
- **M3 Micromegas reference trackers** (4 planes: bot_bot, bot_top, top_bot, top_top)
- **Scintillators** (top and bottom trigger counters)

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

## Flask Monitoring Dashboard

The Flask app serves a live DAQ status page. Once `flask_server` is running, open a browser and navigate to the host address on the configured port (default `http://localhost:5000`).
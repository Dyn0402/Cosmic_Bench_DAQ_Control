# Cosmic_Bench_DAQ_Control

Control software for the high-voltage (HV) crate and DREAM DAQ system at the cosmic ray test bench at CEA Saclay.

The system orchestrates multi-detector data acquisition runs: it ramps HV channels on a CAEN crate, starts and stops the DREAM front-end DAQ, optionally runs M3 reference tracking, drives on-the-fly data processing (FDF decode → ROOT conversion → hit analysis), and produces online QA plots as data arrives.

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
| QA watcher | `qa_watcher.py` | Autonomous QA: generates per-detector plots from combined hits |
| Flask web app | `flask_app/app.py` | Live monitoring dashboard and run control UI |

All server sessions are managed with **tmux**.

---

## Implemented Detector Types

- **Micromegas** (various geometries: mx17, urw, asacusa_strip, strip_plein, strip_strip, rd5, p2) read out via DREAM FEUs
- **BANCO silicon pixel ladders** (`banco_ladder*`)
- **M3 Micromegas reference trackers** (4 planes: bot_bot, bot_top, top_bot, top_top)
- **Scintillators** (top and bottom trigger counters)

Adding a new detector instance to an existing type is straightforward — see the [Adding a New Detector](#adding-a-new-detector) section. Adding a completely new detector type requires one additional step: creating a geometry JSON file in `config/detectors/` named after the `det_type` (e.g. `config/detectors/my_new_type.json`). This is only strictly required if `filter_by_m3 = True` in `processor_config.py`; basic DAQ and decoding work without it.

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

### External dependencies

The following must be built or installed separately and their paths configured before the processor will run:

**C++ binaries (`mm_dream_reconstruction`)** — compiled binaries are git-ignored and must be built from source:
- `build/decoder/decode`
- `build/waveform_analysis/analyze_waveforms`
- `build/feu_hit_combiner/combine_feus_hits`

**M3 tracking** (`cosmic_bench_m3_tracking`) — the shell script and its compiled dependencies must be present:
- `run_tracking_single.sh` (and the DataReader / tracking binaries it calls)

These compiled binaries are git-ignored and **must be rebuilt before tracking or processing will run**. If a binary is missing, `processor_watcher.py` will print a warning at startup identifying exactly which binary is absent and where it is expected.

**CAEN HV library** — `caen_hv_py` must be installed and accessible for `hv_control.py`.

---

## Configuration

### Site configuration — `BASE_DISK` and `PROJECT`

At the top of `run_config.py` are three module-level constants shared across all scripts:

```python
BASE_DISK     = '/mnt/cosmic_data/'   # mount point of the data disk
PROJECT       = 'MX17'               # project subdirectory (e.g. 'MX17', 'P2', 'clas12', 'EIC')
BASE_DATA_DIR = f'{BASE_DISK}{PROJECT}/'
```

All data paths (`Run/`, `pedestals/`, `dream_run/`, etc.) are constructed relative to `BASE_DATA_DIR`. `processor_config.py` and `qa_config.py` both import `BASE_DATA_DIR` from here, so changing it in one place propagates everywhere.

You can also switch `BASE_DISK` and `PROJECT` from the Flask dashboard without editing the file — see [Flask Monitoring Dashboard](#flask-monitoring-dashboard).

### Run configuration (`run_config.py`)

Edit `run_config.py` before each session. Key top-level parameters:

```python
self.run_name            = 'my_run_name'
self.m3_feu_num          = 1      # FEU number of the M3 reference tracker DEU
self.power_off_hv_at_end = True   # Power off HV after the last sub-run
self.save_fdfs           = True   # Keep raw FDF files after processing
self.start_time          = None   # 'YYYY-MM-DD HH:MM:SS' or None to start immediately
self.gas                 = 'Ar/Iso 95/5'  # Gas mixture label (written to run metadata)
```

Paths are derived automatically from `BASE_DATA_DIR`:

```python
self.base_out_dir  = BASE_DATA_DIR
self.data_out_dir  = f'{self.base_out_dir}Run/'
self.run_out_dir   = f'{self.data_out_dir}{self.run_name}/'
```

#### DREAM DAQ settings (`self.dream_daq_info`)

These are the baseline DAQ parameters applied to every sub-run. Any of them can be overridden per sub-run (see below).

| Key | Type | Description |
|---|---|---|
| `ip` | str | IP address of the DREAM DAQ machine |
| `port` | int | TCP port for the DREAM DAQ server |
| `daq_config_template_path` | str | Path to the `.cfg` template file for the DREAM DAQ |
| `run_directory` | str | Local scratch directory used by the DAQ during acquisition |
| `copy_on_fly` | bool | Copy FDF files to `data_out_dir` during the run (True) or only after (False) |
| `n_samples_per_waveform` | int | Number of waveform samples per channel (e.g. 32) |
| `zero_suppress` | bool | Enable zero-suppression mode in the DAQ |
| `pedestal_subtraction` | bool | Enable online pedestal subtraction in FEUs |
| `common_noise_subtraction` | bool | Enable common-mode noise subtraction in FEUs |
| `zs_type` | str | Zero-suppression algorithm: `'tpc'` or `'tracker'` |
| `zs_check_sample` | int | Number of extra samples read out past a ZS threshold crossing (0–4) |
| `sample_period` | int | ADC sampling period in ns (e.g. 60) |
| `pedestals_dir` | str or None | Top-level directory for pedestal runs; `None` to ignore |
| `pedestals` | str | Which pedestal run to use: `'latest'` or a specific directory name |
| `do_pedestal_threshold_run` | bool | Set `Sys Action PedThrRun` in the DREAM `.cfg` |
| `do_trigger_threshold_run` | bool | Set `Sys Action TrgThrRun` in the DREAM `.cfg` |
| `do_data_run` | bool | Set `Sys Action DataRun` in the DREAM `.cfg` |

#### Sub-runs (`self.sub_runs`)

`self.sub_runs` is a list of dicts, each defining one acquisition segment. The orchestrator loops through them in order, ramping HV and acquiring data for each.

Required keys per sub-run:

| Key | Type | Description |
|---|---|---|
| `sub_run_name` | str | Name of this segment (used as subdirectory name) |
| `run_time` | int/float | Acquisition duration in minutes |
| `hvs` | dict | HV settings: `{card: {channel: voltage}}` |

**Per-subrun DAQ overrides** — any key from `dream_daq_info` can be added to a sub-run dict to override only that sub-run's DAQ configuration. The orchestrator merges the global `dream_daq_info` with the sub-run overrides before configuring the DAQ. This makes it easy to mix readout modes within a single session:

```python
# Sub-run without zero suppression
{
    'sub_run_name': 'no_zs',
    'run_time': 10,
    'hvs': {0: {7: 900}, 3: {0: 500}},
    'zero_suppress': False,
    'pedestals': 'pedestals_290',
},
# Next sub-run with ZS enabled
{
    'sub_run_name': 'zs_tpc',
    'run_time': 10,
    'hvs': {0: {7: 900}, 3: {0: 500}},
    'zero_suppress': True,
    'zs_type': 'tpc',
    'zs_check_sample': 1,
    'pedestals': 'pedestals_290',
},
```

Any key not overridden in the sub-run dict falls back to the value in `dream_daq_info`.

#### HV settings (`self.hv_info`)

```python
self.hv_info = {
    'ip': '192.168.10.81',
    'username': 'admin',
    'password': 'admin',
    'n_cards': 4,
    'n_channels_per_card': 12,
    'hv_monitoring': True,       # Record HV to CSV during the run
    'monitor_interval': 2,       # Seconds between HV monitoring reads
}
```

### Processor configuration (`processor_config.py`)

Edit `processor_config.py` and run it to regenerate `config/processor_config.json`. The Flask UI reads that JSON when "Start Processor" is pressed.

Key fields:

| Key | Description |
|---|---|
| `runs_dir` | Top-level directory containing all `run_N/` subdirectories (derived from `BASE_DATA_DIR`) |
| `decode_executable` | Path to the compiled `decode` binary |
| `analyze_executable` | Path to the compiled `analyze_waveforms` binary |
| `combine_executable` | Path to the compiled `combine_feus_hits` binary |
| `do_decode` / `do_analyze` / `do_combine` | Enable/disable each pipeline stage |
| `m3_feu_num` | FEU number of the M3 tracker (int or null) |
| `do_m3_tracking` | Run M3 tracking reconstruction on M3 FEU files |
| `tracking_sh_path` | Path to `run_tracking_single.sh` in `cosmic_bench_m3_tracking` |
| `tracking_run_dir` | Working directory for the M3 tracking program |
| `filter_by_m3` | Filter decoded ROOT files to only M3-traversed events (requires `do_m3_tracking`) |
| `pedestal_loc` | `'same'` (FDFs alongside data), `'abs'` (fixed path), or `'find'` (read `pedestal_run.txt`) |
| `pedestal_dir` | Base directory for pedestal runs (used with `'abs'` or `'find'` modes) |
| `cpp_setup_script` | Shell commands to source the C++ environment (ROOT, devtoolset) before running binaries |
| `include_runs` | List of run names to process exclusively; `null` means all |
| `exclude_runs` | List of run names to skip |
| `poll_interval` | Seconds between full directory scans (default 30) |
| `stale_run_days` | Runs with no new FDFs for this many days are checked once then skipped (default 4) |
| `free_threads` | CPU threads to leave free during parallel decode/analyze (default 2) |

At startup, `processor_watcher.py` checks that all enabled binary paths exist on disk and prints a warning for any that are missing — the affected pipeline steps will fail when reached.

### QA configuration (`qa_config.py`)

Edit `qa_config.py` and run it to regenerate `config/qa_config.json`. The Flask UI reads that JSON when "Start QA Watcher" is pressed.

| Key | Description |
|---|---|
| `runs_dir` | Top-level directory containing all run subdirectories (derived from `BASE_DATA_DIR`) |
| `combined_hits_inner_dir` | Subdirectory name for combined hits files (must match processor config) |
| `qa_file_mode` | `'first'` — QA once per subrun on file 0 (fast, default); `'all'` — accumulate all files; `'per_file'` — separate plot set per file |
| `include_runs` / `exclude_runs` | Run name filtering (same behaviour as processor) |
| `poll_interval` | Seconds between scans (default 10) |
| `stale_run_days` | Runs ignored after this many days of inactivity (default 2) |
| `memory_kill_pct` | Kill the QA subprocess if system RAM usage exceeds this percentage (default 80) |

---

## How to Run

### 1. Start the background servers (once per session)

```bash
./bash_scripts/restart_daq_tmux_processes.sh
```

This launches tmux sessions for all background services. To start the Flask dashboard separately:

```bash
./bash_scripts/start_flask.sh
```

| tmux session | Process |
|---|---|
| `daq_control` | `python daq_control.py` (orchestrator, idle until a run command is sent) |
| `dream_daq` | `python dream_daq_control.py` |
| `hv_control` | `python hv_control.py` |
| `processor` | `python processor_watcher.py` (started separately via Flask or CLI) |
| `qa_watcher` | `python qa_watcher.py` (started separately via Flask or CLI) |

Attach to any session with `tmux attach -t <session_name>`.

### 2. Configure the run

Edit `run_config.py` — or use the Flask dashboard to switch `BASE_DISK`/`PROJECT` and then configure a JSON run config. When the file is ready, run it to produce a JSON config:

```bash
python run_config.py
```

This writes `config/json_run_configs/run_config.json`.

Alternatively, use `iterate_run_num.py` to auto-increment the run number in `run_config.py` before generating the JSON. It handles arbitrary run name formats (not just `run_N`) by appending or incrementing a trailing `_N` suffix, so existing runs on disk are never overwritten:

```bash
python iterate_run_num.py
```

### 3. Start a run

**From the Flask dashboard** (recommended): press "Run Config Py" to regenerate the JSON and start the DAQ in one step.

**From the command line**: attach to the `daq_control` tmux session and run:

```bash
tmux attach -t daq_control
python daq_control.py                                              # uses run_config.py directly
python daq_control.py config/json_run_configs/my_run_config.json  # or pass a JSON config
```

Or send the command from any terminal without attaching:

```bash
bash bash_scripts/start_run.sh <config_path>
```

`daq_control.py` handles the full run automatically:

1. Connects to the HV and DREAM DAQ servers
2. For each sub-run:
   - Ramps the HV channels to the specified voltages and waits until stable
   - Applies any per-subrun DAQ overrides, then starts the DREAM DAQ
   - Acquires data for the configured run time
   - Stops the DAQ and ends HV monitoring
3. Powers off HV at the end (if `power_off_hv_at_end = True`)

### 4. Run pedestals

```bash
bash bash_scripts/run_pedestals.sh
```

This uses `run_config_pedestals.py`, which inherits from `run_config.Config()` and overrides only the pedestal-specific settings (ZS off, pedestal threshold run enabled, short run time).

### 5. Start the processor (on-the-fly processing)

From the Flask dashboard, press "Start Processor" — this regenerates `config/processor_config.json` from `processor_config.py` and launches `processor_watcher.py` in the `processor` tmux session.

From the command line:

```bash
python processor_config.py                                  # regenerate JSON config
python processor_watcher.py config/processor_config.json    # start the watcher
```

The processor watches all run directories under `runs_dir`, processing each new FDF file group as it becomes stable (two consecutive polls with unchanged file sizes). The pipeline per file group is:

1. **M3 tracking** — decode M3 FEU FDFs via `run_tracking_single.sh`
2. **Decode** — convert non-M3 FDFs to ROOT via the `decode` binary
3. **M3 filter** *(optional, `filter_by_m3 = True`)* — keep only events with an M3 track
4. **Analyze waveforms** — produce per-FEU hit ROOT files via `analyze_waveforms`
5. **Combine hits** — merge per-FEU files into a single combined ROOT file via `combine_feus_hits`

### 6. Start the QA watcher (online QA plots)

From the Flask dashboard, press "Start QA" — this regenerates `config/qa_config.json` from `qa_config.py` and launches `qa_watcher.py` in the `qa_watcher` tmux session.

From the command line:

```bash
python qa_config.py                            # regenerate JSON config
python qa_watcher.py config/qa_config.json     # start the watcher
```

The QA watcher watches for new combined-hits files and runs `online_qa/detector_qa.py` on each subrun. It monitors system RAM every second and kills the QA subprocess if RAM usage exceeds `memory_kill_pct` (default 80%), retrying the killed subrun on the next poll cycle. QA output plots are written to `analysis/` under the project directory.

### 7. Stop a run

From the Flask dashboard: press "Stop Run" or "Stop Sub-Run".

From the command line:

```bash
bash bash_scripts/stop_run.sh       # stop the full run (all sub-runs)
bash bash_scripts/stop_sub_run.sh   # stop only the current sub-run
```

To restart all server processes:

```bash
bash bash_scripts/restart_daq_tmux_processes.sh
```

---

## Data Directory Structure

Data is written per-subrun under `BASE_DATA_DIR`:

```
<BASE_DATA_DIR>/
├── Run/
│   └── <run_name>/
│       ├── run_config.json            # copy of the run configuration
│       └── <sub_run_name>/
│           ├── raw_daq_data/          # raw FDF files from the DREAM DAQ
│           ├── decoded_root/          # decoded ROOT files (from 'decode' binary)
│           ├── hits_root/             # per-FEU hit ROOT files (from 'analyze_waveforms')
│           ├── combined_hits_root/    # merged hit ROOT files (from 'combine_feus_hits')
│           ├── m3_tracking_root/      # M3 tracking output (if do_m3_tracking)
│           ├── filtered_root/         # M3-filtered ROOT files (if filter_by_m3)
│           └── hv_monitor.csv         # HV monitoring log for this sub-run
├── pedestals/
│   └── <pedestal_run_name>/
│       └── pedestals/
│           └── raw_daq_data/          # pedestal FDF files
├── dream_run/
│   └── <run_name>/                    # DREAM DAQ local scratch area during acquisition
└── analysis/
    └── <run_name>/
        └── <sub_run_name>/
            └── *.png                  # QA plots from qa_watcher
```

---

## Flask Monitoring Dashboard

Once the Flask server is running, open a browser at `http://<host>:5001`.

The dashboard provides:

- **Status panels** for all tmux sessions (daq_control, dream_daq, hv_control, processor, qa_watcher) with live status fields and colour-coded state
- **Live event count** for the current run, including in-progress sub-run events
- **Run control buttons**: Start Run (from JSON config), Run Config Py (regenerate + start), Stop Sub-Run, Stop Run, Take Pedestals, Git Reset
- **Processor and QA watcher controls**: Start/Stop buttons that also regenerate the respective JSON configs before launching
- **Project switcher**: change `BASE_DISK` and `PROJECT` without editing `run_config.py` directly; the change is written atomically to `run_config.py` and propagates to processor and QA config on their next start
- **HV monitoring charts**: voltage and current per channel over the last 1000 readings
- **Analysis image browser**: navigate the `analysis/` directory tree and view QA PNG plots inline

All DAQ events (project changes, etc.) are logged to `logs/daq_events.log`.

---

## Utility Scripts

| Script | Purpose |
|---|---|
| `iterate_run_num.py` | Auto-increment the run name in `run_config.py` before starting a new run |
| `get_run_events.py` | Count events in a run by reading DREAM RunCtrl `.log` files |
| `quick_scripts/manual_hv_control.py` | Manually set/read HV channels |
| `quick_scripts/cheap_efficiency_plot.py` | Quick efficiency plots from processed data |
| `quick_scripts/cheap_time_res_plot.py` | Quick time resolution plots |
| `quick_scripts/run_config_fixer.py` | Patch existing run config JSON files |
| `quick_scripts/convert_fdf_to_root.py` | Standalone FDF → ROOT conversion |
| `scripts/elog_updater.py` | Post run summaries to the e-log |

---

## Adding a New Detector

### 1. Add an entry to `self.detectors`

Every detector that may ever be used must have an entry in `self.detectors` in `run_config.py`. Only detectors whose `name` appears in `self.included_detectors` are written to the run config JSON and used in processing.

A full DREAM detector entry:

```python
{
    'name': 'my_detector_1',           # unique identifier used everywhere
    'description': 'Notes about build', # optional, for bookkeeping
    'det_type': 'mx17',                # must match a type known to the processing code
    'resist_type': 'strip',            # resistive layer type (e.g. 'strip', 'mesh')
    'det_center_coords': {             # physical centre in bench coordinates (mm)
        'x': 0,
        'y': 0,
        'z': 232,
    },
    'det_orientation': {               # rotation about each axis (degrees)
        'x': 0,
        'y': 0,
        'z': 0,
    },
    'hv_channels': {                   # CAEN crate wiring: {electrode: (card, channel)}
        'drift':  (0, 7),
        'resist': (3, 0),
    },
    'dream_feus': {                    # DREAM DAQ wiring: {feu_label: (crate, feu_number)}
        'x_1': (3, 1),                 # strips along x → measure y hit position
        'x_2': (3, 2),
        'y_1': (4, 1),                 # strips along y → measure x hit position
        'y_2': (4, 2),
    },
    'dream_feu_orientation': {         # physical FEU connector direction
        'x_1': 'inverted',            # 'normal', 'inverted', 'rotated', 'rotated_inverted'
        'x_2': 'inverted',
        'y_1': 'inverted',
        'y_2': 'inverted',
    },
},
```

**`hv_channels`** — check the CAEN crate wiring diagram for the card and channel numbers.

**`dream_feus`** — check the DREAM DAQ wiring. The label convention is `x_N` for strips running along x (they measure the y hit coordinate) and `y_N` for strips running along y (they measure x).

**`dream_feu_orientation`** — depends on the physical direction the FEU connector is inserted. If strips appear mirrored in the data, try `'inverted'`.

### 2. Set the position and alignment

The bench coordinate system has **z along the cosmic axis** (vertical, increasing upward), with x and y transverse. The origin is defined by the M3 reference trackers. Coordinates are in mm.

Use `self.bench_geometry` constants for z positions rather than hardcoded values:

```python
# Detector at the P1 level
'z': self.bench_geometry['p1_z'] + self.bench_geometry['board_thickness']

# Detector on stand level N (N=0 is the bottom level)
'z': self.bench_geometry['p1_z']
    + self.bench_geometry['bottom_level_z']
    + N * self.bench_geometry['level_z_spacing']
    + self.bench_geometry['board_thickness']
```

If the position has been measured from an alignment run, use that value directly:

```python
'z': 712.7  # mm, from alignment
```

### 3. Add the name to `self.included_detectors`

```python
self.included_detectors = [
    'my_detector_1',
    'm3_bot_bot', 'm3_bot_top', 'm3_top_bot', 'm3_top_top',  # always include M3 trackers
]
```

Only detectors in this list are active. The M3 reference trackers should always be included.

---

## Running an HV Scan

An HV scan is a normal run where multiple sub-runs step through different voltages. `daq_control.py` handles the stepping automatically.

### 1. Set run metadata

```python
self.run_name            = 'det_name_HV_scan_date'
self.gas                 = 'Ar/Iso 95/5'
self.power_off_hv_at_end = True
self.included_detectors  = ['your_detector', 'm3_bot_bot', 'm3_bot_top', 'm3_top_bot', 'm3_top_top']
```

### 2. Define the sub-runs

```python
# Explicit list
self.sub_runs = [
    {
        'sub_run_name': 'resist_450V_drift_900V',
        'run_time': 45,
        'hvs': {0: {7: 900}, 3: {0: 450}},
    },
    {
        'sub_run_name': 'resist_460V_drift_900V',
        'run_time': 45,
        'hvs': {0: {7: 900}, 3: {0: 460}},
    },
]

# Or generate programmatically
for resist in [450, 460, 470, 480, 490, 500]:
    self.sub_runs.append({
        'sub_run_name': f'resist_{resist}V_drift_900V',
        'run_time': 45,
        'hvs': {0: {7: 900}, 3: {0: resist}},
    })
```

The `hvs` dict only needs to list channels that should be actively set for that sub-run. Any channel not listed keeps whatever voltage it was last set to.

### 3. Run

```bash
python daq_control.py
```

The scan runs fully automatically — HV is ramped, data is acquired, and the next voltage step begins until all sub-runs are done.
# ROOT version: stay on 6.30.02 (deliberate)

**This repo's DAQ/processing machines must keep ROOT 6.30.02. Do not "update" them to
6.40.x to match the rest of the setup.**

Decision (Dylan, 2026-10-21): the rest of the analysis environment (desktop, laptop,
lxplus) was aligned on ROOT 6.40.04 / Geant4 11.4.3 / Garfield++ in October 2026. The
Cosmic Bench DAQ machines are the one exception, because the old ROOT is needed to run
on the other machine.

## Where it is set

| File | What |
|---|---|
| `processor_config.py` (`cpp_setup_script`) | `source ~/root_6_30_02/root-build/bin/thisroot.sh && source scl_source enable devtoolset-9` |
| `config/processor_config.json` (`cpp_setup_script`) | same line, used by the watcher at runtime |
| `quick_scripts/env_check.py` (`CPP_SETUP`, and the `ROOTSYS points to root_6_30_02` check) | same line, plus a check that fails if ROOT is not 6.30.02 |

The DAQ machine is CentOS-style (`scl_source enable devtoolset-9`, gcc 9), so ROOT 6.40
would also need a newer compiler and a rebuild of the C++ tools (`decode`,
`analyze_waveforms`, `combine_feus_hits`, DreamDataReader) against it.

## Consequences

- ROOT files written here come from 6.30.02. 6.40 reads them fine; the reverse is not
  guaranteed, so analysis machines on 6.40 can read DAQ output but should not write files
  the DAQ machine has to read.
- If you copy this repo to the desktop/laptop (ROOT 6.40.04 is the default there), the
  `cpp_setup_script` path `~/root_6_30_02/...` will not exist. The old install on the
  desktop is `~/Software/root_6_30` (kept on purpose, not deleted).
- Switching the DAQ machines to 6.40 is a separate, deliberate piece of work: new compiler,
  rebuild of all C++ binaries, test on a pedestal run first.

Tracked in `claude-skills/docs/hep-stack/README.md` ("ROOT exception").

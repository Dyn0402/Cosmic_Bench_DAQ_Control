#!/usr/bin/env python3
"""
Environment proof-of-concept for processor_watcher.py.

Checks:
  1. cpp_env builds correctly (ROOT 6.30.02 + devtoolset-9 active)
  2. Default process env is isolated (no newer ROOT leaked in)
  3. decode executable runs successfully on one real FDF → produces ROOT file
  4. M3 tracking runs in default env → produces _rays.root file

Edit the CONFIGURE block below before running.
"""

import os
import re
import sys
import subprocess
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIGURE THESE
# ---------------------------------------------------------------------------
TEST_SUBRUN_DIR = Path('/data/cosmic_data/Run_MX/FIXME_run/FIXME_subrun')
RAW_INNER       = 'raw_daq_data'
M3_FEU_NUM      = 1

MM_BUILD        = '/local/home/usernsw/mm_dream_reconstruction/build'
DECODE_EXE      = f'{MM_BUILD}/decoder/decode'

M3_TRACKING_DIR = '/local/home/usernsw/dylan/m3_tracking/'
TRACKING_SH     = f'{M3_TRACKING_DIR}run_tracking_single.sh'

CPP_SETUP = (
    'source ~/root_6_30_02/root-build/bin/thisroot.sh && '
    'source scl_source enable devtoolset-9'
)
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).parent))

_PASS = '\033[92mPASS\033[0m'
_FAIL = '\033[91mFAIL\033[0m'
_results = []


def check(label, ok, detail=''):
    tag = _PASS if ok else _FAIL
    msg = f"  [{tag}] {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    _results.append((label, ok))
    return ok


# ---------------------------------------------------------------------------
# Helpers (same logic as processor_watcher._build_cpp_env)
# ---------------------------------------------------------------------------

def _build_cpp_env(setup_script):
    result = subprocess.run(
        ['bash', '-l', '-c', f'{setup_script} && env -0'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"    bash stderr: {result.stderr[:300]}")
    env = {}
    for entry in result.stdout.split('\0'):
        if '=' in entry:
            k, _, v = entry.partition('=')
            env[k] = v
    return env or None


def _get_feu_num(filename):
    m = re.search(r'_(\d{3})_(\d{2})[._]', filename)
    return int(m.group(2)) if m else -1


def _get_file_num(filename):
    m = re.search(r'_(\d{3})_(\d{2})[._]', filename)
    return int(m.group(1)) if m else -1


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_cpp_env():
    print("\n=== 1. Build C++ environment ===")
    cpp_env = _build_cpp_env(CPP_SETUP)
    if not check("cpp_env built (non-empty)", cpp_env is not None):
        return None

    rootsys = cpp_env.get('ROOTSYS', '')
    check("ROOTSYS set in cpp_env", bool(rootsys), rootsys or "not set")
    check("ROOTSYS points to root_6_30_02", 'root_6_30_02' in rootsys, rootsys)

    # GCC version via devtoolset-9
    r = subprocess.run(['gcc', '--version'], capture_output=True, text=True, env=cpp_env)
    gcc_line = r.stdout.splitlines()[0] if r.stdout else ''
    check("gcc runs in cpp_env", r.returncode == 0, gcc_line)
    check("GCC 9.x active (devtoolset-9)", '(GCC) 9.' in gcc_line, gcc_line)

    # ROOT version
    r = subprocess.run(['root', '--version'], capture_output=True, text=True, env=cpp_env)
    root_out = (r.stdout + r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr) else ''
    check("root --version runs in cpp_env", r.returncode == 0, root_out)

    return cpp_env


def test_default_env_isolation():
    print("\n=== 2. Default process env isolation ===")
    rootsys = os.environ.get('ROOTSYS', '')
    check("ROOTSYS not set in default env", not rootsys, rootsys or "not set")

    r = subprocess.run(['gcc', '--version'], capture_output=True, text=True)
    gcc_line = r.stdout.splitlines()[0] if r.stdout else ''
    check("gcc --version runs in default env", r.returncode == 0, gcc_line)
    check("GCC 9.x NOT active in default env", '(GCC) 9.' not in gcc_line, gcc_line)


def test_decode(cpp_env):
    print("\n=== 3. Decode one FDF with cpp_env ===")
    raw_dir = TEST_SUBRUN_DIR / RAW_INNER
    if not check("raw_dir exists", raw_dir.exists(), str(raw_dir)):
        return

    fdfs = sorted([f for f in raw_dir.iterdir()
                   if f.suffix == '.fdf' and '_datrun_' in f.name
                   and _get_feu_num(f.name) != M3_FEU_NUM])
    if not check("non-M3 data FDF found", bool(fdfs), f"{len(fdfs)} found"):
        return

    fdf = fdfs[0]
    print(f"    Using: {fdf.name}")
    check("decode exe exists", Path(DECODE_EXE).exists(), DECODE_EXE)

    with tempfile.TemporaryDirectory() as tmp:
        root_out = Path(tmp) / fdf.with_suffix('.root').name
        r = subprocess.run([DECODE_EXE, str(fdf), str(root_out)],
                           env=cpp_env, capture_output=True, text=True)
        check("decode returned 0", r.returncode == 0,
              r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "ok")
        if root_out.exists():
            check("output ROOT file created", True, f"size={root_out.stat().st_size} bytes")
        else:
            check("output ROOT file created", False, "file missing")


def test_m3_tracking():
    print("\n=== 4. M3 tracking in default env ===")
    raw_dir = TEST_SUBRUN_DIR / RAW_INNER
    if not raw_dir.exists():
        check("raw_dir exists (m3 test)", False, str(raw_dir))
        return

    m3_fdfs = sorted([f for f in raw_dir.iterdir()
                      if f.suffix == '.fdf' and '_datrun_' in f.name
                      and _get_feu_num(f.name) == M3_FEU_NUM])
    if not check("M3 data FDF found", bool(m3_fdfs), f"{len(m3_fdfs)} found"):
        return

    fdf = m3_fdfs[0]
    fnum = _get_file_num(fdf.name)
    print(f"    Using: {fdf.name}  (file_num={fnum})")
    check("tracking script exists", Path(TRACKING_SH).exists(), TRACKING_SH)

    try:
        from m3_tracking_control import m3_tracking
        check("m3_tracking_control imported in default env", True)
    except ImportError as e:
        check("m3_tracking_control imported in default env", False, str(e))
        return

    with tempfile.TemporaryDirectory() as tmp:
        m3_tracking(str(raw_dir) + '/', TRACKING_SH, M3_TRACKING_DIR,
                    out_dir=tmp + '/', m3_feu_num=M3_FEU_NUM, file_num=fnum)
        rays = list(Path(tmp).glob('*_rays.root'))
        check("_rays.root output created", bool(rays),
              rays[0].name if rays else "no file found")


# ---------------------------------------------------------------------------

def main():
    print(f"\nSubrun under test: {TEST_SUBRUN_DIR}")

    cpp_env = test_cpp_env()
    test_default_env_isolation()
    if cpp_env:
        test_decode(cpp_env)
    else:
        print("\n=== 3. Decode — SKIPPED (cpp_env failed to build) ===")
    test_m3_tracking()

    passed = sum(1 for _, ok in _results if ok)
    total  = len(_results)
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed")
    if passed < total:
        print("Failed checks:")
        for label, ok in _results:
            if not ok:
                print(f"  - {label}")
    print()


if __name__ == '__main__':
    main()

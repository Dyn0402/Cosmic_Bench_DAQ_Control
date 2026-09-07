# Disk layout: separate the DREAM write disk from the processing disk

## TL;DR

Put the disk the **DREAM DAQ writes to** and the disk the **processor reads from /
writes results to** on **two different physical drives**. When they share one
spinning disk, the on-the-fly copy and the decode → analyze → combine pipeline
fight for a single mechanical head, and throughput collapses from the disk's
~100–150 MB/s sequential rate down to ~5–20 MB/s.

---

## General principle

The pipeline is I/O-heavy and runs several concurrent read+write streams at once:

- DREAM DAQ writing new `.fdf` files (to `dream_run/`)
- the on-the-fly copy reading the source and writing the watched run tree
- `decode` reading `.fdf`, writing `decoded_root/`
- `analyze_waveforms` reading `decoded_root/`, writing `hits_root/`
- `combine_feus_hits` reading `hits_root/`, writing `combined_hits_root/`

On a **single mechanical (rotational) disk**, every one of those streams competes
for one read/write head. A spinning disk is fast only for *sequential* access; the
moment you interleave multiple read and write streams it **seek-thrashes**, and
effective throughput drops by 5–20×. Files here are large (often 0.5–1 GB per FEU,
several GB per file number), so the head spends most of its time seeking between
the source region, the destination region, and the journal.

### What to do

1. **Split the disks (biggest win).** Keep the DAQ's write target on one physical
   drive and put the processing tree (the watcher's `runs_dir` and all of its
   `decoded_root/`, `hits_root/`, `combined_hits_root/`, … subdirs) on a *different*
   physical drive. Then the copy becomes a clean read-from-A → write-to-B, and the
   processor's reads/writes no longer collide with the DAQ's writes.
   - Use **separate spindles**, not just separate partitions on the same disk.
     Two partitions on one HDD still share one head and gain nothing.
   - An internal SATA disk is generally a better processing target than a USB HDD.

2. **Don't copy from a disk to itself.** If the copy source and destination live on
   the same drive, the on-the-fly copy duplicates multi-GB files onto the same
   spindle — doubling write I/O *and* storage for little benefit. Either point the
   destination at a different disk (so the copy is useful) or process in place and
   drop the copy.

3. **Match processing parallelism to the disk, not the CPU.** The watcher runs
   `n_threads = cpu_count − free_threads` concurrent decode/analyze jobs. When the
   bottleneck is a single HDD, *more* parallel jobs means *more* seeking and *less*
   total throughput. On a single spinning disk, cap concurrent disk jobs to ~1–2
   (raise `free_threads`). Higher parallelism only pays off when the processing
   disk can absorb concurrent streams (SSD, or a striped/RAID array).

4. **Prefer an SSD for the processing disk if you want a step change.** This
   workload is seek-bound. An SSD has effectively no seek penalty and handles many
   concurrent read+write streams without the throughput collapse — even a USB-3 SSD
   will dramatically outperform a USB-3 mechanical HDD here.

5. **Check the link, but it's rarely the limit.** Confirm the drive negotiates
   USB 3.0 (`lsusb -t` → 5000M) rather than USB 2.0 (480M). USB 2.0 caps real
   throughput around 30–40 MB/s. But a single mechanical disk usually bottlenecks
   *below* even the USB-2 ceiling under this concurrent workload, so the link is
   usually not the thing to fix first.

### Quick diagnosis checklist

```sh
# Is the processing disk mechanical?  1 = HDD (seeky), 0 = SSD
cat /sys/block/<dev>/queue/rotational

# Do source and destination resolve to the SAME physical device?
df --output=source <dream_write_dir>
df --output=source <processing_runs_dir>
# If both print the same /dev/..., they share one spindle — split them.

# USB link speed (5000M = USB3, 480M = USB2)
lsusb -t

# Live latency/util while a run processes.  High await (>50–100 ms) on a
# rotational disk under load = seek thrashing.
iostat -dx <dev> 1 5
```

---

## This system (as found, June 2026)

Host: `rays_daplxa`. The DAQ and the processor were both pointed at one USB drive.

| Fact | Value |
|------|-------|
| Mount | `/mnt/cosmic_data` = `/dev/sdd1`, ext4, `data=ordered` |
| Drive | Transcend USB HDD, `rotational=1` (mechanical) |
| USB link | **5000 Mbps (USB 3.0)** — link is *not* the bottleneck |
| DAQ write dir | `/mnt/cosmic_data/MX17/dream_run/` → `/dev/sdd1` |
| Processing dir | `/mnt/cosmic_data/MX17/Run/` → **`/dev/sdd1` (same disk!)** |
| Observed copy rate | ~20 MB/s steady, dropping to **~5–6 MB/s** once the processor started working the same disk |
| `iostat` await | 150–480 ms even near-idle (mechanical seek latency) |

**Diagnosis.** `dream_run/` (DAQ writes + copy source) and `Run/` (copy dest + all
processing) are on the **same physical USB HDD**. Every copy is read+write on one
head, and `decode`/`analyze`/`combine` pile more concurrent streams onto the same
spindle. That seek contention — not the USB link — is why throughput sits at
~20 MB/s and collapses to ~5 MB/s under load. File sizes were 566 MB (file_num 001)
and 954 MB (file_num 000) per FEU, ~3–5 GB per file number, so the copy alone takes
minutes and overlaps later file numbers (the cause of out-of-order pickup by the
watcher).

**Recommended fix for this host (highest leverage first).**

1. **Repoint `Run/` (processing tree) to a different physical disk.** Spare spindles
   available: internal SATA **`/dev/sdb1` (1.8 T, mounted `/data`)** and another USB
   drive **`/dev/sdc` (3.7 T)**. Best option is the internal SATA `/data`: keep
   `dream_run/` on `sdd`, point the processor's `runs_dir` at `/data/...`. The copy
   then reads `sdd` and writes `/data` — no shared-head contention.
2. **Lower processor parallelism** while the target stays a single HDD (raise
   `free_threads` so only ~1–2 decode/analyze jobs run at once).
3. **Remove the NFS export** — `/mnt/cosmic_data 132.166.0.0/16(rw,async,no_root_squash,no_subtree_check)`
   is still active with no clients; not needed and a security hole.
4. **Minor:** investigate the periodic kernel message
   `sdd1: rw=0, want=1953520008, limit=1953520002` (a read ~6 sectors past the
   partition end, every ~20 min — likely a monitoring/backup tool); consider
   mounting `noatime`.

### Where these live in the code

- DAQ write dir / processing run dir are derived from `run_config.py`
  (`BASE_DISK`, `PROJECT`, `BASE_DATA_DIR`; `run_directory` = `…/dream_run/<run>/`).
- The processor's `runs_dir` and inner dir names come from `processor_config.py`
  (`BASE_DATA = f'{BASE_DATA_DIR}Run/'`).
- The on-the-fly copy is `copy_files_on_the_fly()` in `dream_daq_control.py`
  (source = DAQ `sub_run_dir`, dest = the watched `Run/` tree).

To split the disks, the change is mostly in those config paths — point the
processing side (`processor_config.py` `runs_dir`, and the copy destination in
`dream_daq_control.py`) at a path on the second disk, leaving the DAQ write target
on the first.

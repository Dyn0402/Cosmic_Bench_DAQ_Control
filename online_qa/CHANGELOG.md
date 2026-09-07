# online_qa changelog

## 2026-06-18 — Fix waveform-stats crash and reduce QA memory usage

Context: `qa_watcher` (running on the daq machine in the `qa_watcher` tmux
session) was repeatedly failing. Two distinct problems, plus a memory cleanup.

### 1. `suptitle` TypeError (crash on every waveform-stats plot)
`MAX_ENTRIES_PER_FILE` had been set to `None` (read all entries per file), but
`_plot_wf_mean_rms` formatted it unconditionally with a thousands separator:

```python
fig.suptitle(f'... (≤{MAX_ENTRIES_PER_FILE:,} waveforms/file)', ...)
```

`None:,` is not a valid format spec → `TypeError: unsupported format string
passed to NoneType.__format__`, which aborted the whole QA run.

Fix: build the caption conditionally — `"all waveforms/file"` when the cap is
`None`, otherwise the `≤N` text.

### 2. `MemoryError` in waveform mean/RMS (long runs)
`_load_wf_stats_from_decoded` loaded *every* waveform row from *every* decoded
file into one concatenated DataFrame, then ran
`groupby(['channel','sample'])`. With the cap removed, long runs produced tens
of millions of rows (one observed run: 55M), and pandas 0.7's groupby tried to
allocate a 55M-element int64 array → OOM.

Fix: stream file-by-file and accumulate per-`(channel, sample)` count / sum /
sum-of-squares into small dense arrays, then compute
`mean = sum/cnt` and `rms = sqrt(sumsq/cnt − mean²)` at the end. Peak memory is
now bounded by a single file plus the (small) accumulators, independent of run
length. Drops the pandas groupby entirely. Results are numerically identical.

### 3. `_load_hits` peak-memory reduction
Previously read all hits from all files, concatenated, then made a filtered
`.copy()` of the whole multi-FEU frame. Now filters each file's hits down to the
wanted FEU ids *before* accumulating, and frees the chunk list before returning.

### Result
Memory holds steady (~43%) through the waveform step on subruns that previously
climbed to 80–95% and were killed by the watcher's memory guard (or hit the hard
`MemoryError`). Moderate runs (50–60k hits) complete and save cleanly.

### Possible future work
- Restrict `_load_hits` to only the hit branches the plots actually use
  (`arrays(filter_name=[...])`) — would further cut the hits DataFrame size.
- Downcast hit columns to `float32`/`int32` after load.

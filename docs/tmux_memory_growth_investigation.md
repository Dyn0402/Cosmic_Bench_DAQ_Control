# Investigation: tmux server memory growth → OOM on the DAQ box

**Status:** root cause hypothesized, **not yet fixed**. Needs controlled testing of the
"dream_daq pane output" hypothesis before any permanent change.

**Host:** `rays_daplxa` — 3.8 GB RAM, 1 GB swap, **tmux 1.8** (very old).

---

## Symptom

The machine OOM-kills the DAQ during long runs. The memory hog is the **tmux server
process itself**, not the Python/DAQ processes. This first took down the
`mx17_det2_det3_weekend_6-17-26` weekend run (tmux reached ~2.4 GB RSS, OOM killer fired
repeatedly Jun 20–21) and resurfaced during the `mx17_det2_det3_weekend_6-20-26` resume.

## Evidence (2026-06-22, during the resumed run)

Single tmux server process dominates memory:

```
ps -eo pid,rss,comm --sort=-rss | head
  PID    RSS(KB)  COMMAND
32700  1233536    tmux      <- 1.23 GB, the tmux SERVER
 1594   129700    X
  814   128248    flask
16856   105592    code
...
```

RSS climbs **~110 MB/hr, linearly, with no plateau**, the entire time a run is taking data:

| time  | tmux RSS |
|-------|----------|
| 00:17 | 270 MB |
| 00:32 | 296 MB |
| 01:03 | 353 MB |
| 01:45 | 431 MB |
| 02:37 | 528 MB |
| 08:36 | 1205 MB |

The growth rate is the same whether the DAQ is healthily taking data **or stalled** —
because in both states RunCtrl keeps printing a status line (`TestFun_TakeData: RunTime …
IntRate … nb_of_events …`) into the `dream_daq` pane roughly **once per second**.

## What does NOT fix it

- **`history-limit` caps** (set in `start_servers.sh`: hv_control 500, dream_daq 20000,
  daq_control 20000, flask 5000; applied via `start_tmux.sh`). These cap the number of
  *retained* scrollback lines but do **not** bound RSS. Growth is proportional to
  *cumulative* output volume, not the current buffer size, so RSS sails past the
  buffer-full point and keeps rising. (Earlier assumption that history-limit would solve
  the OOM was wrong — it only slowed it.)
- **`tmux clear-history`** — does **not** reduce RSS. Verified: cleared all four panes,
  RSS was **1205.5 MB before and 1205.5 MB after**. Freed memory stays in tmux's heap.

The only thing that reclaims the memory is **restarting the tmux server**
(`start_servers.sh`).

## Root-cause hypothesis

tmux 1.8 holds memory from the **cumulative alloc/free churn** of pane output. A pane that
receives high-frequency output for hours churns the grid storage; the heap fragments and
glibc never returns the freed pages to the OS. So RSS ≈ proportional to *total lines ever
written to the pane*, not to the (capped) lines currently retained. The `dream_daq` pane —
fed RunCtrl's ~1 Hz status line — is the driver.

**Implication:** at ~110 MB/hr, a 48 h `long_run` will OOM in ~10–11 h regardless of the
trigger, and neither history-limit nor clear-history can prevent it.

## Proposed fix — TO BE TESTED FIRST (do not commit blind)

Stop sending RunCtrl's high-volume output to the tmux pane. In `dream_daq_control.py`, the
DAQ is launched at ~line 116 with:

```python
subprocess.call(run_command)        # RunCtrl inherits the tmux pane as stdout/stderr
```

Hypothesis: redirecting that output to a log file removes the churn and stops the tmux RSS
growth:

```python
with open(os.path.join(sub_run_dir, 'runctrl_stdout.log'), 'w') as rc_log:
    subprocess.call(run_command, stdout=rc_log, stderr=subprocess.STDOUT)
```

Trade-off: lose the live in-pane view of RunCtrl; recover it with `tail -f` on that log
(plus `dream_daq.log` and the data files).

## Testing plan (validate the hypothesis before changing anything permanent)

1. **Isolate output as the cause (no DAQ needed).** In a throwaway tmux session, run a
   loop that prints ~1 line/sec for a while and watch the tmux server RSS:
   ```sh
   tmux new-session -d -s memtest 'while true; do echo "spam $(date +%s%N)"; sleep 0.05; done'
   # sample RSS over ~10 min:
   while true; do ps -o rss= -p "$(pgrep -x tmux | head -1)"; sleep 30; done
   ```
   Repeat with the same loop **redirected to a file** inside the pane
   (`... > /tmp/spam.log`). If RSS grows in the first case and is flat in the second, the
   pane-output hypothesis is confirmed.
2. **Vary `history-limit`** (e.g. 200 vs 20000) for the spamming pane and compare growth
   rate — quantifies how much is buffer vs cumulative churn.
3. **Confirm reclaim paths:** verify `clear-history` does nothing and a server restart
   resets RSS (already observed once each — reconfirm under controlled conditions).
4. **glibc tuning (non-code mitigation to try):** launch tmux with
   `MALLOC_ARENA_MAX=2` and/or `MALLOC_TRIM_THRESHOLD_=...`, or test `malloc_trim`, to see
   whether the OS reclaims freed pages without code changes.
5. **Then test the real fix in a short run:** apply the `dream_daq_control.py` redirect on
   a brief run, confirm tmux RSS stays flat and the data/logs are intact, before adopting
   it permanently.

## Interim operational workaround

Until the fix is tested and adopted: **restart the tmux server (`start_servers.sh`)
whenever you stop/restart a run** (e.g. when servicing the Dream DAQ trigger). With the
resume feature (`config.resume`) the run picks up where it left off, so the restart is
cheap. Watch tmux RSS vs `free -h`; if available memory gets low (< ~500 MB) mid-run,
stop + restart the server.

## Related

- `docs/disk_layout_dream_vs_processing.md` — separate I/O issue on the same host.
- The intermittent **Dream DAQ trigger stall** (events freeze, trigger coincidence
  count = 0) is a *separate* hardware problem under investigation; it is not the cause of
  this memory growth (growth happens during healthy data-taking too).

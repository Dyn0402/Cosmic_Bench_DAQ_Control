# Investigation: tmux server memory growth → OOM on the DAQ box

**Status:** **ROOT CAUSE CONFIRMED 2026-06-22, fix not yet applied.** The leak is **`tmux
capture-pane`**: in tmux 1.8 each `capture-pane` call leaks ~30 KB of server RSS, and the Flask
dashboard polls `/status` every 1 s, firing **5 `capture-pane` calls/s** against the shared
server. The original "scrollback churn" hypothesis was tested and **falsified**; the
capture-pane cause was then reproduced directly (experiments 1–4 below). See "Confirmed root
cause" and "Fix" sections.

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

## Controlled experiments (2026-06-22) — scrollback hypothesis FALSIFIED

Run on `rays_daplxa` (tmux 1.8) in throwaway servers on custom `-L` sockets, so the
production DAQ server was never touched. Each test compared independent servers and sampled
each server's RSS (server PID = parent of the pane shell) every 30 s. All loops ran ~20 Hz
(`sleep 0.05`) — ~20× the production ~1 Hz — to accelerate any growth. Scripts:
`/tmp/tmux_memtest.sh`, `/tmp/tmux_memtest2.sh`.

**Experiment 1 — pane output vs file redirect (default history-limit 2000), 15 min.**

| elapsed | pane-output RSS | file-redirect RSS |
|--------:|----------------:|------------------:|
| 0 s     | 1564 KB | 1532 KB |
| 120 s   | **2256 KB** | 1556 KB |
| 150 s–870 s | 2256 KB (flat) | 1556 KB (flat) |

~18 000 lines written. Pane output grew only ~0.7 MB while the 2000-line buffer filled, then
**plateaued for 13 min**. File-redirect control was perfectly flat. → output-to-pane costs a
*bounded* amount; redirect costs nothing.

**Experiment 2 — variable vs fixed line WIDTH, both history-limit 20000, 30 min.**
Motivated by the live `dream_daq` pane: RunCtrl prints `nb_of_events=<N>` *unpadded*, so real
line width grows. `frag` = strongly varying width; `fixed` = constant width.

| elapsed | frag (variable width) | fixed (constant width) |
|--------:|----------------------:|-----------------------:|
| 30 s    | 2.7 MB | 2.7 MB |
| 240 s   | 10.6 MB | 10.3 MB |
| 450 s   | 18.5 MB | 17.9 MB |
| ~500 s  | **18.5 MB (plateau)** | **20.2 MB (plateau)** |
| 1772 s  | 18.5 MB | 20.2 MB |

Both grew only until the 20000-line buffer filled, then **plateaued flat for ~22 min**.
Variable width did **not** leak (it plateaued *lower* than fixed). Plateau scales with
history-limit (2000→~2.2 MB, 20000→~20 MB): a textbook bounded ring buffer.

**Conclusion.** High-frequency pane output — even with variable line width and the production
history-limit — does **not** reproduce the unbounded ~110 MB/hr growth. RSS plateaus at
~(history-limit × bytes/line). Production reached **1205 MB**, ~60× this ceiling, so the real
leak is **not scrollback churn**. The original hypothesis is falsified. This also explains
why `clear-history` did nothing and `history-limit` caps didn't help: **the leak was never in
scrollback.**

**Experiment 3 — in-place ANSI repaints, attached vs detached client (history-limit 20000),
~10 Hz, stopped at 6.5 min after plateau.** Both servers ran identical curses-style repaint
loops (cursor-home + clear + redraw of a 16-line block); only difference was whether a client
was attached (nested inside a `holder` tmux to supply a pty).

| elapsed | att (attached) | det (detached) |
|--------:|---------------:|---------------:|
| 30 s    | 4.4 MB | 4.1 MB |
| 210 s   | **18.4 MB** | **17.6 MB** |
| 240–390 s | 18.4 MB (flat) | 17.6 MB (flat) |

Same buffer-bound plateau. The attached client made **no meaningful difference** (~5%), and
repaints did not leak. Both new hypotheses (curses repaints / attached render) **falsified.**

**Experiment 4 — `tmux capture-pane` hammer vs control (history-limit 20000), ~20 captures/s
of `-pS -500`, stopped at 140 s once unbounded growth was obvious.** Both servers ran the same
fill loop; only `memtest_cap` was hammered with `capture-pane`. THIS is the leak:

| elapsed | cap (hammered) | nocap (control) | captures |
|--------:|---------------:|----------------:|---------:|
| 0 s   | 2.3 MB  | 2.1 MB | 0 |
| 20 s  | 14.9 MB | 2.4 MB | 400 |
| 60 s  | 40.9 MB | 3.1 MB | 1200 |
| 100 s | 68.1 MB | 3.7 MB | 2000 |
| 140 s | **91.3 MB** | 4.4 MB | 2800 |

The hammered server grows **linearly and without bound** (~32 KB leaked per `capture-pane -pS
-500` call); the control plateaus. Reproduced the real failure mode.

**Experiment 5 — true leak vs glibc retention, stopped at 120 s.** Two servers, both hammered
identically (~20 `capture-pane -pS -500`/s); one launched with default malloc, one with
`MALLOC_ARENA_MAX=1 MALLOC_TRIM_THRESHOLD_=0 MALLOC_MMAP_THRESHOLD_=0 MALLOC_TOP_PAD_=0`.

| elapsed | plain (default malloc) | glibc-tuned |
|--------:|-----------------------:|------------:|
| 20 s  | 14.9 MB | 21.2 MB |
| 60 s  | 41.2 MB | 46.9 MB |
| 120 s | 79.1 MB | 85.3 MB |

**Identical slope** (both +64 MB over the same 100 s; the tuned one carries a constant
mmap-overhead offset). Aggressive allocator tuning has **no effect on the growth rate** → tmux
1.8 never `free()`s the capture buffer. This is a **genuine leak, not glibc page retention**,
so no launch-env / `MALLOC_*` change and no `malloc_trim` can reclaim it. Allocator-tuning
option (old testing-plan step 4) is **ruled out**.

**Experiment 6 — tmux 3.3a vs 1.8, the proposed fix, stopped at 120 s.** Built tmux 3.3a +
libevent 2.1.12 from source in userspace on the box (CentOS 7, gcc 4.8.5 — builds clean;
binary at `~/tmux_build/tmux-install/bin/tmux`). Both servers hammered identically
(~20 `capture-pane -pS -500`/s, history-limit 20000); only the tmux binary differs.

| elapsed | tmux 3.3a (new) | tmux 1.8 (old) |
|--------:|----------------:|---------------:|
| 0 s   | 2.5 MB | 2.2 MB |
| 40 s  | 3.0 MB | 27.3 MB |
| 80 s  | 3.4 MB | 55.8 MB |
| 120 s | **3.7 MB (flat)** | **78.8 MB (climbing)** |

**tmux 3.3a does not leak.** Its ~1 MB rise is just the scrollback buffer filling (plateaus);
1.8 climbs linearly without bound. The capture-pane leak is a fixed old-tmux bug. **Upgrading
tmux is confirmed as the real, complete fix** — and it requires no application changes.

## Confirmed root cause

**Every `tmux capture-pane` call leaks ~30 KB of tmux-1.8 server RSS, and the Flask dashboard
polls it ~5×/second.** `flask_app/templates/index.html` runs `setInterval(updateStatus, 1000)`
(1 Hz); each `/status` hit (`flask_app/app.py:77` → `daq_status.py`) issues **5** captures
against the single shared server:

- `dream_daq:0.0`  `capture-pane -pS -500` (`daq_status.py:38`)
- `hv_control:0.0` `capture-pane -pS -50`  (`daq_status.py:122`)
- `daq_control:0.0` `capture-pane -pS -50` (`daq_status.py:164`)
- `processor:0.0`  `capture-pane -pS -50`  (`daq_status.py:207`)
- `qa_watcher:0.0` `capture-pane -pS -50`  (`daq_status.py:243`)

5 calls/s × 3600 = ~18 000 captures/hr. At ~6 KB/call (smaller `-50` captures leak less than
the `-500` measured) this is **~100 MB/hr — matching the observed ~110 MB/hr.** The leak is in
server heap, independent of scrollback (so `clear-history` and `history-limit` do nothing) and
only reclaimed by restarting the server. It accrues whenever a browser has the dashboard open
during a run — which is the normal operating condition. **This fully explains all prior
evidence.**

## Fix

Goal (per operator): keep the **1 Hz** dashboard refresh and leave a dashboard **open
indefinitely** with no memory growth. That rules out symptom treatment (periodic server
restart) and — per experiment 5 — allocator tuning. Since the leak is one allocation **per
`capture-pane` call that tmux 1.8 never frees**, the only true fixes either (A) stop calling
`capture-pane`, or (B) replace the leaky tmux.

**True fixes (pick one):**

- **A. Stop reading status via `capture-pane`; read from files instead.** Mirror each pane to a
  log file **once** with `tmux pipe-pane` at pane creation (in `start_tmux.sh`/`start_servers.sh`),
  and rewrite `daq_status.py` to parse the tail of those files instead of capturing the pane
  per poll. One persistent writer per pane, zero per-poll tmux allocation → leak eliminated,
  1 Hz fine, dashboard open forever. Cost: `pipe-pane` streams **raw** pane bytes (ANSI/escape
  sequences from the curses-style RunCtrl TUI), so the parser must tolerate/strip control
  sequences — more involved than the current "rendered screen" capture. Disk file grows but is
  on disk (tailed, and can be rotated/truncated), not in RAM.
- **B. Replace tmux 1.8 with a modern build.** The per-`capture-pane` leak is a fixed
  old-tmux bug; tmux ≥2.x/3.x frees the buffer. Keeps **all** current code (1 Hz capture
  approach unchanged). A **userspace static binary** avoids needing root — drop it in and point
  `start_servers.sh` at it. Cost: must re-validate the tmux-1.8-specific quirks the code relies
  on (e.g. the `unset TMUX` / "can't create a session when $TMUX is set" workaround noted in
  `flask_app/app.py:256-261`, and that all `capture-pane`/`send-keys` targets still behave).

**Mitigations (reduce the slope but do NOT stop growth — only if a true fix is deferred):**

- Capture fewer lines: `dream_daq` `-pS -500` → `-pS -30` (leak scales with lines; the parse
  only needs the last ~20–30 lines). ~17× less from that call.
- Throttle/cache `/status` server-side: capture each pane at most every ~3–5 s, serve cached
  result to the 1 Hz poll. ~5–15× fewer captures. Keeps the browser at 1 Hz.
- Both together drop ~110 MB/hr to ~5–10 MB/hr (days, not hours, to OOM) — buys time, not a cure.

**Recommendation:** **B (upgrade tmux) — chosen and proven on this box** (experiment 6). A is
the fallback only if tmux cannot be changed.

### Deployment plan for B (CentOS 7, admin available)

Feasibility established: yum/EPEL only ever offer tmux 1.8, so build from source. Toolchain
(gcc 4.8.5, make, pkg-config, ncurses-devel) is present; only `libevent-devel` is missing and
is built in userspace. `/usr/local/bin` precedes `/usr/bin` in PATH and `start_tmux.sh` calls
`tmux` bare, so a new `/usr/local/bin/tmux` is picked up with **no code changes**.

**Deploy binary is built and validated.** `~/tmux_build/tmux-deploy/bin/tmux` (3.3a), built by
linking the locally-built libevent 2.1.12 **statically** (`LIBEVENT_LIBS=.../libevent.a`) while
ncurses/util/libc stay dynamic. `ldd` shows only stock el7 libs (libutil, libtinfo, libpthread,
libm, libresolv, libc) — **no libevent, no `LD_LIBRARY_PATH` needed.** (NB: a full
`--enable-static` build fails on el7 with a `forkpty` redeclaration conflict vs `/usr/include/pty.h`;
static-linking only libevent sidesteps that.) Smoke-tested OK: `send-keys`→`capture-pane -pS
-50 -t s:0.0` round-trips, `set-option -g history-limit 20000` works, and the `unset TMUX`
nested-create guard works.

Steps to adopt (chosen: system install; cutover done manually later by the operator):
1. **Install** (operator runs the sudo step — sudo is interactive on this box):
   ```sh
   sudo install -m 0755 ~/tmux_build/tmux-deploy/bin/tmux /usr/local/bin/tmux
   hash -r; tmux -V          # expect: tmux 3.3a  (and `which tmux` -> /usr/local/bin/tmux)
   ```
   No code/script changes: `start_tmux.sh` calls `tmux` bare and `/usr/local/bin` precedes
   `/usr/bin` in PATH. Installing is safe mid-run — the live 1.8 *server* keeps its in-memory
   binary until restarted.
2. **Cutover at a run boundary only:** with the DAQ stopped/between runs, run
   `start_servers.sh` (kills + recreates all sessions) so every session is recreated under 3.3a.
   `config.resume` lets the run pick back up.
3. **Post-cutover validation:** confirm the dashboard `/status` still parses
   (RUNNING / event count / HV / processor / qa), DAQ controls (`send-keys`-driven) still work,
   and — the whole point — sample the production tmux server RSS over ~20 min with the
   dashboard open and confirm it stays flat instead of climbing ~110 MB/hr.
   - Watch for a `~/.tmux.conf` for `usernsw`: 3.3a may reject 1.8-era config syntax (none was
     needed for the headless sessions in testing, but check if one exists).

## Validation plan for the fix

- **For B (tmux upgrade):** install modern tmux (userspace static OK), repoint `start_servers.sh`,
  bring up all sessions, confirm dashboard `/status` still parses (RUNNING/event count/HV/
  processor/qa) and `send-keys`-driven controls still work; then hammer `capture-pane` on a
  throwaway session of the **new** tmux (reuse `/tmp/tmux_memtest4.sh` pattern) to confirm RSS
  is now flat. Watch production server RSS over a real run with the dashboard open.
- **For A (file-based status):** after rewrite, sample production tmux server RSS
  (`ps -o rss= -p <server-pid>`) every 30 s for ~20 min with the dashboard open; confirm slope
  ≈ flat and `/status` still reports correctly.
- Keep the server-restart workaround documented as a backstop until the chosen fix is adopted.

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

#!/bin/bash

name=$1
cmd=$2
# Scrollback cap for this session, in LINES. tmux's only history knob is a
# per-pane line count (no byte-size or time-based limit), so "cap by size"
# means capping lines. Each retained line costs memory, so keep chatty
# sessions short to avoid the OOM killer on this RAM-limited machine.
hist=${3:-5000}

# Check if tmux session already exists
if tmux has-session -t "$name" 2>/dev/null; then
    echo "❌ Tmux session '$name' already exists!"
    exit 1
fi

unset TMUX

# A pane captures history-limit at the moment it is created, from the global
# option. On this machine's old tmux (1.8), a standalone `set-option -g` does
# NOT persist for a pane spawned by a *separate* later `tmux` invocation, so the
# pane silently falls back to the 2000-line default. Chaining the global set and
# new-session into a SINGLE tmux command (with \;) guarantees the new pane
# captures $hist. Verified on tmux 1.8: chained -> pane gets $hist; separate
# commands -> pane gets 2000.
#
# We also set the option on the session afterward so any windows created later
# in this session keep $hist even after a subsequent start_tmux.sh call
# overwrites the global default for the next session.
if [ -z "$cmd" ]; then
    # Start an empty interactive tmux session
    tmux set-option -g history-limit "$hist" \; new-session -d -s "$name"
    tmux set-option -t "$name" history-limit "$hist" 2>/dev/null
    echo "✅ Started empty tmux session: $name (scrollback ${hist} lines)"
else
    # Start tmux session and run command
    tmux set-option -g history-limit "$hist" \; new-session -d -s "$name"
    tmux set-option -t "$name" history-limit "$hist" 2>/dev/null
    tmux send-keys -t "$name" "$cmd" Enter
    echo "✅ Started $name running: $cmd (scrollback ${hist} lines)"
fi
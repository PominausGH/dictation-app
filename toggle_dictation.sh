#!/bin/bash
# Toggle dictation on/off
# Assign this script to a keyboard shortcut (e.g., Super+D)

PID_FILE="/tmp/dictation.pid"
STATE_FILE="/tmp/dictation_state"
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PYTHON="$SCRIPT_DIR/venv/bin/python"

# Check if daemon is running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        # Daemon running - send SIGUSR1 to toggle
        kill -SIGUSR1 "$PID"
        exit 0
    fi
fi

# Daemon not running - start it
cd "$SCRIPT_DIR"
nohup "$PYTHON" dictation_daemon.py > /tmp/dictation.log 2>&1 &

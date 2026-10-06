#!/bin/bash
# Launch i3-master-layout daemon — wait for i3 IPC to be ready

# Kill any old instance
pkill -f i3-master-layout 2>/dev/null || true
sleep 0.5

# Wait for i3 IPC socket to be available (up to 10 seconds)
for i in $(seq 1 20); do
    if i3-msg -t get_version >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

# Give i3 a bit more time to settle after reload
sleep 1

# Launch daemon
setsid python3 "$HOME/.config/i3/scripts/i3-master-layout.py" \
    > /tmp/master.log 2>&1 < /dev/null &
disown

# Verify it stays alive
sleep 2
if ! pgrep -f i3-master-layout >/dev/null; then
    # Try once more
    sleep 2
    setsid python3 "$HOME/.config/i3/scripts/i3-master-layout.py" \
        > /tmp/master.log 2>&1 < /dev/null &
    disown
fi

#!/bin/bash
# Launch Cava in floating window — forced via i3 IPC by window ID

# Kill old
pkill -x cava 2>/dev/null
sleep 0.3

# Launch Cava
cava -p "$HOME/.config/cava/config" >/dev/null 2>&1 &
CAVA_PID=$!

# Wait for its window to appear (poll up to 5s)
WID=""
for i in $(seq 1 25); do
    WID=$(xdotool search --pid "$CAVA_PID" 2>/dev/null | head -1)
    [ -z "$WID" ] && WID=$(xdotool search --class cava 2>/dev/null | head -1)
    [ -n "$WID" ] && break
    sleep 0.2
done

if [ -z "$WID" ]; then
    echo "Cava window not found" >&2
    exit 1
fi

# Force floating via i3 IPC (con_id = xdotool WID works)
i3-msg "[id=$WID] floating enable" >/dev/null
i3-msg "[id=$WID] resize set 600 150" >/dev/null
i3-msg "[id=$WID] move position center" >/dev/null

wait $CAVA_PID

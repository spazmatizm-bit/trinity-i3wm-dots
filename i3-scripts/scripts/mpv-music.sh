#!/bin/bash
# Launch mpv with IPC socket for localmusapp control
SOCKET="/tmp/mpv-music.sock"
PLAYLIST="${1:-$HOME/Music}"

# Kill old mpv if running
if [ -S "$SOCKET" ]; then
    echo '{"command": ["quit"]}' | socat - UNIX-CONNECT:"$SOCKET" 2>/dev/null
    sleep 0.5
fi
pkill -f "mpv.*--input-ipc-server" 2>/dev/null
rm -f "$SOCKET"

# If argument is a directory, play everything inside
if [ -d "$PLAYLIST" ]; then
    exec mpv --shuffle --no-video \
        --input-ipc-server="$SOCKET" \
        --idle=yes \
        --force-window=no \
        "$PLAYLIST"
else
    exec mpv --shuffle --no-video \
        --input-ipc-server="$SOCKET" \
        --idle=yes \
        --force-window=no \
        "$PLAYLIST"
fi

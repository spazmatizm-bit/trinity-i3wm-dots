#!/bin/bash
# Control script for mpv via IPC socket
MPV_SOCKET="/tmp/mpv-music.sock"

# If no mpv running, launch the picker
if [ ! -S "$MPV_SOCKET" ]; then
    exec ~/.config/polybar/scripts/playlist-picker.sh
fi

# Check mpv is actually alive
if ! echo '{"command":["get_property","pause"]}' | socat - UNIX-CONNECT:"$MPV_SOCKET" >/dev/null 2>&1; then
    rm -f "$MPV_SOCKET"
    exec ~/.config/polybar/scripts/playlist-picker.sh
fi

case "$1" in
    toggle) echo 'cycle pause' | socat - UNIX-CONNECT:"$MPV_SOCKET" ;;
    next)   echo 'playlist-next' | socat - UNIX-CONNECT:"$MPV_SOCKET" ;;
    prev)   echo 'playlist-prev' | socat - UNIX-CONNECT:"$MPV_SOCKET" ;;
    stop)   echo 'quit' | socat - UNIX-CONNECT:"$MPV_SOCKET" ;;
esac

#!/bin/bash
# Shows current track or playback state
MPV_SOCKET="/tmp/mpv-music.sock"

if [ ! -S "$MPV_SOCKET" ]; then
    echo ""
    exit 0
fi

# Get paused state and title
PAUSED=$(echo '{"command":["get_property","pause"]}' | socat - UNIX-CONNECT:"$MPV_SOCKET" 2>/dev/null | grep -oP '"data":\K(true|false)')
TITLE=$(echo '{"command":["get_property","media-title"]}' | socat - UNIX-CONNECT:"$MPV_SOCKET" 2>/dev/null | grep -oP '"data":"\K[^"]+')

[ -z "$TITLE" ] && { echo ""; exit 0; }

# Truncate
[ ${#TITLE} -gt 30 ] && TITLE="${TITLE:0:27}..."

if [ "$PAUSED" = "true" ]; then
    echo " $TITLE"
else
    echo " $TITLE"
fi

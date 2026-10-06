#!/bin/bash
if pgrep -f music-control.py >/dev/null; then
    pkill -f music-control.py
else
    setsid python3 ~/music-control/music-control.py >/dev/null 2>&1 &
fi

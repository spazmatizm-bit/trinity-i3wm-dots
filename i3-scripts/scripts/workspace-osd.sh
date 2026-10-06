#!/bin/bash
# Show workspace number as OSD
WS="$1"
[ -z "$WS" ] && exit 0
dunstify -a "workspace" -u low -t 800 \
    -h string:x-dunst-stack-tag:workspace \
    "Workspace $WS"

#!/bin/bash
# Brightness control with Dunst OSD
STEP=10
msgTag="brightness"

BRIGHT=$(brightnessctl g 2>/dev/null || echo 0)
MAX=$(brightnessctl m 2>/dev/null || echo 100)

case "$1" in
    up)   brightnessctl set +${STEP}% >/dev/null 2>&1 ;;
    down) brightnessctl set ${STEP}%- >/dev/null 2>&1 ;;
esac

BRIGHT=$(brightnessctl g 2>/dev/null || echo 0)
MAX=$(brightnessctl m 2>/dev/null || echo 100)
PCT=$(( BRIGHT * 100 / MAX ))

dunstify -a "brightness" -u low -i display-brightness -h string:x-dunst-stack-tag:$msgTag -h int:value:"$PCT" "Brightness: ${PCT}%"

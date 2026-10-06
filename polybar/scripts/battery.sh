#!/bin/bash
cap=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || echo "100")
stat=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null || echo "Unknown")
if [ "$cap" -lt 30 ] || [ "$stat" = "Charging" ]; then
    printf "  %s%%\n" "$cap"
fi

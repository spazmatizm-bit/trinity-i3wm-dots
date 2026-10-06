#!/bin/bash
# Toggle a floating scratchpad terminal
if ! i3-msg -t get_tree | grep -q "__i3_scratch.*scratchpad-term"; then
    i3-msg "exec --no-startup-id kitty --name scratchpad-term" >/dev/null
    sleep 0.3
    i3-msg "[instance=\"scratchpad-term\"] floating enable, resize set 900 600, move position center, move scratchpad" >/dev/null
fi
i3-msg "scratchpad show" >/dev/null

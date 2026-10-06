#!/bin/bash
# Polybar custom script — i3 workspaces as fixed-width squares.

# Nord palette
FG="#eceff4"
FG_DIM="#6c7086"
FG_FOCUSED="#2e3440"
BG_FOCUSED="#88c0d0"
BG_VISIBLE="#4c566a"
BG_HIDDEN="#3b4252"
BG_URGENT="#bf616a"

i3-msg -t get_workspaces \
| jq -r 'sort_by(.num)[] | "\(.name)|\(.focused)|\(.visible)|\(.urgent)"' \
| while IFS='|' read -r name focused visible urgent; do
    if [ "$urgent" = "true" ]; then
        fg="$FG"; bg="$BG_URGENT"
    elif [ "$focused" = "true" ]; then
        fg="$FG_FOCUSED"; bg="$BG_FOCUSED"
    elif [ "$visible" = "true" ]; then
        fg="$FG"; bg="$BG_VISIBLE"
    else
        fg="$FG_DIM"; bg="$BG_HIDDEN"
    fi
    # %{A1:...:} wraps the square in a click handler -> switch workspace
    printf '%%{A1:i3-msg workspace %s:}%%{F%s}%%{B%s}  %s  %%{B-}%%{F-}%%{A} ' \
        "$name" "$fg" "$bg" "$name"
done

#!/bin/bash
# Full screenshot → file + clipboard

DIR="$HOME/Pictures/Screenshots"
mkdir -p "$DIR"
FILE="$DIR/$(date +%Y-%m-%d_%H-%M-%S).png"

# Capture full screen
maim "$FILE"

# Copy to clipboard
xclip -selection clipboard -t image/png -i "$FILE"

# Notification
if command -v dunstify >/dev/null; then
    dunstify -a "screenshot" -u low -i "$FILE" "Screenshot saved & copied"
else
    notify-send "Screenshot saved & copied" "$FILE"
fi

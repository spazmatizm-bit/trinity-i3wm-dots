#!/bin/bash
# Region screenshot → clipboard + file
DIR="$HOME/Pictures/Screenshots"
mkdir -p "$DIR"
FILE="$DIR/$(date +%Y-%m-%d_%H-%M-%S).png"

# Capture region with Spectacle in background mode
spectacle -b -r -n -o "$FILE"

# Copy to clipboard (needs xclip)
if [ -f "$FILE" ]; then
    xclip -selection clipboard -t image/png -i "$FILE"
    dunstify -a "screenshot" -u low -i "$FILE" "Screenshot saved & copied"
fi

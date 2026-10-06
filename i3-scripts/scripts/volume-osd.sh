#!/bin/bash
# Volume control with Dunst OSD
STEP=5
msgTag="volume"

VOL=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\d+(?=%)' | head -1)
MUTE=$(pactl get-sink-mute @DEFAULT_SINK@ | grep -oP '(?<=: )\w+')

case "$1" in
    up)   pactl set-sink-volume @DEFAULT_SINK@ +${STEP}% ;;
    down) pactl set-sink-volume @DEFAULT_SINK@ -${STEP}% ;;
    mute) pactl set-sink-mute @DEFAULT_SINK@ toggle ;;
esac

VOL=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\d+(?=%)' | head -1)
MUTE=$(pactl get-sink-mute @DEFAULT_SINK@ | grep -oP '(?<=: )\w+')

if [ "$MUTE" = "yes" ]; then
    dunstify -a "volume" -u low -i audio-volume-muted -h string:x-dunst-stack-tag:$msgTag "Muted"
else
    dunstify -a "volume" -u low -i audio-volume-high -h string:x-dunst-stack-tag:$msgTag -h int:value:"$VOL" "Volume: ${VOL}%"
fi

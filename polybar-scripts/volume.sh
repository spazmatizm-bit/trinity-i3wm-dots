#!/bin/bash
msgTag="volume"
VOL=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\d+(?=%)' | head -1)
MUTE=$(pactl get-sink-mute @DEFAULT_SINK@ | grep -oP '(?<=: )\w+')

case "$1" in
    up)   pactl set-sink-volume @DEFAULT_SINK@ +5% ;;
    down) pactl set-sink-volume @DEFAULT_SINK@ -5% ;;
    mute) pactl set-sink-mute @DEFAULT_SINK@ toggle ;;
esac

VOL=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\d+(?=%)' | head -1)
MUTE=$(pactl get-sink-mute @DEFAULT_SINK@ | grep -oP '(?<=: )\w+')

if [ "$MUTE" = "yes" ]; then
    dunstify -a "volume" -u low -i audio-volume-muted -h string:x-dunst-stack-tag:$msgTag "Volume muted"
else
    dunstify -a "volume" -u low -i audio-volume-high -h string:x-dunst-stack-tag:$msgTag -h int:value:"$VOL" "Volume: ${VOL}%"
fi

#!/bin/bash
# Rofi-based playlist picker, launches mpv
MUSIC_DIR="$HOME/Music"
MPV_SOCKET="/tmp/mpv-music.sock"

# Find all directories under ~/Music that contain audio files
PLAYLISTS=$(find "$MUSIC_DIR" -type f \( -name "*.mp3" -o -name "*.flac" -o -name "*.m4a" -o -name "*.opus" -o -name "*.ogg" \) \
    | sed "s|$MUSIC_DIR/||" \
    | awk -F/ '{print $1"/"$2}' \
    | sort -u)

[ -z "$PLAYLISTS" ] && { notify-send "Playlist" "No music found in ~/Music"; exit 1; }

CHOSEN=$(echo "$PLAYLISTS" | rofi -dmenu -i -p "Playlist" -theme-str 'window {width: 30%;}')

[ -z "$CHOSEN" ] && exit 0

# Kill old mpv if running
if [ -S "/tmp/mpv-music.sock" ]; then
    echo '{"command": ["quit"]}' | socat - UNIX-CONNECT:/tmp/mpv-music.sock 2>/dev/null
fi
pkill -f "mpv.*--input-ipc-server" 2>/dev/null
sleep 0.5
rm -f /tmp/mpv-music.sock

# Launch mpv with IPC socket
mpv --shuffle --no-video \
    --input-ipc-server=/tmp/mpv-music.sock \
    --idle=yes \
    "$MUSIC_DIR/$CHOSEN" >/dev/null 2>&1 &



notify-send -a "music" "Playing" "$CHOSEN"

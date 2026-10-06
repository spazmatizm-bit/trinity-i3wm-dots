#!/bin/bash
# Trinity main menu — all actions in one place
ROFI_THEME='window {width: 30%;}'

CHOICE=$(echo " Apps
 Windows
 Files
 Screenshots
 Wallpapers
 Themes
 Presets
 Power Menu
 Settings
 Cheatsheet
 System Info
 Logout" | rofi -dmenu -i -p Trinity -theme-str "$ROFI_THEME")

[ -z "$CHOICE" ] && exit 0

# Strip leading spaces
CHOICE="${CHOICE# }"

case "$CHOICE" in
    "Apps")
        exec rofi -show drun
        ;;
    "Windows")
        exec rofi -show window
        ;;
    "Files")
        exec rofi -show filebrowser -filebrowser-command "xdg-open" -filebrowser-dir "$HOME"
        ;;
    "Screenshots")
        SUB=$(echo "Region
Full Screen
Active Window" | rofi -dmenu -i -p Screenshot)
        [ -z "$SUB" ] && exit 0
        case "$SUB" in
            Region)        exec ~/.config/i3/scripts/fullshot.sh -r ;;
            "Full Screen") exec ~/.config/i3/scripts/fullshot.sh ;;
            "Active Window") exec ~/.config/i3/scripts/fullshot.sh -w ;;
        esac
        ;;
    "Wallpapers")
        WALLS=$(ls ~/Pictures/wallpapers/*.png ~/Pictures/wallpapers/*.jpg 2>/dev/null | xargs -n1 basename 2>/dev/null)
        [ -z "$WALLS" ] && { dunstify "No wallpapers found"; exit 0; }
        W=$(echo "$WALLS" | rofi -dmenu -i -p Wallpaper -theme-str "$ROFI_THEME")
        [ -n "$W" ] && feh --bg-scale "$HOME/Pictures/wallpapers/$W"
        ;;
    "Themes")
        THEMES=$(python3 -c "import json; print('\n'.join(json.load(open('$HOME/dotfiles/themes/themes.json')).keys()))" 2>/dev/null)
        [ -z "$THEMES" ] && { dunstify "No themes found"; exit 0; }
        T=$(echo "$THEMES" | rofi -dmenu -i -p Theme -theme-str "$ROFI_THEME")
        [ -n "$T" ] && ~/.config/i3/scripts/theme-switch.sh "$T"
        ;;
    "Presets")
        SUB=$(echo "Minimal
Standard
Maximal" | rofi -dmenu -i -p Preset)
        [ -z "$SUB" ] && exit 0
        python3 - "$SUB" << 'PYEOF'
import sys, os, re
preset = sys.argv[1].lower()
conf = os.path.expanduser("~/.config/i3/config")
src = open(conf).read()
if preset == "minimal":
    src = re.sub(r'^gaps inner \d+', 'gaps inner 0', src, flags=re.M)
    src = re.sub(r'^gaps outer \d+', 'gaps outer 0', src, flags=re.M)
    src = re.sub(r'^default_border .*', 'default_border pixel 1', src, flags=re.M)
elif preset == "standard":
    src = re.sub(r'^gaps inner \d+', 'gaps inner 8', src, flags=re.M)
    src = re.sub(r'^gaps outer \d+', 'gaps outer 4', src, flags=re.M)
    src = re.sub(r'^default_border .*', 'default_border pixel 2', src, flags=re.M)
elif preset == "maximal":
    src = re.sub(r'^gaps inner \d+', 'gaps inner 12', src, flags=re.M)
    src = re.sub(r'^gaps outer \d+', 'gaps outer 8', src, flags=re.M)
    src = re.sub(r'^default_border .*', 'default_border pixel 3', src, flags=re.M)
open(conf, "w").write(src)
PYEOF
        i3-msg reload
        dunstify "Preset: $SUB"
        ;;
    "Power Menu")
        exec ~/.config/i3/scripts/powermenu.sh
        ;;
    "Settings")
        exec python3 "$HOME/Documents/trinity-settings/settings.py"
        ;;
    "Cheatsheet")
        exec kitty --class cheatsheet -e ~/.config/i3/scripts/cheatsheet.sh
        ;;
    "System Info")
        exec kitty --hold -e fastfetch
        ;;
    "Logout")
        i3-msg exit
        ;;
esac

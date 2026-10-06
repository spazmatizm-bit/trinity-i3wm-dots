#!/bin/bash
THEMES_FILE="$HOME/dotfiles/themes/themes.json"
CHOICES=$(python3 -c "import json; print('\n'.join(json.load(open('$THEMES_FILE')).keys()))")
CHOSEN=$(echo "$CHOICES" | rofi -dmenu -i -p "Theme")
[ -z "$CHOSEN" ] && exit 0
"$HOME/.config/i3/scripts/theme-switch.sh" "$CHOSEN"

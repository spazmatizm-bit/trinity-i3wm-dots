#!/bin/bash
# Show theme change with notification
THEME="$1"
[ -z "$THEME" ] && exit 0

python3 - "$THEME" << 'PYEOF'
import json, sys, subprocess, os

theme_name = sys.argv[1]
theme_file = os.path.expanduser("~/dotfiles/themes/themes.json")
try:
    themes = json.load(open(theme_file))
    t = themes.get(theme_name, {})
except:
    t = {}

bg = t.get("bg", "#2e3440")
blue = t.get("blue", "#88c0d0")
red = t.get("red", "#bf616a")
green = t.get("green", "#a3be8c")
yellow = t.get("yellow", "#ebcb8b")
name = t.get("name", theme_name)

# Create a 5-color palette preview image
from PIL import Image, ImageDraw
img = Image.new("RGB", (250, 50), bg)
draw = ImageDraw.Draw(img)
colors = [bg, blue, green, yellow, red]
for i, c in enumerate(colors):
    draw.rectangle([i*50, 0, (i+1)*50, 50], fill=c)
path = "/tmp/theme-preview.png"
img.save(path)

subprocess.run(["dunstify", "-a", "theme", "-u", "low",
                "-i", path,
                "-h", "string:x-dunst-stack-tag:theme",
                f"Theme: {name}", theme_name])
PYEOF

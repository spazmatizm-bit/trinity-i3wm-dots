#!/usr/bin/env python3
"""Generate a theme from an image."""
import sys, os, json, shutil, subprocess
from pathlib import Path
from colorthief import ColorThief

THEMES_FILE = Path.home() / "dotfiles/themes/themes.json"
WALL_DIR = Path.home() / "Pictures/wallpapers"
THEME_SWITCH = Path.home() / ".config/i3/scripts/theme-switch.sh"


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def lighten(h, f=0.3):
    r, g, b = int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(
        min(255, int(r + (255-r)*f)),
        min(255, int(g + (255-g)*f)),
        min(255, int(b + (255-b)*f))
    )


def darken(h, f=0.5):
    r, g, b = int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(int(r*f), int(g*f), int(b*f))


def lum(h):
    r, g, b = int(h[1:3],16)/255, int(h[3:5],16)/255, int(h[5:7],16)/255
    return 0.2126*r + 0.7152*g + 0.0722*b


def sat(c):
    r, g, b = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
    mx, mn = max(r,g,b), min(r,g,b)
    return 0 if mx == 0 else (mx-mn)/mx


def generate(image_path):
    ct = ColorThief(image_path)
    palette = [rgb_to_hex(c) for c in ct.get_palette(color_count=8, quality=10)]
    sorted_p = sorted(palette, key=lum)

    bg = sorted_p[0]
    fg = sorted_p[-1]
    fg_alt = lighten(bg, 0.4)
    blue_dim = darken(bg, 1.3)

    mids = sorted_p[1:-1] if len(sorted_p) > 2 else sorted_p
    accent = max(mids, key=sat) if mids else lighten(bg, 0.5)

    red = "#c06060"
    green = "#80b080"
    yellow = "#d0c080"

    for c in mids:
        r, g, b = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
        if r > g and r > b and (r - min(g,b)) > 40:
            red = c
        if g > r and g > b and (g - min(r,b)) > 20:
            green = c
        if r > 150 and g > 150 and b < 120:
            yellow = c

    return {
        "name": "Custom",
        "bg": bg, "fg": fg, "fg_alt": fg_alt,
        "blue": accent, "blue_dim": blue_dim,
        "red": red, "green": green, "yellow": yellow,
        "cyan": lighten(accent, 0.3),
        "accent": accent,
        "wallpaper": "custom.png",
        "picom_bg_opacity": "0.95",
        "gradient_color_1": bg,
        "gradient_color_2": blue_dim,
        "gradient_color_3": lighten(accent, 0.2),
        "gradient_color_4": lighten(accent, 0.5),
    }


def main():
    if len(sys.argv) < 2:
        files = sorted(WALL_DIR.glob("*"))
        files = [f for f in files if f.suffix.lower() in (".png",".jpg",".jpeg")]
        if not files:
            print("No images in " + str(WALL_DIR))
            sys.exit(1)
        try:
            chosen = subprocess.check_output(
                ["rofi", "-dmenu", "-i", "-p", "Image"],
                input="\n".join(f.name for f in files), text=True
            ).strip()
        except Exception:
            sys.exit(0)
        if not chosen:
            sys.exit(0)
        image_path = str(WALL_DIR / chosen)
    else:
        image_path = os.path.expanduser(sys.argv[1])

    if not os.path.exists(image_path):
        print("ERROR: not found: " + image_path)
        sys.exit(1)

    print("==> Analyzing: " + image_path)
    theme = generate(image_path)

    for k in ("bg","fg","fg_alt","blue","blue_dim","red","green","yellow","cyan"):
        print("     " + k.ljust(10) + " " + theme[k])

    dest = WALL_DIR / "custom.png"
    shutil.copy(image_path, dest)
    print("   Wallpaper: " + str(dest))

    themes = json.loads(THEMES_FILE.read_text()) if THEMES_FILE.exists() else {}
    themes["custom"] = theme
    THEMES_FILE.write_text(json.dumps(themes, indent=2))
    print("   Saved as 'custom'")

    print("==> Applying...")
    subprocess.run(["bash", str(THEME_SWITCH), "custom"])


if __name__ == "__main__":
    main()

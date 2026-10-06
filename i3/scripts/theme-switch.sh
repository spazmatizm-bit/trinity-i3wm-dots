#!/usr/bin/env python3
"""Theme switcher for Trinity rice."""
import sys, os, re, json, subprocess, time
from pathlib import Path

THEMES_FILE = Path.home() / "dotfiles/themes/themes.json"
CURRENT_FILE = Path.home() / ".config/theme-current"
I3_CONF     = Path.home() / ".config/i3/config"
POLY_CONF   = Path.home() / ".config/polybar/config.ini"
DUNST_CONF  = Path.home() / ".config/dunst/dunstrc"
KITTY_CONF  = Path.home() / ".config/kitty/kitty.conf"
CAVA_CONF   = Path.home() / ".config/cava/config"
FASTFETCH   = Path.home() / ".config/fastfetch/config.jsonc"
FISH_PROMPT = Path.home() / ".config/fish/functions/fish_prompt.fish"
WALL_DIR    = Path.home() / "Pictures/wallpapers"
NL = chr(10)

def read(p):
    try: return Path(p).read_text()
    except: return ""

def write(p, c):
    Path(p).write_text(c)

def replace_ini_in_section(src, section, keyvals):
    lines = src.splitlines()
    out = []
    in_sec = False
    hit = set()
    for line in lines:
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            in_sec = (s == "[" + section + "]")
            out.append(line); continue
        if in_sec:
            m = re.match(r'^(\s*)([a-zA-Z0-9_-]+)(\s*=\s*)(.*)$', line)
            if m and m.group(2) in keyvals:
                out.append(m.group(1) + m.group(2) + m.group(3) + keyvals[m.group(2)])
                hit.add(m.group(2)); continue
        out.append(line)
    if len(hit) < len(keyvals):
        new_out = []
        inserted = False
        for line in out:
            new_out.append(line)
            if not inserted and line.strip() == "[" + section + "]":
                for k, v in keyvals.items():
                    if k not in hit:
                        new_out.append(k + " = " + v)
                inserted = True
        out = new_out
    return NL.join(out) + NL

def apply_polybar(t):
    src = read(POLY_CONF)
    kv = {"bg": t["bg"], "fg": t["fg"], "fg-alt": t["fg_alt"], "blue": t["blue"], "blue-dim": t["blue_dim"], "red": t["red"], "green": t["green"], "yellow": t["yellow"]}
    write(POLY_CONF, replace_ini_in_section(src, "colors", kv))

def apply_polybar_modules(t):
    src = read(POLY_CONF)
    m = re.search(r'(\[module/i3\].*?)(?=\n\[|\Z)', src, re.DOTALL)
    if not m: return
    block = m.group(1)
    rp = {
        "label-focused-foreground": "${colors.bg}",
        "label-focused-background": "${colors.blue}",
        "label-unfocused-foreground": "${colors.fg}",
        "label-unfocused-background": "${colors.blue-dim}",
        "label-visible-foreground": "${colors.fg}",
        "label-visible-background": "${colors.blue-dim}",
        "label-urgent-foreground": "${colors.bg}",
        "label-urgent-background": "${colors.red}",
    }
    lines = block.splitlines()
    nl = []
    for line in lines:
        m2 = re.match(r'^(\s*)([a-zA-Z0-9_-]+)(\s*=\s*)(.*)$', line)
        if m2 and m2.group(2) in rp:
            nl.append(m2.group(1) + m2.group(2) + m2.group(3) + rp[m2.group(2)])
        else: nl.append(line)
    src = src.replace(block, NL.join(nl))
    write(POLY_CONF, src)

def apply_i3_borders(t):
    src = read(I3_CONF)
    src = re.sub(r'^client\.(focused|focused_inactive|unfocused|urgent|placeholder)\s+.*$', '', src, flags=re.M)
    borders = (
        NL + "# ===== window borders (theme colors) =====" + NL +
        "client.focused          " + t["blue"] + " " + t["blue"] + " " + t["bg"] + " " + t["cyan"] + " " + t["blue"] + NL +
        "client.focused_inactive " + t["blue_dim"] + " " + t["blue_dim"] + " " + t["bg"] + " " + t["fg_alt"] + " " + t["blue_dim"] + NL +
        "client.unfocused        " + t["blue_dim"] + " " + t["blue_dim"] + " " + t["bg"] + " " + t["fg_alt"] + " " + t["blue_dim"] + NL +
        "client.urgent           " + t["red"] + " " + t["red"] + " " + t["bg"] + " " + t["fg"] + " " + t["red"] + NL +
        "client.placeholder      " + t["bg"] + " " + t["bg"] + " " + t["bg"] + " " + t["fg"] + " " + t["bg"] + NL
    )
    src = src.rstrip() + NL + borders
    write(I3_CONF, src)

def apply_dunst(t):
    src = read(DUNST_CONF)
    if not src: return
    lines = src.splitlines()
    out = []
    section = "global"
    for line in lines:
        s = line.strip()
        m = re.match(r'^\[([^\]]+)\]$', s)
        if m:
            section = m.group(1)
            out.append(line); continue
        m = re.match(r'^(\s*)(background|foreground|frame_color|highlight)(\s*=\s*)(.*)$', line)
        if m:
            indent, key, eq, _ = m.groups()
            if "critical" in section or "urgent" in section:
                val = t["red"] if key in ("background","frame_color","highlight") else t["bg"]
            elif "low" in section:
                val = t["blue_dim"] if key in ("background","frame_color","highlight") else t["fg"]
            else:
                val = t["bg"] if key == "background" else (t["fg"] if key == "foreground" else t["blue"])
            out.append(indent + key + eq + '"' + val + '"')
        else: out.append(line)
    write(DUNST_CONF, NL.join(out) + NL)

def apply_kitty(t):
    src = read(KITTY_CONF)
    if not src: return
    src = re.sub(r'\n?# ===== rice colors =====.*$', '', src, flags=re.S)
    src += NL + NL + "# ===== rice colors =====" + NL
    src += "background " + t["bg"] + NL
    src += "foreground " + t["fg"] + NL
    src += "cursor " + t["accent"] + NL
    src += "selection_background " + t["blue"] + NL
    src += "selection_foreground " + t["bg"] + NL
    src += "url_color " + t["cyan"] + NL
    write(KITTY_CONF, src)

def apply_cava(t):
    src = read(CAVA_CONF)
    if not src: return
    g1 = t.get("gradient_color_1", t["bg"])
    g2 = t.get("gradient_color_2", t["blue_dim"])
    g3 = t.get("gradient_color_3", t["cyan"])
    g4 = t.get("gradient_color_4", t["blue"])
    pairs = [("background", t["bg"]), ("foreground", t["blue"]),
             ("gradient_color_1", g1), ("gradient_color_2", g2),
             ("gradient_color_3", g3), ("gradient_color_4", g4)]
    lines = src.splitlines()
    out = []
    handled = set()
    for line in lines:
        s = line.strip()
        matched = False
        for key, val in pairs:
            if s.startswith(key + " ") or s.startswith(key + "="):
                out.append(key + " = '" + val + "'")
                handled.add(key); matched = True; break
        if not matched: out.append(line)
    for key, val in pairs:
        if key not in handled: out.append(key + " = '" + val + "'")
    write(CAVA_CONF, NL.join(out) + NL)

def apply_fastfetch(t):
    src = read(FASTFETCH)
    if not src: return
    src = re.sub(r'("keys"\s*:\s*)"[^"]*"', r'\1"' + t["blue"] + r'"', src)
    write(FASTFETCH, src)

def apply_fastfetch_logo(t):
    ascii_file = Path.home() / ".config/fastfetch/trixity-ascii.txt"
    colored_file = Path.home() / ".config/fastfetch/trixity-colored.txt"
    if not ascii_file.exists(): return
    accent = t.get("blue", "#88c0d0")
    try:
        r, g, b = int(accent[1:3],16), int(accent[3:5],16), int(accent[5:7],16)
    except: r, g, b = 136, 192, 208
    esc = chr(27)
    ansi = esc + "[38;2;" + str(r) + ";" + str(g) + ";" + str(b) + "m"
    reset = esc + "[0m"
    raw = ascii_file.read_text().rstrip(NL)
    lines = raw.split(NL)
    colored = NL.join(ansi + l + reset for l in lines)
    colored_file.write_text(colored)

def apply_settings_css(t):
    style = Path.home() / "Documents/trinity-settings/style.css"
    if not style.parent.exists(): return
    def lighten(h, f=0.2):
        try:
            r, g, b = int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)
            return "#{:02x}{:02x}{:02x}".format(min(255,int(r+(255-r)*f)), min(255,int(g+(255-g)*f)), min(255,int(b+(255-b)*f)))
        except: return h
    bg, fg, blue, blue_dim, red = t["bg"], t["fg"], t["blue"], t["blue_dim"], t["red"]
    blue_hover = lighten(blue_dim, 0.15)
    css = "/* Trinity Settings - " + t["name"] + " */" + NL + NL
    css += "window#trinity-settings { background-color: " + bg + "; color: " + fg + "; }" + NL
    css += ".sidebar { background-color: " + blue_dim + "; padding: 16px 8px; border-right: 1px solid " + bg + "; }" + NL
    css += ".sidebar-title { color: " + blue + "; padding: 8px 16px; margin-bottom: 0; }" + NL
    css += "button.sidebar-btn { background-color: transparent; background-image: none; color: " + fg + "; border: none; border-radius: 6px; padding: 10px 16px; font-size: 13px; min-height: 32px; }" + NL
    css += "button.sidebar-btn:hover { background-color: " + blue_hover + "; }" + NL
    css += "button.sidebar-btn.active { background-color: " + blue + "; color: " + bg + "; }" + NL
    css += ".section-title { color: " + blue + "; margin-top: 8px; }" + NL
    css += ".param-label { color: " + fg + "; font-size: 12px; }" + NL
    css += "scale.param-slider trough { background-color: " + blue_dim + "; border-radius: 4px; min-height: 6px; }" + NL
    css += "scale.param-slider highlight { background-color: " + blue + "; border-radius: 4px; }" + NL
    css += "scale.param-slider slider { background-color: " + fg + "; border: 2px solid " + blue + "; min-width: 12px; min-height: 12px; border-radius: 8px; margin: -4px 0; }" + NL
    css += "switch { background-color: " + blue_dim + "; border-radius: 12px; min-width: 40px; min-height: 22px; }" + NL
    css += "switch:checked { background-color: " + blue + "; }" + NL
    css += "switch slider { background-color: " + fg + "; border-radius: 10px; min-width: 18px; min-height: 18px; }" + NL
    css += "button.action-btn { background-color: " + blue_dim + "; color: " + fg + "; border: none; border-radius: 6px; padding: 10px 16px; font-size: 13px; min-height: 36px; }" + NL
    css += "button.action-btn:hover { background-color: " + blue + "; color: " + bg + "; }" + NL
    css += "button.danger-btn { background-color: " + red + "; color: " + fg + "; border: none; border-radius: 6px; padding: 10px 16px; min-height: 36px; }" + NL
    css += "separator { background-color: " + blue_dim + "; min-height: 1px; margin: 8px 0; }" + NL
    style.write_text(css)

def apply_rofi(t):
    rofi_dir = Path.home() / ".config/rofi"
    if not rofi_dir.exists(): return
    theme_file = rofi_dir / "theme.rasi"
    bg, fg, fg_alt, blue, blue_dim, red = t["bg"], t["fg"], t["fg_alt"], t["blue"], t["blue_dim"], t["red"]
    rasi = "/* Trinity Rofi - " + t["name"] + " */" + NL + NL
    rasi += "* {" + NL
    rasi += "    bg:     " + bg + ";" + NL
    rasi += "    bg-alt: " + blue_dim + ";" + NL
    rasi += "    fg:     " + fg + ";" + NL
    rasi += "    fg-alt: " + fg_alt + ";" + NL
    rasi += "    accent: " + blue + ";" + NL
    rasi += "    urgent: " + red + ";" + NL
    rasi += "    background-color: @bg;" + NL
    rasi += "    text-color: @fg;" + NL
    rasi += "}" + NL + NL
    rasi += "window { width: 30%; border: 2px; border-color: @accent; border-radius: 8px; background-color: @bg; padding: 12px; }" + NL
    rasi += "inputbar { background-color: @bg-alt; text-color: @fg; padding: 8px; border-radius: 4px; children: [ prompt, entry ]; }" + NL
    rasi += "prompt { background-color: transparent; text-color: @accent; padding: 0 8px 0 0; }" + NL
    rasi += "entry { background-color: transparent; text-color: @fg; }" + NL
    rasi += "listview { background-color: transparent; padding: 8px 0 0 0; lines: 8; columns: 1; }" + NL
    rasi += "element { background-color: transparent; text-color: @fg; padding: 6px 8px; border-radius: 4px; }" + NL
    rasi += "element selected { background-color: @accent; text-color: @bg; }" + NL
    rasi += "element-icon { background-color: transparent; size: 1.2em; padding: 0 8px 0 0; }" + NL
    theme_file.write_text(rasi)

def apply_wallpaper(t):
    wall = WALL_DIR / t["wallpaper"]
    if not wall.exists(): return
    subprocess.Popen(["feh", "--bg-scale", str(wall)])
    src = read(I3_CONF)
    src = re.sub(r'^exec --no-startup-id feh --bg-scale.*$', '', src, flags=re.M)
    src = src.rstrip() + NL + "exec --no-startup-id feh --bg-scale " + str(wall) + NL
    write(I3_CONF, src)
    subprocess.Popen(["betterlockscreen","-u",str(wall),"--fx","blur"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def reload_all():
    subprocess.run(["killall","polybar"], stderr=subprocess.DEVNULL)
    time.sleep(0.4)
    l = Path.home() / ".config/polybar/launch.sh"
    if l.exists():
        subprocess.Popen(["bash",str(l)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill","dunst"], stderr=subprocess.DEVNULL)
    time.sleep(0.3)
    subprocess.Popen(["dunst"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["i3-msg","reload"], stderr=subprocess.DEVNULL)

def main():
    if not THEMES_FILE.exists():
        print("No themes file: " + str(THEMES_FILE)); sys.exit(1)
    themes = json.loads(THEMES_FILE.read_text())
    if len(sys.argv) < 2:
        cur = CURRENT_FILE.read_text().strip() if CURRENT_FILE.exists() else "none"
        print("Current: " + cur)
        for k, v in themes.items(): print("  " + k.ljust(10) + " - " + v["name"])
        sys.exit(0)
    name = sys.argv[1]
    if name not in themes: print("Unknown: " + name); sys.exit(1)
    t = themes[name]
    print("==> Applying: " + name + " (" + t["name"] + ")")
    apply_polybar(t);         print("   + Polybar colors")
    apply_polybar_modules(t); print("   + Polybar modules")
    apply_i3_borders(t);      print("   + i3 borders")
    apply_dunst(t);           print("   + Dunst")
    apply_kitty(t);           print("   + Kitty")
    apply_cava(t);            print("   + Cava")
    apply_fastfetch(t);       print("   + Fastfetch")
    apply_fastfetch_logo(t);  print("   + Fastfetch logo")
    apply_settings_css(t);    print("   + Trinity CSS")
    apply_rofi(t);            print("   + Rofi")
    apply_wallpaper(t);       print("   + Wallpaper")
    CURRENT_FILE.write_text(name)
    json.dump(t, open(Path.home() / ".config/theme-current.json", "w"), indent=2)
    reload_all()
    subprocess.Popen(["notify-send","-a","theme","Theme: " + t["name"], name])
    print("Done: " + t["name"])

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Polybar i3 workspaces — show 'Trinity' when focused workspace is empty."""

import subprocess
import json
import os


BRAND = "Trinity"
THEME_FILE = os.path.expanduser("~/.config/theme-current.json")


def get_workspaces():
    try:
        out = subprocess.check_output(["i3-msg", "-t", "get_workspaces"], text=True)
        return json.loads(out)
    except Exception:
        return []


def get_theme():
    if os.path.exists(THEME_FILE):
        try:
            return json.load(open(THEME_FILE))
        except Exception:
            pass
    return {}


def main():
    theme = get_theme()
    bg       = theme.get("bg",       "#2e3440")
    fg       = theme.get("fg",       "#eceff4")
    blue     = theme.get("blue",     "#88c0d0")
    blue_dim = theme.get("blue_dim", "#4c566a")
    red      = theme.get("red",      "#bf616a")

    parts = []
    for ws in sorted(get_workspaces(), key=lambda w: w.get("num", 0)):
        focused = ws.get("focused", False)
        visible = ws.get("visible", False)
        urgent  = ws.get("urgent", False)
        name    = ws.get("name", "?")
        windows = ws.get("windows", 0)

        if windows == 0 and focused:
            label = BRAND
        else:
            label = name

        if urgent:
            c_fg, c_bg = bg, red
        elif focused:
            c_fg, c_bg = bg, blue
        else:
            c_fg, c_bg = fg, blue_dim

        parts.append(
            "%{F" + c_fg + "}%{B" + c_bg + "} " + label + " %{B-}%{F-}"
        )

    print(" ".join(parts))


if __name__ == "__main__":
    main()

"""Fish shell settings."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import os, subprocess
from apply_mixin import ApplyBar, DeferredSection

FISH_CONF = os.path.expanduser("~/.config/fish/config.fish")


def st(t):
    l = Gtk.Label(); l.set_markup(f'<span size="large" weight="bold">{t}</span>')
    l.set_xalign(0); l.get_style_context().add_class("section-title"); return l


def build_page(parent):
    scroll = Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14); box.set_border_width(20); scroll.add(box)

    title = Gtk.Label()
    title.set_markup('<span size="x-large" weight="bold">Fish Shell</span>')
    title.set_xalign(0); box.pack_start(title, False, False, 0)
    info = Gtk.Label()
    info.set_markup('<span size="small" color="#9c9c9c">Fish config and abbreviations.</span>')
    info.set_xalign(0); box.pack_start(info, False, False, 0)

    # Abbr list
    box.pack_start(st("Abbreviations"), False, False, 10)

    try:
        abbrs = subprocess.check_output(["fish", "-c", "abbr -s"], text=True, timeout=3).strip().split("\n")
    except:
        abbrs = []

    abbr_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    for line in abbrs:
        if not line:
            continue
        # Format: abbr -a -- name 'value'
        parts = line.split(" ", 4)
        if len(parts) >= 5:
            name = parts[3]
            val = parts[4].strip("'")
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            l = Gtk.Label(label=f"{name}  →  {val}")
            l.set_xalign(0)
            l.get_style_context().add_class("param-label")
            l.set_hexpand(True)
            row.pack_start(l, True, True, 0)
            abbr_box.pack_start(row, False, False, 0)

    if not abbrs:
        abbr_box.pack_start(Gtk.Label(label="No abbreviations defined"), False, False, 0)

    abbr_scroll = Gtk.ScrolledWindow()
    abbr_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    abbr_scroll.add(abbr_box)
    abbr_scroll.set_size_request(-1, 200)
    box.pack_start(abbr_scroll, False, False, 0)

    # Config preview
    box.pack_start(st("config.fish preview"), False, False, 10)
    preview = Gtk.TextView()
    preview.set_editable(False)
    preview.set_monospace(True)
    preview.set_size_request(-1, 200)
    try:
        content = open(FISH_CONF).read()
    except:
        content = "(no config.fish)"
    preview.get_buffer().set_text(content)
    sw = Gtk.ScrolledWindow()
    sw.add(preview)
    box.pack_start(sw, False, False, 0)

    box.pack_start(Gtk.Separator(), False, False, 10)
    ob = Gtk.Button(label="Open config.fish in editor")
    ob.get_style_context().add_class("action-btn")
    ob.connect("clicked", lambda _: subprocess.Popen(["micro", FISH_CONF]))
    box.pack_start(ob, False, False, 0)

    ob2 = Gtk.Button(label="Open fish_prompt.fish in editor")
    ob2.connect("clicked", lambda _: subprocess.Popen(["micro",
        os.path.expanduser("~/.config/fish/functions/fish_prompt.fish")]))
    box.pack_start(ob2, False, False, 0)

    ob3 = Gtk.Button(label="Reload fish config (exec fish)")
    ob3.connect("clicked", lambda _: subprocess.Popen(["kitty", "-e", "fish", "-c", "echo 'Opening new fish shell'"]))
    box.pack_start(ob3, False, False, 0)

    return scroll

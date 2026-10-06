"""Cava visualizer settings (config_utils + Apply)."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import os, subprocess
from apply_mixin import ApplyBar, DeferredSection
from config_utils import cava as C

CAVA_CONF = os.path.expanduser("~/.config/cava/config")


def st(t):
    l = Gtk.Label(); l.set_markup(f'<span size="large" weight="bold">{t}</span>')
    l.set_xalign(0); l.get_style_context().add_class("section-title"); return l


def slider(label, mn, mx, step, init, cb):
    b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label=label); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); b.pack_start(l, False, False, 0)
    s = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, mn, mx, step)
    s.set_value(init); s.set_draw_value(True); s.set_value_pos(Gtk.PositionType.RIGHT)
    s.set_hexpand(True); s.get_style_context().add_class("param-slider")
    s.connect("value-changed", lambda w: cb(w.get_value()))
    b.pack_start(s, True, True, 0)
    return b, s


def color_row(label, key, init, section, cb):
    r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label=label); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); r.pack_start(l, False, False, 0)
    entry = Gtk.Entry(); entry.set_text(init or "#88c0d0"); entry.set_hexpand(True)
    entry.connect("changed", lambda w: cb(key, f"'{w.get_text().strip()}'"))
    r.pack_start(entry, True, True, 0)
    return r


def build_page(parent):
    scroll = Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14); box.set_border_width(20); scroll.add(box)

    pending_colors = {}

    def on_apply(pending):
        c = C()
        for key, val in pending.items():
            if key in ("bars","bar_width","bar_spacing","framerate","sensitivity"):
                c.set(key, val, "general")
            elif key in ("gradient_color_1","gradient_color_2","gradient_color_3","gradient_color_4"):
                c.set(key, val, "color")
            elif key == "method":
                c.set(key, val, "input")

    def on_reload():
        subprocess.run(["pkill", "-USR1", "cava"], stderr=subprocess.DEVNULL)

    section = DeferredSection(on_apply=on_apply, on_reload=on_reload)
    c = C()

    title = Gtk.Label()
    title.set_markup('<span size="x-large" weight="bold">Cava Visualizer</span>')
    title.set_xalign(0); box.pack_start(title, False, False, 0)
    info = Gtk.Label()
    info.set_markup('<span size="small" color="#9c9c9c">Changes apply on next Cava start.</span>')
    info.set_xalign(0); box.pack_start(info, False, False, 0)

    box.pack_start(st("Bars"), False, False, 10)
    v = c.get("bars", None, "general") or "0"
    try:
        cur_bars = int(v)
    except ValueError:
        cur_bars = 0

    def on_bars_change(val):
        n = int(val)
        # Force even number when > 0
        if n > 0 and n % 2 == 1:
            n += 1
        section.set("bars", str(n))

    r, bars_scale = slider("Bars (0=auto, even only)", 0, 100, 2, cur_bars,
                           on_bars_change)
    box.pack_start(r, False, False, 0)

    # Hint label
    hint = Gtk.Label()
    hint.set_markup('<span size="small" color="#9c9c9c">Стерео режим: bars должно быть чётным. 0 = auto.</span>')
    hint.set_xalign(0)
    box.pack_start(hint, False, False, 0)
    v = c.get("bar_width", None, "general") or "3"
    r, _ = slider("Bar width", 1, 10, 1, int(v), lambda v: section.set("bar_width", str(int(v))))
    box.pack_start(r, False, False, 0)
    v = c.get("bar_spacing", None, "general") or "2"
    r, _ = slider("Bar spacing", 0, 10, 1, int(v), lambda v: section.set("bar_spacing", str(int(v))))
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Frequency range"), False, False, 10)
    v = c.get("lower_cutoff_freq", None, "general") or "50"
    r, _ = slider("Lower cutoff (Hz)", 20, 500, 10, int(v),
                  lambda v: section.set("lower_cutoff_freq", str(int(v))))
    box.pack_start(r, False, False, 0)
    v = c.get("higher_cutoff_freq", None, "general") or "10000"
    r, _ = slider("Upper cutoff (Hz)", 5000, 20000, 500, int(v),
                  lambda v: section.set("higher_cutoff_freq", str(int(v))))
    box.pack_start(r, False, False, 0)

    r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label="Auto-sensitivity"); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); r.pack_start(l, False, False, 0)
    sw = Gtk.Switch()
    sw.set_active(c.get("autosens", None, "general") != "0")
    sw.connect("notify::active", lambda w, _: section.set("autosens", "1" if w.get_active() else "0"))
    r.pack_end(sw, False, False, 0)
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Performance"), False, False, 10)
    v = c.get("framerate", None, "general") or "60"
    r, _ = slider("Framerate (fps)", 15, 144, 1, int(v), lambda v: section.set("framerate", str(int(v))))
    box.pack_start(r, False, False, 0)
    v = c.get("sensitivity", None, "general") or "100"
    r, _ = slider("Sensitivity", 10, 300, 5, int(v), lambda v: section.set("sensitivity", str(int(v))))
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Input"), False, False, 10)
    r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label="Method"); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); r.pack_start(l, False, False, 0)
    combo = Gtk.ComboBoxText()
    for m in ["pipewire", "pulse", "alsa"]: combo.append_text(m)
    cur = c.get("method", None, "input") or "pipewire"
    if cur in ["pipewire","pulse","alsa"]: combo.set_active(["pipewire","pulse","alsa"].index(cur))
    combo.connect("changed", lambda cc: section.set("method", cc.get_active_text()))
    r.pack_start(combo, True, True, 0)
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Gradient (4 colors, bottom to top)"), False, False, 10)
    for i, key in enumerate(["gradient_color_1","gradient_color_2","gradient_color_3","gradient_color_4"], 1):
        v = c.get(key, "color") or "#88c0d0"
        box.pack_start(color_row(f"Color {i}", key, v, "color",
                      lambda k, val: section.set(k, val)), False, False, 0)

    box.pack_start(Gtk.Separator(), False, False, 10)
    rb = Gtk.Button(label="Reload Cava now")
    rb.get_style_context().add_class("action-btn")
    rb.connect("clicked", lambda _: on_reload())
    box.pack_start(rb, False, False, 0)
    ob = Gtk.Button(label="Open cava config in editor")
    ob.connect("clicked", lambda _: subprocess.Popen(["micro", CAVA_CONF]))
    box.pack_start(ob, False, False, 0)

    bar = ApplyBar(on_apply=section.apply, on_reset=section.reset)
    section.attach_bar(bar)
    box.pack_start(Gtk.Separator(), False, False, 10)
    box.pack_start(bar, False, False, 0)

    return scroll

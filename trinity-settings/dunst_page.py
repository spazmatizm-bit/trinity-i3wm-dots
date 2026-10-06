"""Dunst settings (config_utils + Apply)."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import os, subprocess, time
from apply_mixin import ApplyBar, DeferredSection
from config_utils import dunst as D

DUNST_CONF = os.path.expanduser("~/.config/dunst/dunstrc")


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


def build_page(parent):
    scroll = Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14); box.set_border_width(20); scroll.add(box)

    def on_apply(pending):
        d = D()
        for key, val in pending.items():
            if key in ("timeout_low","timeout_normal","timeout_critical"):
                sec = {"timeout_low":"urgency_low","timeout_normal":"urgency_normal","timeout_critical":"urgency_critical"}[key]
                d.set("timeout", val, sec)
            else:
                d.set(key, val, "global")

    def on_reload():
        subprocess.run(["pkill", "dunst"], stderr=subprocess.DEVNULL)
        time.sleep(0.3)
        subprocess.Popen(["dunst"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    section = DeferredSection(on_apply=on_apply, on_reload=on_reload)
    d = D()

    title = Gtk.Label()
    title.set_markup('<span size="x-large" weight="bold">Dunst Notifications</span>')
    title.set_xalign(0); box.pack_start(title, False, False, 0)
    info = Gtk.Label()
    info.set_markup('<span size="small" color="#9c9c9c">Changes apply on Apply.</span>')
    info.set_xalign(0); box.pack_start(info, False, False, 0)

    box.pack_start(st("Position"), False, False, 10)
    r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label="Origin"); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); r.pack_start(l, False, False, 0)
    combo = Gtk.ComboBoxText()
    origins = ["top-right","top-left","top-center","bottom-right","bottom-left","bottom-center","right-center","left-center","center"]
    for o in origins: combo.append_text(o)
    cur = d.get("origin", None, "global") or "top-right"
    if cur in origins: combo.set_active(origins.index(cur))
    combo.connect("changed", lambda c: section.set("origin", c.get_active_text()))
    r.pack_start(combo, True, True, 0)
    box.pack_start(r, False, False, 0)

    v = d.get("offset", None, "global") or "10x40"
    r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label="Offset (WxH)"); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); r.pack_start(l, False, False, 0)
    entry = Gtk.Entry(); entry.set_text(v); entry.set_hexpand(True)
    entry.connect("changed", lambda w: section.set("offset", w.get_text().strip()))
    r.pack_start(entry, True, True, 0)
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Size"), False, False, 10)
    v = d.get("width", None, "global") or "350"
    r, _ = slider("Width (px)", 200, 800, 10, int(v), lambda v: section.set("width", str(int(v))))
    box.pack_start(r, False, False, 0)
    v = d.get("height", None, "global") or "300"
    r, _ = slider("Max height (px)", 100, 800, 10, int(v), lambda v: section.set("height", str(int(v))))
    box.pack_start(r, False, False, 0)
    v = d.get("corner_radius", None, "global") or "10"
    r, _ = slider("Corner radius", 0, 30, 1, int(v), lambda v: section.set("corner_radius", str(int(v))))
    box.pack_start(r, False, False, 0)
    v = d.get("padding", None, "global") or "12"
    r, _ = slider("Padding", 0, 30, 1, int(v), lambda v: section.set("padding", str(int(v))))
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Appearance"), False, False, 10)

    r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label="Font"); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); r.pack_start(l, False, False, 0)
    entry = Gtk.Entry()
    entry.set_text(d.get("font", None, "global") or "JetBrainsMono Nerd Font 10")
    entry.set_hexpand(True)
    entry.connect("changed", lambda w: section.set("font", w.get_text().strip()))
    r.pack_start(entry, True, True, 0)
    box.pack_start(r, False, False, 0)

    v = d.get("frame_width", None, "global") or "1"
    r, _ = slider("Frame width", 0, 10, 1, int(v),
                  lambda v: section.set("frame_width", str(int(v))))
    box.pack_start(r, False, False, 0)

    v = d.get("gap_size", None, "global") or "8"
    r, _ = slider("Gap size", 0, 30, 1, int(v),
                  lambda v: section.set("gap_size", str(int(v))))
    box.pack_start(r, False, False, 0)

    v = d.get("separator_height", None, "global") or "1"
    r, _ = slider("Separator height", 0, 10, 1, int(v),
                  lambda v: section.set("separator_height", str(int(v))))
    box.pack_start(r, False, False, 0)

    v = d.get("horizontal_padding", None, "global") or "12"
    r, _ = slider("Horizontal padding", 0, 40, 1, int(v),
                  lambda v: section.set("horizontal_padding", str(int(v))))
    box.pack_start(r, False, False, 0)

    v = d.get("icon_size", None, "global") or "32"
    r, _ = slider("Max icon size", 16, 128, 4, int(v),
                  lambda v: section.set("max_icon_size", str(int(v))))
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Timeouts (seconds)"), False, False, 10)
    v = d.get("timeout", None, "urgency_low") or "5"
    r, _ = slider("Low", 0, 30, 1, int(v), lambda v: section.set("timeout_low", str(int(v))))
    box.pack_start(r, False, False, 0)
    v = d.get("timeout", None, "urgency_normal") or "5"
    r, _ = slider("Normal", 0, 30, 1, int(v), lambda v: section.set("timeout_normal", str(int(v))))
    box.pack_start(r, False, False, 0)
    v = d.get("timeout", None, "urgency_critical") or "0"
    r, _ = slider("Critical (0=forever)", 0, 30, 1, int(v), lambda v: section.set("timeout_critical", str(int(v))))
    box.pack_start(r, False, False, 0)

    box.pack_start(Gtk.Separator(), False, False, 10)
    tb = Gtk.Button(label="Test notification")
    tb.get_style_context().add_class("action-btn")
    tb.connect("clicked", lambda _: subprocess.Popen(["dunstify", "Test", "Dunst notification test"]))
    box.pack_start(tb, False, False, 0)
    rb = Gtk.Button(label="Restart Dunst now")
    rb.connect("clicked", lambda _: on_reload())
    box.pack_start(rb, False, False, 0)
    ob = Gtk.Button(label="Open dunstrc in editor")
    ob.connect("clicked", lambda _: subprocess.Popen(["micro", DUNST_CONF]))
    box.pack_start(ob, False, False, 0)

    bar = ApplyBar(on_apply=section.apply, on_reset=section.reset)
    section.attach_bar(bar)
    box.pack_start(Gtk.Separator(), False, False, 10)
    box.pack_start(bar, False, False, 0)

    return scroll

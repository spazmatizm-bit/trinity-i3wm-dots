"""Kitty terminal settings (config_utils + Apply)."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import os, subprocess
from apply_mixin import ApplyBar, DeferredSection
from config_utils import kitty as K

KITTY_CONF = os.path.expanduser("~/.config/kitty/kitty.conf")


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


def toggle(label, active, cb):
    b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label=label); l.set_width_chars(32); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); b.pack_start(l, False, False, 0)
    sw = Gtk.Switch(); sw.set_active(active)
    sw.connect("notify::active", lambda w, _: cb(w.get_active()))
    b.pack_end(sw, False, False, 0)
    return b


def build_page(parent):
    scroll = Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14); box.set_border_width(20); scroll.add(box)

    def on_apply(pending):
        k = K()
        for key, val in pending.items():
            k.set(key, val)

    def on_reload():
        # Reload all running kitty instances
        subprocess.run(["kitty", "@", "--to", "unix:/tmp/kitty-socket", "load-config"],
                       stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-SIGUSR1", "kitty"], stderr=subprocess.DEVNULL)

    section = DeferredSection(on_apply=on_apply, on_reload=on_reload)
    k = K()

    title = Gtk.Label()
    title.set_markup('<span size="x-large" weight="bold">Kitty Terminal</span>')
    title.set_xalign(0); box.pack_start(title, False, False, 0)
    info = Gtk.Label()
    info.set_markup('<span size="small" color="#9c9c9c">Changes apply to all running kitty windows on Apply.</span>')
    info.set_xalign(0); box.pack_start(info, False, False, 0)

    box.pack_start(st("Font"), False, False, 10)

    r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label="Font family"); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); r.pack_start(l, False, False, 0)
    entry = Gtk.Entry()
    entry.set_text(k.get("font_family") or "JetBrainsMono Nerd Font")
    entry.set_hexpand(True)
    entry.connect("changed", lambda w: section.set("font_family", w.get_text().strip()))
    r.pack_start(entry, True, True, 0)
    box.pack_start(r, False, False, 0)

    v = k.get("font_size") or "11"
    r, _ = slider("Font size", 6, 24, 1, int(float(v)), lambda v: section.set("font_size", str(int(v))))
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Appearance"), False, False, 10)

    v = k.get("background_opacity") or "0.95"
    r, _ = slider("Opacity (%)", 50, 100, 1, int(float(v) * 100),
                  lambda v: section.set("background_opacity", f"{v/100:.2f}"))
    box.pack_start(r, False, False, 0)

    v = k.get("window_padding_width") or "8"
    r, _ = slider("Padding (px)", 0, 40, 1, int(v), lambda v: section.set("window_padding_width", str(int(v))))
    box.pack_start(r, False, False, 0)

    r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label="Cursor shape"); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); r.pack_start(l, False, False, 0)
    combo = Gtk.ComboBoxText()
    for shape in ["block", "beam", "underline"]: combo.append_text(shape)
    cur = k.get("cursor_shape") or "block"
    if cur in ["block", "beam", "underline"]: combo.set_active(["block","beam","underline"].index(cur))
    combo.connect("changed", lambda c: section.set("cursor_shape", c.get_active_text()))
    r.pack_start(combo, True, True, 0)
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Window margins"), False, False, 10)
    v = k.get("window_margin_width") or "0"
    r, _ = slider("Window margin (px)", 0, 60, 1, int(v) if v.isdigit() else 0,
                  lambda v: section.set("window_margin_width", str(int(v))))
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Tab bar"), False, False, 10)
    r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label="Tab style"); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); r.pack_start(l, False, False, 0)
    combo = Gtk.ComboBoxText()
    for s in ["powerline", "powerline_rounded", "separator", "slant", "fade", "custom"]:
        combo.append_text(s)
    cur = k.get("tab_bar_style") or "powerline"
    if cur in ["powerline","powerline_rounded","separator","slant","fade","custom"]:
        combo.set_active(["powerline","powerline_rounded","separator","slant","fade","custom"].index(cur))
    combo.connect("changed", lambda c: section.set("tab_bar_style", c.get_active_text()))
    r.pack_start(combo, True, True, 0)
    box.pack_start(r, False, False, 0)

    r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label="Tab position"); l.set_width_chars(22); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); r.pack_start(l, False, False, 0)
    combo = Gtk.ComboBoxText()
    for s in ["top", "bottom"]: combo.append_text(s)
    cur = k.get("tab_bar_edge") or "bottom"
    if cur in ["top", "bottom"]: combo.set_active(["top","bottom"].index(cur))
    combo.connect("changed", lambda c: section.set("tab_bar_edge", c.get_active_text()))
    r.pack_start(combo, True, True, 0)
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Cursor blink"), False, False, 10)
    v = k.get("cursor_blink_interval") or "0.5"
    try: cur = int(float(v) * 10)
    except: cur = 5
    r, _ = slider("Blink interval ×0.1s (0=off)", 0, 20, 1, cur,
                  lambda v: section.set("cursor_blink_interval", f"{v/10:.1f}"))
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Scrollback"), False, False, 10)
    v = k.get("scrollback_lines") or "10000"
    r, _ = slider("Lines", 100, 100000, 100, int(v),
                  lambda v: section.set("scrollback_lines", str(int(v))))
    box.pack_start(r, False, False, 0)

    box.pack_start(st("Toggles"), False, False, 10)
    box.pack_start(toggle("Hide window decorations",
        k.get("hide_window_decorations") == "yes",
        lambda v: section.set("hide_window_decorations", "yes" if v else "no")), False, False, 0)
    box.pack_start(toggle("Enable audio bell",
        k.get("enable_audio_bell") == "yes",
        lambda v: section.set("enable_audio_bell", "yes" if v else "no")), False, False, 0)
    box.pack_start(toggle("Copy on select",
        k.get("copy_on_select") == "yes",
        lambda v: section.set("copy_on_select", "yes" if v else "no")), False, False, 0)
    box.pack_start(toggle("Confirm close (Ctrl+Shift+W)",
        k.get("confirm_os_window_close") == "1",
        lambda v: section.set("confirm_os_window_close", "1" if v else "0")), False, False, 0)

    box.pack_start(Gtk.Separator(), False, False, 10)
    rb = Gtk.Button(label="Reload Kitty now")
    rb.get_style_context().add_class("action-btn")
    rb.connect("clicked", lambda _: on_reload())
    box.pack_start(rb, False, False, 0)
    ob = Gtk.Button(label="Open kitty.conf in editor")
    ob.connect("clicked", lambda _: subprocess.Popen(["micro", KITTY_CONF]))
    box.pack_start(ob, False, False, 0)

    bar = ApplyBar(on_apply=section.apply, on_reset=section.reset)
    section.attach_bar(bar)
    box.pack_start(Gtk.Separator(), False, False, 10)
    box.pack_start(bar, False, False, 0)

    return scroll

"""Presets page — Save All As / Load All From."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import os, sys, subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_presets import list_presets, save_preset, load_preset, delete_preset, PRESETS_DIR


def st(t):
    l = Gtk.Label(); l.set_markup(f'<span size="large" weight="bold">{t}</span>')
    l.set_xalign(0); l.get_style_context().add_class("section-title")
    return l


def build_page(parent):
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    box.set_border_width(20)
    scroll.add(box)

    title = Gtk.Label()
    title.set_markup('<span size="x-large" weight="bold">Presets</span>')
    title.set_xalign(0)
    box.pack_start(title, False, False, 0)

    info = Gtk.Label()
    info.set_markup('<span size="small" color="#9c9c9c">Save your entire Trinity config as a preset. Load it later to restore.</span>')
    info.set_xalign(0); info.set_line_wrap(True)
    box.pack_start(info, False, False, 0)

    box.pack_start(st("Actions"), False, False, 10)

    actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    actions.set_homogeneous(True)
    box.pack_start(actions, False, False, 0)

    list_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

    def refresh():
        for c in list_container.get_children():
            list_container.remove(c)
        presets = list_presets()
        if not presets:
            e = Gtk.Label()
            e.set_markup('<span color="#9c9c9c">No presets yet. Click "Save All As…" to create one.</span>')
            e.set_xalign(0)
            list_container.pack_start(e, False, False, 0)
        else:
            for p in presets:
                list_container.pack_start(_row(parent, p, refresh), False, False, 0)
        list_container.show_all()

    save_btn = Gtk.Button(label="Save All As…")
    save_btn.get_style_context().add_class("action-btn")
    save_btn.connect("clicked", lambda _: _save_dlg(parent, refresh))
    actions.pack_start(save_btn, True, True, 0)

    load_btn = Gtk.Button(label="Load All From…")
    load_btn.get_style_context().add_class("action-btn")
    load_btn.connect("clicked", lambda _: _load_dlg(parent, refresh))
    actions.pack_start(load_btn, True, True, 0)

    box.pack_start(st("Saved Presets"), False, False, 10)
    box.pack_start(list_container, False, False, 0)

    box.pack_start(Gtk.Separator(), False, False, 10)
    footer = Gtk.Label()
    footer.set_markup(f'<span size="small" color="#9c9c9c">Storage:</span>\n<span size="small" font_family="monospace" color="#88c0d0">{PRESETS_DIR}</span>')
    footer.set_xalign(0)
    box.pack_start(footer, False, False, 0)

    open_btn = Gtk.Button(label="Open presets folder")
    open_btn.connect("clicked", lambda _: subprocess.Popen(["xdg-open", str(PRESETS_DIR)]))
    box.pack_start(open_btn, False, False, 0)

    refresh()
    return scroll


def _row(parent, preset, refresh_cb):
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    row.set_margin_top(4); row.set_margin_bottom(4)

    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    vbox.set_hexpand(True)

    n = Gtk.Label(); n.set_markup(f'<b>{preset["name"]}</b>'); n.set_xalign(0)
    vbox.pack_start(n, False, False, 0)

    meta = f'{preset["timestamp"]} · theme: {preset["theme"]}'
    m = Gtk.Label()
    m.set_markup(f'<span size="small" color="#9c9c9c">{meta}</span>')
    m.set_xalign(0)
    vbox.pack_start(m, False, False, 0)

    row.pack_start(vbox, True, True, 0)

    lb = Gtk.Button(label="Load")
    lb.set_size_request(80, -1)
    lb.connect("clicked", lambda _, p=preset: _quick_load(parent, p, refresh_cb))
    row.pack_end(lb, False, False, 0)

    db = Gtk.Button(label="×")
    db.get_style_context().add_class("danger-btn")
    db.set_size_request(40, -1)
    db.connect("clicked", lambda _, p=preset: _delete(parent, p, refresh_cb))
    row.pack_end(db, False, False, 0)

    return row


def _save_dlg(parent, refresh_cb):
    d = Gtk.Dialog(title="Save All As", transient_for=parent, flags=0)
    d.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)
    d.set_default_size(450, 240)
    c = d.get_content_area(); c.set_spacing(10); c.set_border_width(15)

    c.add(Gtk.Label(label="Preset name:", xalign=0))
    ne = Gtk.Entry(); ne.set_text("preset-" + datetime.now().strftime("%Y%m%d-%H%M")); c.add(ne)

    c.add(Gtk.Label(label="Description (optional):", xalign=0))
    de = Gtk.Entry(); de.set_placeholder_text("e.g. Work setup"); c.add(de)

    hint = Gtk.Label()
    hint.set_markup('<span size="small" color="#9c9c9c">Saves: i3, polybar, picom, kitty, rofi, dunst, fish, fastfetch, cava, themes</span>')
    hint.set_xalign(0); hint.set_line_wrap(True); c.add(hint)

    d.show_all()
    if d.run() == Gtk.ResponseType.OK:
        name = ne.get_text().strip()
        desc = de.get_text().strip()
        if name:
            try:
                path, count = save_preset(name, desc)
                subprocess.Popen(["dunstify", "-a", "trinity", "-u", "low",
                                  f"Preset saved: {name}", f"{count} files"])
                refresh_cb()
            except Exception as e:
                subprocess.Popen(["dunstify", "-a", "trinity", "-u", "critical",
                                  "Save failed", str(e)])
    d.destroy()


def _load_dlg(parent, refresh_cb):
    presets = list_presets()
    if not presets:
        d = Gtk.MessageDialog(transient_for=parent, flags=0,
                              message_type=Gtk.MessageType.INFO,
                              buttons=Gtk.ButtonsType.OK,
                              text="No presets saved yet")
        d.format_secondary_text("Click 'Save All As…' first.")
        d.run(); d.destroy()
        return

    d = Gtk.Dialog(title="Load All From", transient_for=parent, flags=0)
    d.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Load", Gtk.ResponseType.OK)
    d.set_default_size(500, 400)
    c = d.get_content_area(); c.set_spacing(10); c.set_border_width(15)

    c.add(Gtk.Label(label="Select preset to load:", xalign=0))

    sc = Gtk.ScrolledWindow()
    sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    lb = Gtk.ListBox(); lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
    rows = {}
    for p in presets:
        r = Gtk.ListBoxRow()
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hb.set_margin_top(6); hb.set_margin_bottom(6)
        hb.set_margin_start(8); hb.set_margin_end(8)
        vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        nl = Gtk.Label(); nl.set_markup(f'<b>{p["name"]}</b>'); nl.set_xalign(0)
        vb.pack_start(nl, False, False, 0)
        ml = Gtk.Label()
        ml.set_markup(f'<span size="small" color="#9c9c9c">{p["timestamp"]} · {p["theme"]}</span>')
        ml.set_xalign(0)
        vb.pack_start(ml, False, False, 0)
        hb.pack_start(vb, True, True, 0)
        r.add(hb); lb.add(r)
        rows[r] = p
    sc.add(lb); c.add(sc)

    warn = Gtk.Label()
    warn.set_markup('<span size="small" color="#ebcb8b">⚠ Current configs will be backed up before loading</span>')
    warn.set_xalign(0); c.add(warn)

    d.show_all()
    if d.run() == Gtk.ResponseType.OK:
        sel = lb.get_selected_row()
        if sel and sel in rows:
            p = rows[sel]
            try:
                count, backup = load_preset(p["name"])
                subprocess.Popen(["dunstify", "-a", "trinity", "-u", "normal",
                                  f"Loaded: {p['name']}", f"{count} files"])
                refresh_cb()
            except Exception as e:
                subprocess.Popen(["dunstify", "-a", "trinity", "-u", "critical",
                                  "Load failed", str(e)])
    d.destroy()


def _quick_load(parent, preset, refresh_cb):
    d = Gtk.MessageDialog(transient_for=parent, flags=0,
                          message_type=Gtk.MessageType.QUESTION,
                          buttons=Gtk.ButtonsType.YES_NO,
                          text=f"Load preset '{preset['name']}'?")
    d.format_secondary_text("Current configs will be backed up first.")
    resp = d.run(); d.destroy()
    if resp == Gtk.ResponseType.YES:
        try:
            count, backup = load_preset(preset["name"])
            subprocess.Popen(["dunstify", "-a", "trinity", "-u", "normal",
                              f"Loaded: {preset['name']}", f"{count} files restored"])
            refresh_cb()
        except Exception as e:
            subprocess.Popen(["dunstify", "-a", "trinity", "-u", "critical",
                              "Load failed", str(e)])


def _delete(parent, preset, refresh_cb):
    d = Gtk.MessageDialog(transient_for=parent, flags=0,
                          message_type=Gtk.MessageType.WARNING,
                          buttons=Gtk.ButtonsType.YES_NO,
                          text=f"Delete preset '{preset['name']}'?")
    resp = d.run(); d.destroy()
    if resp == Gtk.ResponseType.YES:
        if delete_preset(preset["name"]):
            subprocess.Popen(["dunstify", "-a", "trinity", "Preset deleted", preset["name"]])
            refresh_cb()

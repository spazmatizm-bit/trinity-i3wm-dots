"""Themes page for Trinity Settings."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import os
import json
import subprocess


THEMES_FILE = os.path.expanduser("~/dotfiles/themes/themes.json")
CURRENT_FILE = os.path.expanduser("~/.config/theme-current")
THEME_SWITCH = os.path.expanduser("~/.config/i3/scripts/theme-switch.sh")
POLY_CONF = os.path.expanduser("~/.config/polybar/config.ini")


def read_file(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return ""


def load_themes():
    try:
        with open(THEMES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_themes(themes):
    os.makedirs(os.path.dirname(THEMES_FILE), exist_ok=True)
    with open(THEMES_FILE, "w") as f:
        json.dump(themes, f, indent=2)


def current_theme():
    try:
        with open(CURRENT_FILE) as f:
            return f.read().strip()
    except Exception:
        return "none"


def read_current_colors():
    src = read_file(POLY_CONF)
    import re
    mapping = {
        "bg": "bg", "fg": "fg", "fg_alt": "fg-alt",
        "blue": "blue", "blue_dim": "blue-dim",
        "red": "red", "green": "green", "yellow": "yellow",
        "cyan": "cyan", "accent": "blue",
    }
    result = {}
    for key, ini_key in mapping.items():
        m = re.search(rf'^\s*{re.escape(ini_key)}\s*=\s*(\S+)', src, re.M)
        result[key] = m.group(1) if m else "#000000"
    return result


def _draw_swatch(widget, cr, color):
    try:
        r = int(color[1:3], 16) / 255
        g = int(color[3:5], 16) / 255
        b = int(color[5:7], 16) / 255
        cr.set_source_rgb(r, g, b)
    except Exception:
        cr.set_source_rgb(0.5, 0.5, 0.5)
    cr.rectangle(0, 0, widget.get_allocated_width(), widget.get_allocated_height())
    cr.fill()


def build_page(parent):
    """Return a ScrolledWindow with themes UI. `parent` = main window."""
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    box.set_border_width(20)
    scroll.add(box)

    # Title
    title = Gtk.Label()
    title.set_markup('<span size="large" weight="bold">Themes</span>')
    title.set_xalign(0)
    box.pack_start(title, False, False, 0)

    cur = current_theme()
    cur_lbl = Gtk.Label()
    cur_lbl.set_markup(f'<span size="small" color="#9c9c9c">Current: <b>{cur}</b></span>')
    cur_lbl.set_xalign(0)
    box.pack_start(cur_lbl, False, False, 0)

    themes = load_themes()

    # Rebuild button
    def rebuild():
        # Remove all children from box
        for child in box.get_children():
            box.remove(child)
        # Re-add
        box.pack_start(title, False, False, 0)
        box.pack_start(cur_lbl, False, False, 0)
        _render_themes(box, themes, parent)

    _render_themes(box, themes, parent)

    # Bottom actions
    box.pack_start(Gtk.Separator(), False, False, 10)

    save_btn = Gtk.Button(label="Save current as new theme")
    save_btn.get_style_context().add_class("action-btn")
    save_btn.connect("clicked", lambda _: _save_theme_dialog(parent))
    box.pack_start(save_btn, False, False, 0)

    import_btn = Gtk.Button(label="Import theme from JSON")
    import_btn.get_style_context().add_class("action-btn")
    import_btn.connect("clicked", lambda _: _import_theme(parent))
    box.pack_start(import_btn, False, False, 0)

    gen_btn = Gtk.Button(label="Generate theme from image")
    gen_btn.get_style_context().add_class("action-btn")
    gen_btn.connect("clicked", lambda _: _generate_from_image(parent))
    box.pack_start(gen_btn, False, False, 0)

    return scroll


def _render_themes(box, themes, parent):
    for name, t in themes.items():
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        swatch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        for key in ("bg", "blue", "red", "green", "yellow"):
            sw = Gtk.DrawingArea()
            sw.set_size_request(24, 24)
            c = t.get(key, "#000000")
            sw.connect("draw", _draw_swatch, c)
            swatch_box.pack_start(sw, False, False, 0)
        row.pack_start(swatch_box, False, False, 0)

        name_lbl = Gtk.Label()
        name_lbl.set_markup(f'<b>{t.get("name", name)}</b>')
        name_lbl.set_width_chars(15)
        name_lbl.set_xalign(0)
        row.pack_start(name_lbl, False, False, 0)

        row.pack_start(Gtk.Label(label=""), True, True, 0)

        apply_btn = Gtk.Button(label="Apply")
        apply_btn.get_style_context().add_class("action-btn")
        apply_btn.connect("clicked",
                          lambda _, n=name: _apply(n, parent))
        row.pack_start(apply_btn, False, False, 0)

        edit_btn = Gtk.Button(label="Edit")
        edit_btn.connect("clicked",
                         lambda _: subprocess.Popen(["micro", THEMES_FILE]))
        row.pack_start(edit_btn, False, False, 0)

        if name != "nordy":
            del_btn = Gtk.Button(label="×")
            del_btn.get_style_context().add_class("danger-btn")
            del_btn.set_size_request(30, -1)
            del_btn.connect("clicked",
                            lambda _, n=name: _delete(n, parent))
            row.pack_start(del_btn, False, False, 0)

        box.pack_start(row, False, False, 2)


def _apply(name, parent):
    if not os.path.exists(THEME_SWITCH):
        _toast(parent, f"Not found: {THEME_SWITCH}")
        return
    subprocess.Popen([THEME_SWITCH, name])
    _toast(parent, f"Applying: {name}")


def _delete(name, parent):
    dlg = Gtk.MessageDialog(
        transient_for=parent, flags=0,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.YES_NO,
        text=f"Delete theme '{name}'?",
    )
    if dlg.run() != Gtk.ResponseType.YES:
        dlg.destroy()
        return
    dlg.destroy()

    themes = load_themes()
    if name in themes:
        del themes[name]
        save_themes(themes)
        _toast(parent, f"Deleted: {name}")


def _save_theme_dialog(parent):
    dlg = Gtk.Dialog(title="Save Theme", transient_for=parent, flags=0)
    dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)
    dlg.set_default_size(400, 250)

    content = dlg.get_content_area()
    content.set_spacing(10)
    content.set_border_width(15)

    content.add(Gtk.Label(label="Theme ID (a-z, 0-9, -, _):", xalign=0))
    id_entry = Gtk.Entry()
    content.add(id_entry)

    content.add(Gtk.Label(label="Display name:", xalign=0))
    name_entry = Gtk.Entry()
    content.add(name_entry)

    content.add(Gtk.Label(label="Wallpaper filename:", xalign=0))
    wall_entry = Gtk.Entry()
    wall_entry.set_text("clouds_above_a_mountain.png")
    content.add(wall_entry)

    dlg.show_all()
    if dlg.run() == Gtk.ResponseType.OK:
        tid = id_entry.get_text().strip().replace(" ", "_").lower()
        tname = name_entry.get_text().strip()
        wall = wall_entry.get_text().strip()
        if tid and tname:
            colors = read_current_colors()
            themes = load_themes()
            themes[tid] = {"name": tname, "wallpaper": wall, **colors}
            save_themes(themes)
            _toast(parent, f"Saved: {tname}")
        else:
            _toast(parent, "ID and name required")
    dlg.destroy()


def _import_theme(parent):
    dlg = Gtk.FileChooserDialog(
        title="Import Theme", transient_for=parent,
        action=Gtk.FileChooserAction.OPEN,
    )
    dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Open", Gtk.ResponseType.OK)
    f = Gtk.FileFilter()
    f.set_name("JSON")
    f.add_pattern("*.json")
    dlg.add_filter(f)

    if dlg.run() == Gtk.ResponseType.OK:
        path = dlg.get_filename()
        try:
            with open(path) as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                raise ValueError("Not a dict")
            themes = load_themes()
            if "name" in data and "bg" in data:
                tid = os.path.splitext(os.path.basename(path))[0]
                themes[tid] = data
            else:
                themes.update(data)
            save_themes(themes)
            _toast(parent, "Theme imported")
        except Exception as e:
            _toast(parent, f"Error: {e}")
    dlg.destroy()


def _toast(parent, message):
    dlg = Gtk.MessageDialog(
        transient_for=parent, flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=message,
    )
    dlg.run()
    dlg.destroy()



def _generate_from_image(parent):
    """Open file picker, generate theme from selected image."""
    dlg = Gtk.FileChooserDialog(
        title="Choose image",
        transient_for=parent,
        action=Gtk.FileChooserAction.OPEN,
    )
    dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL,
                    "Generate", Gtk.ResponseType.OK)

    f = Gtk.FileFilter()
    f.set_name("Images")
    f.add_pattern("*.png")
    f.add_pattern("*.jpg")
    f.add_pattern("*.jpeg")
    dlg.add_filter(f)

    dlg.set_current_folder(os.path.expanduser("~/Pictures/wallpapers"))

    resp = dlg.run()
    path = dlg.get_filename()
    dlg.destroy()

    if resp != Gtk.ResponseType.OK or not path:
        return

    script = os.path.expanduser("~/.config/i3/scripts/theme-from-image.sh")
    if not os.path.exists(script):
        _toast(parent, "Script not found:\n" + script)
        return

    try:
        subprocess.Popen([script, path])
        _toast(parent, "Generating theme...\nWatch notifications.")
    except Exception as e:
        _toast(parent, "Error: " + str(e))

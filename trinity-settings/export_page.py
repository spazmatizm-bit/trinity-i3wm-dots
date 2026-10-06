"""Export / Import page for Trinity Settings."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import os
import subprocess
import shutil
import tempfile
from datetime import datetime


EXPORT_DIR = os.path.expanduser("~/Documents/trinity-exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def build_page(parent):
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    box.set_border_width(20)
    scroll.add(box)

    title = Gtk.Label()
    title.set_markup('<span size="large" weight="bold">Export / Import</span>')
    title.set_xalign(0)
    box.pack_start(title, False, False, 0)

    info = Gtk.Label()
    info.set_markup(
        '<span size="small" color="#9c9c9c">'
        'Export your entire rice as a single .tar.gz file.\n'
        'Share with friends or backup before experimenting.'
        '</span>'
    )
    info.set_xalign(0)
    info.set_line_wrap(True)
    box.pack_start(info, False, False, 0)

    box.pack_start(Gtk.Separator(), False, False, 10)

    box.pack_start(_section_title("Export"), False, False, 0)

    for label, fn in [
        ("Export full rice to .tar.gz", _export_rice),
        ("Export themes only (.tar.gz)", _export_themes),
        ("Export configs only (.tar.gz)", _export_configs),
    ]:
        btn = Gtk.Button(label=label)
        btn.get_style_context().add_class("action-btn")
        btn.connect("clicked", lambda _, f=fn: f(parent))
        box.pack_start(btn, False, False, 0)

    box.pack_start(Gtk.Separator(), False, False, 10)

    box.pack_start(_section_title("Import"), False, False, 0)

    imp_btn = Gtk.Button(label="Import rice from .tar.gz")
    imp_btn.get_style_context().add_class("action-btn")
    imp_btn.connect("clicked", lambda _: _import_rice(parent))
    box.pack_start(imp_btn, False, False, 0)

    box.pack_start(Gtk.Separator(), False, False, 10)

    box.pack_start(_section_title("Exports folder"), False, False, 0)
    path_lbl = Gtk.Label()
    path_lbl.set_markup(f'<span size="small" font_family="monospace" color="#88c0d0">{EXPORT_DIR}</span>')
    path_lbl.set_xalign(0)
    box.pack_start(path_lbl, False, False, 0)

    open_btn = Gtk.Button(label="Open folder")
    open_btn.connect("clicked", lambda _: subprocess.Popen(["xdg-open", EXPORT_DIR]))
    box.pack_start(open_btn, False, False, 0)

    # Recent exports
    files = sorted(
        [f for f in os.listdir(EXPORT_DIR) if f.endswith(".tar.gz")],
        reverse=True
    )[:10]
    if files:
        box.pack_start(Gtk.Separator(), False, False, 10)
        box.pack_start(_section_title("Recent exports"), False, False, 0)
        for f in files:
            full = os.path.join(EXPORT_DIR, f)
            size_kb = os.path.getsize(full) // 1024
            lbl = Gtk.Label()
            lbl.set_markup(f'<span size="small" font_family="monospace">{f} — {size_kb} KB</span>')
            lbl.set_xalign(0)
            box.pack_start(lbl, False, False, 0)

    return scroll


def _section_title(text):
    lbl = Gtk.Label()
    lbl.set_markup(f'<span size="large" weight="bold">{text}</span>')
    lbl.set_xalign(0)
    lbl.get_style_context().add_class("section-title")
    return lbl


def _export_rice(parent):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(EXPORT_DIR, f"trinity-rice-{ts}.tar.gz")

    configs = [
        ".config/i3",
        ".config/polybar",
        ".config/picom",
        ".config/kitty",
        ".config/rofi",
        ".config/dunst",
        ".config/fish",
        ".config/fastfetch",
        ".config/cava",
        "Documents/trinity-settings",
        "Pictures/wallpapers",
        "dotfiles/themes",
    ]
    existing = [c for c in configs if os.path.exists(os.path.expanduser(f"~/{c}"))]

    try:
        subprocess.run(
            ["tar", "-czf", out, "-C", os.path.expanduser("~")] + existing,
            check=True
        )
        size_mb = os.path.getsize(out) / (1024 * 1024)
        _toast(parent, f"Exported ({size_mb:.1f} MB)")
    except Exception as e:
        _toast(parent, f"Export failed: {e}")


def _export_themes(parent):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(EXPORT_DIR, f"trinity-themes-{ts}.tar.gz")

    src = os.path.expanduser("~/dotfiles/themes")
    if not os.path.isdir(src):
        _toast(parent, "No themes folder")
        return

    try:
        subprocess.run(
            ["tar", "-czf", out, "-C", os.path.expanduser("~/dotfiles"), "themes"],
            check=True
        )
        _toast(parent, "Themes exported")
    except Exception as e:
        _toast(parent, f"Export failed: {e}")


def _export_configs(parent):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(EXPORT_DIR, f"trinity-configs-{ts}.tar.gz")

    configs = ["i3", "polybar", "picom", "kitty", "rofi", "dunst",
               "fish", "fastfetch", "cava"]
    existing = [c for c in configs
                if os.path.isdir(os.path.expanduser(f"~/.config/{c}"))]

    try:
        subprocess.run(
            ["tar", "-czf", out, "-C", os.path.expanduser("~/.config")] + existing,
            check=True
        )
        _toast(parent, "Configs exported")
    except Exception as e:
        _toast(parent, f"Export failed: {e}")


def _import_rice(parent):
    dlg = Gtk.FileChooserDialog(
        title="Import Rice", transient_for=parent,
        action=Gtk.FileChooserAction.OPEN,
    )
    dlg.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Open", Gtk.ResponseType.OK)
    f = Gtk.FileFilter()
    f.set_name("Archives")
    f.add_pattern("*.tar.gz")
    f.add_pattern("*.tgz")
    dlg.add_filter(f)

    if dlg.run() == Gtk.ResponseType.OK:
        path = dlg.get_filename()
        try:
            tmp = tempfile.mkdtemp(prefix="trinity-import-")
            subprocess.run(["tar", "-xzf", path, "-C", tmp], check=True)

            # Backup current
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.expanduser(f"~/.config/trinity-backups/pre-import-{ts}")
            os.makedirs(backup_dir, exist_ok=True)
            for d in ["i3", "polybar", "picom", "kitty", "rofi", "dunst",
                      "fish", "fastfetch", "cava"]:
                src_dir = os.path.expanduser(f"~/.config/{d}")
                if os.path.isdir(src_dir):
                    shutil.copytree(src_dir, os.path.join(backup_dir, d),
                                    dirs_exist_ok=True)

            # Copy files
            copied = 0
            for root, _, files in os.walk(tmp):
                for fn in files:
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, tmp)
                    if rel.startswith((".config/", "dotfiles/",
                                       "Documents/", "Pictures/")):
                        dest = os.path.expanduser(f"~/{rel}")
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        shutil.copy2(full, dest)
                        copied += 1

            shutil.rmtree(tmp)
            _toast(parent, f"Imported {copied} files\nBackup: {backup_dir}")
        except Exception as e:
            _toast(parent, f"Import failed: {e}")
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

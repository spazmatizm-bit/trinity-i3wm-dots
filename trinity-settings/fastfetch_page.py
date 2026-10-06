"""Fastfetch settings."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import os, subprocess

FF_CONF = os.path.expanduser("~/.config/fastfetch/config.jsonc")

def read():
    try: return open(FF_CONF).read()
    except: return ""

def write(c):
    open(FF_CONF, "w").write(c)

def st(t):
    l = Gtk.Label(); l.set_markup(f'<span size="large" weight="bold">{t}</span>')
    l.set_xalign(0); l.get_style_context().add_class("section-title"); return l

def build_page(parent):
    s = Gtk.ScrolledWindow(); s.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14); b.set_border_width(20); s.add(b)

    b.pack_start(st("Fastfetch"), False, False, 0)
    info = Gtk.Label()
    info.set_markup('<span size="small" color="#9c9c9c">System info tool. Opens in terminal.</span>')
    info.set_xalign(0); b.pack_start(info, False, False, 0)

    # Preview
    b.pack_start(st("Preview"), False, False, 10)

    preview = Gtk.TextView()
    preview.set_editable(False)
    preview.set_cursor_visible(False)
    preview.set_monospace(True)
    preview.set_wrap_mode(Gtk.WrapMode.NONE)
    preview.set_size_request(600, 400)          # minimum size
    preview.set_left_margin(10)
    preview.set_right_margin(10)
    preview.set_top_margin(10)
    preview.set_bottom_margin(10)
    preview.get_style_context().add_class("preview")

    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    sw.set_size_request(-1, 400)                # ensure height
    sw.set_min_content_height(350)
    sw.add(preview)
    b.pack_start(sw, False, False, 0)

    def refresh_preview(_=None):
        try:
            out = subprocess.check_output(["fastfetch", "--logo", "none"], timeout=5).decode()
        except Exception as e:
            out = f"(fastfetch not installed: {e})"
        buf = preview.get_buffer()
        buf.set_text(out)

    rb = Gtk.Button(label="Refresh preview"); rb.get_style_context().add_class("action-btn")
    rb.connect("clicked", refresh_preview); b.pack_start(rb, False, False, 0)

    b.pack_start(st("Actions"), False, False, 10)

    def run(cmd):
        subprocess.Popen(["kitty", "--hold", "-e", "bash", "-c", cmd])

    ob = Gtk.Button(label="Open config in editor")
    ob.get_style_context().add_class("action-btn")
    ob.connect("clicked", lambda _: subprocess.Popen(["micro", FF_CONF]))
    b.pack_start(ob, False, False, 0)

    ob2 = Gtk.Button(label="Run fastfetch in terminal")
    ob2.get_style_context().add_class("action-btn")
    ob2.connect("clicked", lambda _: run("fastfetch"))
    b.pack_start(ob2, False, False, 0)

    ob3 = Gtk.Button(label="Generate config from current")
    ob3.get_style_context().add_class("action-btn")
    ob3.connect("clicked", lambda _: run("fastfetch --gen-config-full"))
    b.pack_start(ob3, False, False, 0)

    refresh_preview()

    return s

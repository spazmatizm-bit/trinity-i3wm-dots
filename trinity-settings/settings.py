#!/usr/bin/env python3
"""Trinity Settings — GTK3 control panel for the Trinity i3 rice."""

import gi
from config_utils import i3 as I3, polybar as PB
from apply_mixin import ApplyBar, DeferredSection
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

import subprocess
import os
import re
import shutil
import time
from datetime import datetime

# Theme and export modules
try:
    from themes_page import build_page as build_themes_page
except ImportError:
    build_themes_page = None
try:
    from export_page import build_page as build_export_page
except ImportError:
    build_export_page = None

# New modular pages
try:
    from kitty_page import build_page as build_kitty_page
except ImportError:
    build_kitty_page = None
try:
    from presets_page import build_page as build_presets_page
except ImportError:
    build_presets_page = None
try:
    from rofi_page import build_page as build_rofi_page
except ImportError:
    build_rofi_page = None
try:
    from fish_page import build_page as build_fish_page
except ImportError:
    build_fish_page = None
try:
    from cava_page import build_page as build_cava_page
except ImportError:
    build_cava_page = None
try:
    from fastfetch_page import build_page as build_fastfetch_page
except ImportError:
    build_fastfetch_page = None
try:
    from dunst_page import build_page as build_dunst_page
except ImportError:
    build_dunst_page = None
try:
    from picom_page import build_page as build_picom_page
except ImportError:
    build_picom_page = None


I3_CONF    = os.path.expanduser("~/.config/i3/config")
PICOM_CONF = os.path.expanduser("~/.config/picom/picom.conf")
POLY_CONF  = os.path.expanduser("~/.config/polybar/config.ini")
KITTY_CONF = os.path.expanduser("~/.config/kitty/kitty.conf")
DUNST_CONF = os.path.expanduser("~/.config/dunst/dunstrc")
WALL_DIR   = os.path.expanduser("~/Pictures/wallpapers")
BACKUP_DIR = os.path.expanduser("~/.config/trinity-backups")

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(WALL_DIR, exist_ok=True)


# ============ Config helpers ============

def backup(path):
    if os.path.exists(path):
        name = os.path.basename(path)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            shutil.copy2(path, os.path.join(BACKUP_DIR, f"{name}.{ts}"))
            files = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith(name + ".")], reverse=True)
            for old in files[20:]:
                try: os.remove(os.path.join(BACKUP_DIR, old))
                except Exception: pass
        except Exception:
            pass


def read_file(path):
    try:
        with open(path) as f: return f.read()
    except Exception: return ""


def write_file(path, content, do_backup=True):
    if do_backup: backup(path)
    with open(path, "w") as f: f.write(content)


def get_ini_val(path, key):
    src = read_file(path)
    m = re.search(rf'^\s*{re.escape(key)}\s*=\s*(.+)$', src, re.M)
    if not m: return None
    return m.group(1).strip().rstrip(";").strip().strip('"')


def set_ini_val(path, key, value, do_backup=True):
    src = read_file(path)
    if re.search(rf'^\s*{re.escape(key)}\s*=', src, re.M):
        src = re.sub(rf'^\s*{re.escape(key)}\s*=.*$', f'{key} = {value}', src, flags=re.M)
    else:
        src = src.rstrip() + f'\n{key} = {value}\n'
    write_file(path, src, do_backup)


# ============ Reload hooks ============

def reload_i3():
    if subprocess.run(["i3", "-C", "-c", I3_CONF],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
        subprocess.run(["i3-msg", "reload"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    return False


def reload_picom():
    subprocess.run(["pkill", "picom"], stderr=subprocess.DEVNULL)
    time.sleep(0.3)
    subprocess.Popen(["picom", "--config", PICOM_CONF, "-b"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def reload_polybar():
    # Kill hard — SIGKILL to be sure
    subprocess.run(["pkill", "-9", "polybar"], stderr=subprocess.DEVNULL)
    # Wait until polybar is really gone
    for _ in range(20):
        r = subprocess.run(["pgrep", "-x", "polybar"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            break
        time.sleep(0.1)
    time.sleep(0.2)
    # Launch via launch.sh
    launcher = os.path.expanduser("~/.config/polybar/launch.sh")
    if os.path.exists(launcher):
        subprocess.Popen(["bash", launcher],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    else:
        subprocess.Popen(["polybar", "main"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)


# ============ Color schemes ============

COLORSCHEMES = {
    "nord": {
        "bg": "#2e3440", "fg": "#eceff4", "fg_alt": "#9c9c9c",
        "blue": "#88c0d0", "blue_dim": "#4c566a", "red": "#bf616a",
        "green": "#a3be8c", "yellow": "#ebcb8b", "accent": "#88c0d0",
    },
    "gruvbox": {
        "bg": "#282828", "fg": "#ebdbb2", "fg_alt": "#928374",
        "blue": "#83a598", "blue_dim": "#504945", "red": "#fb4934",
        "green": "#b8bb26", "yellow": "#fabd2f", "accent": "#83a598",
    },
    "catppuccin": {
        "bg": "#1e1e2e", "fg": "#cdd6f4", "fg_alt": "#a6adc8",
        "blue": "#89b4fa", "blue_dim": "#585b70", "red": "#f38ba8",
        "green": "#a6e3a1", "yellow": "#f9e2af", "accent": "#89b4fa",
    },
}


# ============ UI helpers ============

def section_title(text):
    lbl = Gtk.Label()
    lbl.set_markup(f'<span size="large" weight="bold">{text}</span>')
    lbl.set_xalign(0)
    lbl.get_style_context().add_class("section-title")
    return lbl


def make_slider(label, min_v, max_v, step, init, on_change):
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    lbl = Gtk.Label(label=label)
    lbl.set_width_chars(14); lbl.set_xalign(0)
    lbl.get_style_context().add_class("param-label")
    box.pack_start(lbl, False, False, 0)

    scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, min_v, max_v, step)
    scale.set_value(init)
    scale.set_draw_value(True)
    scale.set_value_pos(Gtk.PositionType.RIGHT)
    scale.set_hexpand(True)
    scale.get_style_context().add_class("param-slider")

    def _changed(s):
        if on_change: on_change(s.get_value())

    scale.connect("value-changed", _changed)
    box.pack_start(scale, True, True, 0)
    return box, scale


def make_switch(label, active, on_change):
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    lbl = Gtk.Label(label=label)
    lbl.set_width_chars(20); lbl.set_xalign(0)
    lbl.get_style_context().add_class("param-label")
    box.pack_start(lbl, False, False, 0)

    sw = Gtk.Switch()
    sw.set_active(active)
    sw.connect("notify::active", lambda s, _: on_change(s.get_active()))
    box.pack_end(sw, False, False, 0)
    return box, sw


# ============ Main window ============

def switch_row(label, active, cb):
    """Wrapper: returns only the box (not tuple)."""
    box, _sw = make_switch(label, active, cb)
    return box


class TrinitySettings(Gtk.Window):
    def __init__(self):
        super().__init__(title="Trinity Settings")
        self.set_default_size(1000, 680)
        self.set_size_request(1000, 680)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_name("trinity-settings")
        self.set_resizable(False)
        # Force WM class for i3
        self.set_wmclass("trinity-settings", "TrinitySettings")
        self.set_role("trinity-settings")
        # Prevent i3 from tiling — set as dialog
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)
        # Set stable WM_CLASS BEFORE mapping so i3 can match it
        self.set_wmclass("trinity-settings", "TrinitySettings")
        # Also set role for stubborn WMs
        self.set_role("trinity-settings")

        css_path = os.path.join(os.path.dirname(__file__), "style.css")
        if os.path.exists(css_path):
            p = Gtk.CssProvider()
            p.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), p,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(root)

        # Sidebar
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sidebar.set_size_request(220, -1)
        sidebar.get_style_context().add_class("sidebar")
        # Wrap sidebar in scroller (so it can scroll if too many items)
        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_size_request(220, -1)
        sidebar_scroll.set_hexpand(False)
        sidebar_scroll.set_vexpand(True)
        sidebar_scroll.add(sidebar)
        root.pack_start(sidebar_scroll, False, True, 0)

        title = Gtk.Label()
        title.set_markup('<span size="large" weight="bold">Trinity</span>')
        title.set_xalign(0)
        title.get_style_context().add_class("sidebar-title")
        sidebar.pack_start(title, False, False, 12)

        subtitle = Gtk.Label()
        subtitle.set_markup('<span size="small" color="#88c0d0">Settings</span>')
        subtitle.set_xalign(0)
        sidebar.pack_start(subtitle, False, False, 12)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(150)
        # Wrap content (stack) in scroller
        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_scroll.set_hexpand(True)
        content_scroll.set_vexpand(True)
        content_scroll.add(self.stack)
        root.pack_start(content_scroll, True, True, 0)

        self.sidebar_buttons = {}
        for name, label in [
            ("appearance", "Appearance"),
            ("compositor", "Compositor"),
            ("keybinds",   "Keybindings"),
            ("barmods",    "Bar Modules"),
            ("display",    "Display"),
            ("input",      "Input Devices"),
            ("autostart",  "Autostart"),("rofi","Rofi"),("fish","Fish"),
            ("kitty",      "Kitty"),
            ("cava","Cava"),("fastfetch","Fastfetch"),("dunst","Dunst"),
            ("wallpaper",  "Wallpaper"),
            ("colors",     "Colorscheme"),
            ("presets",    "Presets"),("presets_save","Presets Save/Load"),
            ("themes",     "Themes"),
            ("backup",     "Backup"),
            ("export",     "Export"),
            ("session",    "Session"),
        ]:
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("sidebar-btn")
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.connect("clicked", self._on_sidebar, name)
            sidebar.pack_start(btn, False, False, 0)
            self.sidebar_buttons[name] = btn

        # Build pages
        self.stack.add_named(self._page_appearance(), "appearance")
        if build_picom_page:
            self.stack.add_named(build_picom_page(self), "compositor")
        else:
            self.stack.add_named(self._page_compositor(), "compositor")
        self.stack.add_named(self._page_keybinds(),   "keybinds")
        self.stack.add_named(self._page_barmods(),    "barmods")
        self.stack.add_named(self._page_display(),    "display")
        self.stack.add_named(self._page_input(),      "input")
        self.stack.add_named(self._page_autostart(),  "autostart")
        if build_rofi_page:
            self.stack.add_named(build_rofi_page(self), "rofi")
        if build_fish_page:
            self.stack.add_named(build_fish_page(self), "fish")
        self.stack.add_named(self._page_kitty(),      "kitty")
        if build_cava_page:
            self.stack.add_named(build_cava_page(self), "cava")
        if build_fastfetch_page:
            self.stack.add_named(build_fastfetch_page(self), "fastfetch")
        if build_dunst_page:
            self.stack.add_named(build_dunst_page(self), "dunst")
        self.stack.add_named(self._page_wallpaper(),  "wallpaper")
        self.stack.add_named(self._page_colors(),     "colors")
        self.stack.add_named(self._page_presets(),    "presets")
        if build_presets_page:
            self.stack.add_named(build_presets_page(self), "presets_save")
        if build_themes_page:
            self.stack.add_named(build_themes_page(self), "themes")
        self.stack.add_named(self._page_backup(),     "backup")
        if build_export_page:
            self.stack.add_named(build_export_page(self), "export")
        self.stack.add_named(self._page_session(),    "session")

        self._select("appearance")
        self.connect("key-press-event", self._on_key)
        self.watch_css()


    def watch_css(self):
        """Reload CSS every 2 seconds if the file changed."""
        css_path = os.path.join(os.path.dirname(__file__), "style.css")
        self._last_css_mtime = 0
        try:
            self._last_css_mtime = os.path.getmtime(css_path)
        except Exception:
            pass
        GLib.timeout_add_seconds(2, self._check_css)

    def _check_css(self):
        css_path = os.path.join(os.path.dirname(__file__), "style.css")
        try:
            m = os.path.getmtime(css_path)
            if m > self._last_css_mtime:
                self._last_css_mtime = m
                provider = Gtk.CssProvider()
                provider.load_from_path(css_path)
                Gtk.StyleContext.add_provider_for_screen(
                    Gdk.Screen.get_default(),
                    provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception:
            pass
        return True

    def _on_key(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
            return True
        return False

    def _on_sidebar(self, _, name):
        self._select(name)

    def _select(self, name):
        self.stack.set_visible_child_name(name)
        for k, btn in self.sidebar_buttons.items():
            ctx = btn.get_style_context()
            if k == name: ctx.add_class("active")
            else: ctx.remove_class("active")

    def _scroll(self):
        s = Gtk.ScrolledWindow()
        s.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(20)
        s.add(box)
        return s, box

    # ============ Appearance ============

    def _page_appearance(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(20)
        scroll.add(box)

        def on_apply(pending):
            i3 = I3()
            pb = PB()
            for key, val in pending.items():
                if key == "gaps_inner": i3.set_gaps("inner", val)
                elif key == "gaps_outer": i3.set_gaps("outer", val)
                elif key == "border": i3.set_border(val)
                elif key.startswith("i3_raw:"):
                    _raw_i3_set(key[7:], val)
                elif key.startswith("i3_toggle:"):
                    _raw_i3_toggle(key[10:], val)
                elif key == "bar_height": pb.set("height", val, "bar/main")
                elif key == "bar_radius": pb.set("radius", val, "bar/main")
                elif key == "bar_offset_x": pb.set("offset-x", val, "bar/main")
                elif key == "bar_offset_y": pb.set("offset-y", val, "bar/main")
                elif key == "bar_font":
                    s = read_file(POLY_CONF)
                    s = re.sub(r'(font-0\s*=\s*"[^:]+:size=)\d+', rf'\g<1>{val}', s)
                    s = re.sub(r'(font-1\s*=\s*"[^:]+(?::style=[A-Za-z]+)?:size=)\d+', rf'\g<1>{val}', s)
                    write_file(POLY_CONF, s, do_backup=True)

        def on_reload():
            subprocess.run(["i3-msg", "reload"], stderr=subprocess.DEVNULL)
            reload_polybar()

        section = DeferredSection(on_apply=on_apply, on_reload=on_reload)
        i = I3()
        pb = PB()

        title = Gtk.Label()
        title.set_markup('<span size="x-large" weight="bold">Appearance</span>')
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)

        info = Gtk.Label()
        info.set_markup('<span size="small" color="#9c9c9c">Gaps, borders, i3 behavior, client colors, bar.</span>')
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)

        # ==== Gaps ====
        box.pack_start(section_title("Gaps"), False, False, 10)
        r, _ = make_slider("Inner gaps", 0, 40, 1, i.get_gaps("inner") or 8,
                           lambda v: section.set("gaps_inner", int(v)))
        box.pack_start(r, False, False, 0)
        r, _ = make_slider("Outer gaps", 0, 40, 1, i.get_gaps("outer") or 4,
                           lambda v: section.set("gaps_outer", int(v)))
        box.pack_start(r, False, False, 0)

        box.pack_start(switch_row("Smart gaps (no gaps with 1 window)",
            "smart_gaps on" in read_file(I3_CONF),
            lambda v: section.set("i3_toggle:smart_gaps on", v)), False, False, 0)

        box.pack_start(switch_row("Smart borders",
            "smart_borders on" in read_file(I3_CONF),
            lambda v: section.set("i3_toggle:smart_borders on", v)), False, False, 0)

        # ==== Border ====
        box.pack_start(section_title("Border width"), False, False, 10)
        r, _ = make_slider("Pixel width", 0, 10, 1, i.get_border(),
                           lambda v: section.set("border", int(v)))
        box.pack_start(r, False, False, 0)

        # ==== i3 Behavior ====
        box.pack_start(section_title("i3 behavior"), False, False, 10)

        box.pack_start(switch_row("Focus follows mouse",
            "focus_follows_mouse yes" in read_file(I3_CONF),
            lambda v: section.set("i3_raw:focus_follows_mouse", "yes" if v else "no")), False, False, 0)

        # Mouse warping
        r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        l = Gtk.Label(label="Mouse warping")
        l.set_width_chars(22); l.set_xalign(0)
        l.get_style_context().add_class("param-label")
        r.pack_start(l, False, False, 0)
        combo = Gtk.ComboBoxText()
        for opt in ["none", "output", "container"]: combo.append_text(opt)
        m2 = re.search(r'^mouse_warping (\w+)', read_file(I3_CONF), re.M)
        cur = m2.group(1) if m2 else "output"
        if cur in ["none", "output", "container"]:
            combo.set_active(["none", "output", "container"].index(cur))
        combo.connect("changed", lambda c: section.set("i3_raw:mouse_warping", c.get_active_text()))
        r.pack_start(combo, True, True, 0)
        box.pack_start(r, False, False, 0)

        # Workspace layout
        r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        l = Gtk.Label(label="Workspace layout")
        l.set_width_chars(22); l.set_xalign(0)
        l.get_style_context().add_class("param-label")
        r.pack_start(l, False, False, 0)
        combo = Gtk.ComboBoxText()
        for opt in ["splith", "splitv", "tabbed", "stacking"]: combo.append_text(opt)
        m3 = re.search(r'^workspace_layout (\w+)', read_file(I3_CONF), re.M)
        cur = m3.group(1) if m3 else "splith"
        if cur in ["splith", "splitv", "tabbed", "stacking"]:
            combo.set_active(["splith","splitv","tabbed","stacking"].index(cur))
        combo.connect("changed", lambda c: section.set("i3_raw:workspace_layout", c.get_active_text()))
        r.pack_start(combo, True, True, 0)
        box.pack_start(r, False, False, 0)

        # i3 font
        r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        l = Gtk.Label(label="i3 font")
        l.set_width_chars(22); l.set_xalign(0)
        l.get_style_context().add_class("param-label")
        r.pack_start(l, False, False, 0)
        entry = Gtk.Entry()
        m4 = re.search(r'^font (.+)$', read_file(I3_CONF), re.M)
        entry.set_text(m4.group(1).strip() if m4 else "pango:JetBrainsMono Nerd Font 10")
        entry.set_hexpand(True)
        entry.connect("changed", lambda w: section.set("i3_raw:font", w.get_text()))
        r.pack_start(entry, True, True, 0)
        box.pack_start(r, False, False, 0)

        # ==== Client colors ====
        box.pack_start(section_title("Client colors (i3)"), False, False, 10)
        for label, key in [
            ("Focused", "client.focused"),
            ("Focused inactive", "client.focused_inactive"),
            ("Unfocused", "client.unfocused"),
            ("Urgent", "client.urgent"),
            ("Placeholder", "client.placeholder"),
        ]:
            m5 = re.search(rf'^{re.escape(key)}\s+(.+)$', read_file(I3_CONF), re.M)
            val = m5.group(1).strip() if m5 else ""
            r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            l = Gtk.Label(label=label)
            l.set_width_chars(22); l.set_xalign(0)
            l.get_style_context().add_class("param-label")
            r.pack_start(l, False, False, 0)
            e = Gtk.Entry(); e.set_text(val); e.set_hexpand(True)
            e.connect("changed", lambda w, k=key: section.set(f"i3_raw:{k}", w.get_text()))
            r.pack_start(e, True, True, 0)
            box.pack_start(r, False, False, 0)

        # ==== Polybar bar ====
        box.pack_start(section_title("Polybar bar"), False, False, 10)

        v = pb.get("height", "bar/main") or "24"
        r, _ = make_slider("Bar height (px)", 16, 60, 1, int(v) if v.isdigit() else 24,
                           lambda v: section.set("bar_height", str(int(v))))
        box.pack_start(r, False, False, 0)

        v = pb.get("radius", "bar/main") or "0"
        r, _ = make_slider("Bar corner radius", 0, 30, 1, int(v) if v.isdigit() else 0,
                           lambda v: section.set("bar_radius", str(int(v))))
        box.pack_start(r, False, False, 0)

        v = pb.get("offset-x", "bar/main") or "0"
        r, _ = make_slider("Bar offset X", 0, 500, 5, int(v) if v.isdigit() else 0,
                           lambda v: section.set("bar_offset_x", str(int(v))))
        box.pack_start(r, False, False, 0)

        v = pb.get("offset-y", "bar/main") or "0"
        r, _ = make_slider("Bar offset Y", 0, 100, 1, int(v) if v.isdigit() else 0,
                           lambda v: section.set("bar_offset_y", str(int(v))))
        box.pack_start(r, False, False, 0)

        m6 = re.search(r'^font-0\s*=\s*"[^:]+:size=(\d+)', read_file(POLY_CONF), re.M)
        v = int(m6.group(1)) if m6 else 10
        r, _ = make_slider("Bar font size", 6, 20, 1, v,
                           lambda v: section.set("bar_font", int(v)))
        box.pack_start(r, False, False, 0)

        # ==== Apply ====
        bar = ApplyBar(on_apply=section.apply, on_reset=section.reset)
        section.attach_bar(bar)
        box.pack_start(Gtk.Separator(), False, False, 10)
        box.pack_start(bar, False, False, 0)

        return scroll

    def _apply_gaps(self, _):
        inner = int(self.inner_scale.get_value())
        outer = int(self.outer_scale.get_value())
        subprocess.run(["i3-msg", f"gaps inner all set {inner}"], stderr=subprocess.DEVNULL)
        subprocess.run(["i3-msg", f"gaps outer all set {outer}"], stderr=subprocess.DEVNULL)
        src = read_file(I3_CONF)
        src = re.sub(r'^gaps inner \d+', f'gaps inner {inner}', src, flags=re.M)
        src = re.sub(r'^gaps outer \d+', f'gaps outer {outer}', src, flags=re.M)
        if not re.search(r'^gaps inner', src, re.M): src += f'\ngaps inner {inner}\n'
        if not re.search(r'^gaps outer', src, re.M): src += f'gaps outer {outer}\n'
        with open(I3_CONF, "w") as f: f.write(src)

    def _apply_border(self, _):
        px = int(self.border_scale.get_value())
        src = read_file(I3_CONF)
        src = re.sub(r'^default_border .*', f'default_border pixel {px}', src, flags=re.M)
        src = re.sub(r'^default_floating_border .*', f'default_floating_border pixel {px}', src, flags=re.M)
        if not re.search(r'^default_border ', src, re.M):
            src += f'\ndefault_border pixel {px}\n'
        if not re.search(r'^default_floating_border ', src, re.M):
            src += f'default_floating_border pixel {px}\n'
        with open(I3_CONF, "w") as f: f.write(src)
        subprocess.run(["i3-msg", "reload"], stderr=subprocess.DEVNULL)

    def _apply_bar_height(self, _):
        h = int(self.bar_scale.get_value())
        set_ini_val(POLY_CONF, "height", str(h), do_backup=False)
        reload_polybar()

    def _apply_font_size(self, _):
        s = int(self.font_scale.get_value())
        src = read_file(POLY_CONF)
        src = re.sub(r'(font-0\s*=\s*"[^:]+:size=)\d+', rf'\g<1>{s}', src)
        src = re.sub(r'(font-1\s*=\s*"[^:]+(?::style=[A-Za-z]+)?:size=)\d+', rf'\g<1>{s}', src)
        write_file(POLY_CONF, src, do_backup=False)
        reload_polybar()

    # ============ Compositor ============

    def _page_compositor(self):
        scroll, box = self._scroll()

        box.pack_start(section_title("Blur"), False, False, 0)
        row, self.blur_switch = make_switch(
            "Enable blur", self._blur_enabled(), self._apply_blur_toggle)
        box.pack_start(row, False, False, 0)

        cur = self._picom_blur_strength()
        row, self.strength_scale = make_slider(
            "Blur strength", 1, 15, 1, cur, self._apply_blur_strength)
        box.pack_start(row, False, False, 0)

        box.pack_start(section_title("Shadows"), False, False, 10)
        row, self.shadow_switch = make_switch(
            "Enable shadows",
            get_ini_val(PICOM_CONF, "shadow") == "true",
            self._apply_shadow_toggle)
        box.pack_start(row, False, False, 0)

        box.pack_start(section_title("Rounded corners"), False, False, 10)
        v = get_ini_val(PICOM_CONF, "corner-radius")
        cur = int(v) if v and v.isdigit() else 8
        row, self.radius_scale = make_slider(
            "Corner radius", 0, 30, 1, cur, self._apply_corner_radius)
        box.pack_start(row, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 10)
        btn = Gtk.Button(label="Restart Picom")
        btn.get_style_context().add_class("action-btn")
        btn.connect("clicked", lambda _: reload_picom())
        box.pack_start(btn, False, False, 0)

        return scroll

    def _apply_blur_toggle(self, active):
        src = read_file(PICOM_CONF)
        if active:
            if not re.search(r'^\s*blur\s*\{', src, re.M):
                src = src.rstrip() + '''

blur {
  method = "dual_kawase";
  strength = 4;
};
blur-background-exclude = [
  "window_type = 'dock'",
  "window_type = 'desktop'"
];
'''
        else:
            src = re.sub(r'\n?blur\s*\{[^}]*\}\s*;?\s*', '\n', src)
            src = re.sub(r'\n?blur-background-exclude\s*=\s*\[[^\]]*\];?\s*', '\n', src)
        write_file(PICOM_CONF, src)
        reload_picom()

    def _apply_blur_strength(self, _):
        s = int(self.strength_scale.get_value())
        src = read_file(PICOM_CONF)
        if re.search(r'strength\s*=\s*\d+', src):
            src = re.sub(r'strength\s*=\s*\d+', f'strength = {s}', src)
            write_file(PICOM_CONF, src, do_backup=False)
            reload_picom()

    def _apply_shadow_toggle(self, active):
        set_ini_val(PICOM_CONF, "shadow", "true" if active else "false")
        reload_picom()

    def _apply_corner_radius(self, _):
        r = int(self.radius_scale.get_value())
        set_ini_val(PICOM_CONF, "corner-radius", str(r), do_backup=False)
        reload_picom()

    def _blur_enabled(self):
        return bool(re.search(r'^\s*blur\s*\{', read_file(PICOM_CONF), re.M))

    def _picom_blur_strength(self):
        m = re.search(r'strength\s*=\s*(\d+)', read_file(PICOM_CONF))
        return int(m.group(1)) if m else 4


    # ============ Keybindings editor ============

    def _parse_binds(self):
        """Return list of (bind, command) tuples from i3 config."""
        src = read_file(I3_CONF)
        binds = []
        for line in src.splitlines():
            m = re.match(r'^\s*bindsym\s+(--release\s+)?(\S+)\s+(.*)$', line)
            if m:
                binds.append((m.group(2), m.group(3).strip()))
        return binds

    def _page_keybinds(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(20)
        scroll.add(box)

        box.pack_start(section_title("Keybindings"), False, False, 0)

        # Search row
        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        search_lbl = Gtk.Label(label="Search:")
        search_lbl.get_style_context().add_class("param-label")
        search_row.pack_start(search_lbl, False, False, 0)
        self.kb_search = Gtk.SearchEntry()
        self.kb_search.set_hexpand(True)
        self.kb_search.connect("search-changed", self._filter_keybinds)
        search_row.pack_start(self.kb_search, True, True, 0)
        box.pack_start(search_row, False, False, 0)

        # Add button
        add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        add_btn = Gtk.Button(label="+ Add new binding")
        add_btn.get_style_context().add_class("action-btn")
        add_btn.connect("clicked", self._kb_add)
        add_row.pack_start(add_btn, False, False, 0)
        box.pack_start(add_row, False, False, 0)

        # TreeView with columns
        self.kb_store = Gtk.ListStore(str, str, int)  # bind, command, line_index
        for bind, cmd in self._parse_binds():
            self.kb_store.append([bind, cmd, 0])

        self.kb_filter = self.kb_store.filter_new()
        self.kb_filter.set_visible_func(self._kb_visible)

        tree = Gtk.TreeView(model=self.kb_filter)
        tree.set_headers_visible(True)
        tree.set_enable_search(True)

        # Column: bind
        r1 = Gtk.CellRendererText()
        r1.set_property("editable", False)
        c1 = Gtk.TreeViewColumn("Key", r1, text=0)
        c1.set_min_width(180)
        c1.set_sort_column_id(0)
        tree.append_column(c1)

        # Column: command
        r2 = Gtk.CellRendererText()
        r2.set_property("editable", False)
        c2 = Gtk.TreeViewColumn("Command", r2, text=1)
        c2.set_min_width(400)
        c2.set_sort_column_id(1)
        tree.append_column(c2)

        # Double-click to edit
        tree.connect("row-activated", self._kb_edit)

        # Right-click menu
        tree.connect("button-press-event", self._kb_button_press)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(tree)
        sw.set_size_request(-1, 400)
        box.pack_start(sw, True, True, 0)

        # Hint
        hint = Gtk.Label()
        hint.set_markup('<span size="small" color="#9c9c9c">Double-click to edit · Right-click to delete · Changes saved to i3 config</span>')
        hint.set_xalign(0)
        box.pack_start(hint, False, False, 0)

        self.kb_tree = tree
        return scroll

    def _kb_visible(self, model, iter, _):
        q = self.kb_search.get_text().lower()
        if not q: return True
        return q in model[iter][0].lower() or q in model[iter][1].lower()

    def _filter_keybinds(self, _):
        self.kb_filter.refilter()

    def _kb_button_press(self, tree, event):
        if event.button == 3:  # right click
            path_info = tree.get_path_at_pos(int(event.x), int(event.y))
            if not path_info: return False
            path = path_info[0]
            tree.get_selection().select_path(path)
            menu = Gtk.Menu()
            del_item = Gtk.MenuItem(label="Delete binding")
            del_item.connect("activate", self._kb_delete, path)
            menu.append(del_item)
            edit_item = Gtk.MenuItem(label="Edit command")
            edit_item.connect("activate", lambda _: self._kb_edit(tree, path, None))
            menu.append(edit_item)
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        return False

    def _kb_add(self, _):
        dialog = Gtk.Dialog(title="Add Binding", transient_for=self, flags=0)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)
        dialog.set_default_size(450, 200)
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_border_width(15)

        content.add(Gtk.Label(label="Key (e.g. $mod+Shift+t):", xalign=0))
        key_entry = Gtk.Entry()
        content.add(key_entry)

        content.add(Gtk.Label(label="Command (e.g. exec alacritty):", xalign=0))
        cmd_entry = Gtk.Entry()
        content.add(cmd_entry)

        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            key = key_entry.get_text().strip()
            cmd = cmd_entry.get_text().strip()
            if key and cmd:
                src = read_file(I3_CONF)
                src = src.rstrip() + f'\nbindsym {key} {cmd}\n'
                write_file(I3_CONF, src)
                self.kb_store.append([key, cmd, 0])
                subprocess.run(["i3-msg", "reload"], stderr=subprocess.DEVNULL)
                self._toast(f"Added: {key}")
        dialog.destroy()

    def _kb_edit(self, tree, path, _):
        # Convert filter path to store path
        filter_iter = self.kb_filter.get_iter(path)
        store_iter = self.kb_filter.convert_iter_to_child_iter(filter_iter)
        old_key = self.kb_store.get_value(store_iter, 0)
        old_cmd = self.kb_store.get_value(store_iter, 1)

        dialog = Gtk.Dialog(title="Edit Binding", transient_for=self, flags=0)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)
        dialog.set_default_size(450, 200)
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_border_width(15)

        content.add(Gtk.Label(label="Key:", xalign=0))
        key_entry = Gtk.Entry()
        key_entry.set_text(old_key)
        content.add(key_entry)

        content.add(Gtk.Label(label="Command:", xalign=0))
        cmd_entry = Gtk.Entry()
        cmd_entry.set_text(old_cmd)
        content.add(cmd_entry)

        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            new_key = key_entry.get_text().strip()
            new_cmd = cmd_entry.get_text().strip()
            if new_key and new_cmd:
                # Update config file
                src = read_file(I3_CONF)
                src = re.sub(
                    rf'^\s*bindsym\s+(--release\s+)?{re.escape(old_key)}\s+.*$',
                    f'bindsym {new_key} {new_cmd}',
                    src, flags=re.M)
                write_file(I3_CONF, src)
                # Update model
                self.kb_store.set_value(store_iter, 0, new_key)
                self.kb_store.set_value(store_iter, 1, new_cmd)
                subprocess.run(["i3-msg", "reload"], stderr=subprocess.DEVNULL)
                self._toast(f"Updated: {new_key}")
        dialog.destroy()

    def _kb_delete(self, _, path):
        filter_iter = self.kb_filter.get_iter(path)
        store_iter = self.kb_filter.convert_iter_to_child_iter(filter_iter)
        key = self.kb_store.get_value(store_iter, 0)
        cmd = self.kb_store.get_value(store_iter, 1)

        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete binding?",
        )
        dialog.format_secondary_text(f"{key} → {cmd}")
        resp = dialog.run()
        dialog.destroy()
        if resp != Gtk.ResponseType.YES:
            return

        src = read_file(I3_CONF)
        src = re.sub(
            rf'^\s*bindsym\s+(--release\s+)?{re.escape(key)}\s+{re.escape(cmd)}\s*$',
            '', src, flags=re.M)
        write_file(I3_CONF, src)
        self.kb_store.remove(store_iter)
        subprocess.run(["i3-msg", "reload"], stderr=subprocess.DEVNULL)
        self._toast(f"Deleted: {key}")

    # ============ Bar modules ============

    def _parse_polybar_modules(self, position):
        """Return list of module names for given position (left/center/right)."""
        src = read_file(POLY_CONF)
        m = re.search(rf'^modules-{position}\s*=\s*(.*)$', src, re.M)
        if not m: return []
        return m.group(1).split()

    ALL_MODULES = [
        "i3", "date", "volume", "cpu", "memory", "pulseaudio",
        "battery", "network", "systray", "music-ctl", "music-status",
        "now-playing", "xkeyboard", "tray",
    ]

    def _page_barmods(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(20)
        scroll.add(box)

        box.pack_start(section_title("Bar Modules"), False, False, 0)

        info = Gtk.Label()
        info.set_markup('<span size="small" color="#9c9c9c">Toggle modules on/off. Changes apply instantly.</span>')
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)

        self.barmod_switches = {}
        for position in ["left", "center", "right"]:
            box.pack_start(section_title(position.capitalize()), False, False, 8)
            active = self._parse_polybar_modules(position)
            for mod in self.ALL_MODULES:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                lbl = Gtk.Label(label=mod)
                lbl.set_width_chars(20); lbl.set_xalign(0)
                lbl.get_style_context().add_class("param-label")
                row.pack_start(lbl, False, False, 0)
                sw = Gtk.Switch()
                sw.set_active(mod in active)
                sw.connect("notify::active", self._apply_barmods)
                row.pack_end(sw, False, False, 0)
                box.pack_start(row, False, False, 0)
                self.barmod_switches[f"{position}:{mod}"] = sw

        return scroll

    def _apply_barmods(self, _):
        src = read_file(POLY_CONF)
        for position in ["left", "center", "right"]:
            mods = []
            for mod in self.ALL_MODULES:
                sw = self.barmod_switches.get(f"{position}:{mod}")
                if sw and sw.get_active():
                    mods.append(mod)
            line = f'modules-{position} = {" ".join(mods)}'
            if re.search(rf'^modules-{position}\s*=', src, re.M):
                src = re.sub(rf'^modules-{position}\s*=.*$', line, src, flags=re.M)
            else:
                src += f'\n{line}\n'
        write_file(POLY_CONF, src, do_backup=False)
        reload_polybar()


    # ============ Display &amp; Monitor ============

    def _page_display(self):
        scroll, box = self._scroll()
        box.pack_start(section_title("Display &amp; Monitor"), False, False, 0)

        info = Gtk.Label()
        info.set_markup('<span size="small" color="#9c9c9c">Set resolution, refresh rate, position, rotation.</span>')
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)

        # Get monitors
        try:
            out = subprocess.check_output(["xrandr", "--query"], stderr=subprocess.DEVNULL).decode()
        except Exception:
            out = ""

        monitors = []
        for line in out.splitlines():
            if " connected" in line:
                name = line.split()[0]
                monitors.append(name)

        if not monitors:
            box.pack_start(Gtk.Label(label="No monitors detected"), False, False, 10)
            return scroll

        # For each monitor
        for mon in monitors:
            box.pack_start(section_title(mon), False, False, 10)

            # Get modes
            modes = []
            for line in out.splitlines():
                if line.startswith("  ") and "x" in line.split()[0]:
                    res = line.split()[0]
                    rates = re.findall(r'(\d+\.\d+|\d+)', line)
                    if rates:
                        for r in rates[:6]:
                            modes.append((res, r))

            # Resolution selector
            res_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            res_lbl = Gtk.Label(label="Resolution"); res_lbl.set_width_chars(14); res_lbl.set_xalign(0)
            res_lbl.get_style_context().add_class("param-label")
            res_row.pack_start(res_lbl, False, False, 0)

            res_combo = Gtk.ComboBoxText()
            current_res = "1920x1080"
            for res, _ in modes:
                if res not in [res_combo.get_active_text()]:
                    res_combo.append_text(res)
            # Find current
            for line in out.splitlines():
                if line.startswith(mon):
                    m = re.search(r'(\d+x\d+)', line)
                    if m:
                        current_res = m.group(1)
                        break
            res_combo.set_active(0)
            for i, (res, _) in enumerate(modes):
                if res == current_res:
                    res_combo.set_active(i)
                    break
            res_combo.connect("changed", self._apply_display, mon)
            res_row.pack_start(res_combo, True, True, 0)
            box.pack_start(res_row, False, False, 0)

            # Refresh rate
            rate_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            rate_lbl = Gtk.Label(label="Refresh rate"); rate_lbl.set_width_chars(14); rate_lbl.set_xalign(0)
            rate_lbl.get_style_context().add_class("param-label")
            rate_row.pack_start(rate_lbl, False, False, 0)

            rates_set = set()
            for res, r in modes:
                if res == current_res:
                    try:
                        f = float(r)
                        if 30 <= f <= 500:   # valid refresh rate range
                            rates_set.add(f"{f:.0f}" if f == int(f) else f"{f:.2f}")
                    except ValueError:
                        pass
            rates_sorted = sorted(rates_set, key=lambda x: -float(x))

            rate_combo = Gtk.ComboBoxText()
            for r in rates_sorted:
                rate_combo.append_text(r)
            if rates_sorted:
                rate_combo.set_active(0)
            rate_combo.connect("changed", self._apply_display, mon)
            rate_row.pack_start(rate_combo, True, True, 0)
            box.pack_start(rate_row, False, False, 0)

            # Rotation
            rot_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            rot_lbl = Gtk.Label(label="Rotation"); rot_lbl.set_width_chars(14); rot_lbl.set_xalign(0)
            rot_lbl.get_style_context().add_class("param-label")
            rot_row.pack_start(rot_lbl, False, False, 0)

            rot_combo = Gtk.ComboBoxText()
            for r in ["normal", "left", "right", "inverted"]:
                rot_combo.append_text(r)
            rot_combo.set_active(0)
            rot_combo.connect("changed", self._apply_display, mon)
            rot_row.pack_start(rot_combo, True, True, 0)
            box.pack_start(rot_row, False, False, 0)

            # Apply button per monitor
            apply_btn = Gtk.Button(label=f"Apply {mon}")
            apply_btn.get_style_context().add_class("action-btn")
            apply_btn.connect("clicked", lambda _, m=mon: self._save_display_config(m))
            box.pack_start(apply_btn, False, False, 8)

        return scroll

    def _apply_display(self, combo, mon):
        # Live preview: apply current selections for this monitor
        # Find the monitor box
        pass

    def _save_display_config(self, mon):
        # Persist xrandr line to i3 config
        # Get current xrandr output for this monitor
        try:
            out = subprocess.check_output(["xrandr", "--query"], stderr=subprocess.DEVNULL).decode()
        except Exception:
            return
        # Extract current mode
        mode = "1920x1080"
        rate = "60"
        for line in out.splitlines():
            if line.startswith(mon):
                m = re.search(r'(\d+x\d+)', line)
                if m: mode = m.group(1)
                # find rate marked with *
                for r in re.findall(r'(\d+\.\d+|\d+)\*', line):
                    rate = r
                break
        line = f"exec --no-startup-id xrandr --output {mon} --mode {mode} --rate {rate}"
        src = read_file(I3_CONF)
        src = re.sub(rf'^exec --no-startup-id xrandr --output {mon}.*$', '', src, flags=re.M)
        src = src.rstrip() + f'\n{line}\n'
        write_file(I3_CONF, src)
        self._toast(f"Saved display config for {mon}")

    # ============ Input Devices ============

    def _page_input(self):
        scroll, box = self._scroll()
        box.pack_start(section_title("Input Devices"), False, False, 0)

        # Keyboard repeat
        box.pack_start(section_title("Keyboard repeat"), False, False, 8)

        try:
            out = subprocess.check_output(["xset", "q"], stderr=subprocess.DEVNULL).decode()
            m_delay = re.search(r'repeat delay:\s*(\d+)', out)
            m_rate = re.search(r'repeat rate:\s*(\d+)', out)
            cur_delay = int(m_delay.group(1)) if m_delay else 660
            cur_rate = int(m_rate.group(1)) if m_rate else 25
        except Exception:
            cur_delay, cur_rate = 660, 25

        row, self.kb_delay = make_slider("Delay (ms)", 100, 1000, 10, cur_delay, self._apply_keyboard)
        box.pack_start(row, False, False, 0)
        row, self.kb_rate = make_slider("Rate (Hz)", 10, 100, 1, cur_rate, self._apply_keyboard)
        box.pack_start(row, False, False, 0)

        # Mouse
        box.pack_start(section_title("Mouse"), False, False, 10)

        try:
            out = subprocess.check_output(["xset", "q"], stderr=subprocess.DEVNULL).decode()
            m = re.search(r'Mouse Control:\s*accel\s*(\d+)/\d+', out)
            cur_accel = int(m.group(1)) if m else 2
        except Exception:
            cur_accel = 2

        row, self.mouse_accel = make_slider("Accel", 1, 10, 1, cur_accel, self._apply_mouse)
        box.pack_start(row, False, False, 0)

        # Keyboard layout
        box.pack_start(section_title("Keyboard layout"), False, False, 10)

        layout_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ll = Gtk.Label(label="Layouts"); ll.set_width_chars(14); ll.set_xalign(0)
        ll.get_style_context().add_class("param-label")
        layout_row.pack_start(ll, False, False, 0)

        self.layout_entry = Gtk.Entry()
        try:
            q = subprocess.check_output(["setxkbmap", "-query"], stderr=subprocess.DEVNULL).decode()
            m = re.search(r'layout:\s*(.+)', q)
            self.layout_entry.set_text(m.group(1).strip() if m else "us,ru")
        except Exception:
            self.layout_entry.set_text("us,ru")
        layout_row.pack_start(self.layout_entry, True, True, 0)

        apply_layout = Gtk.Button(label="Apply")
        apply_layout.connect("clicked", self._apply_layout)
        layout_row.pack_start(apply_layout, False, False, 0)
        box.pack_start(layout_row, False, False, 0)

        # Grp toggle
        grp_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        gl = Gtk.Label(label="Switch key"); gl.set_width_chars(14); gl.set_xalign(0)
        gl.get_style_context().add_class("param-label")
        grp_row.pack_start(gl, False, False, 0)

        self.grp_combo = Gtk.ComboBoxText()
        for opt in ["grp:alt_shift_toggle", "grp:caps_toggle", "grp:ctrl_shift_toggle"]:
            self.grp_combo.append_text(opt)
        self.grp_combo.set_active(0)
        grp_row.pack_start(self.grp_combo, True, True, 0)

        apply_grp = Gtk.Button(label="Apply")
        apply_grp.connect("clicked", self._apply_layout)
        grp_row.pack_start(apply_grp, False, False, 0)
        box.pack_start(grp_row, False, False, 0)

        return scroll

    def _apply_keyboard(self, _):
        delay = int(self.kb_delay.get_value())
        rate = int(self.kb_rate.get_value())
        subprocess.run(["xset", "r", "rate", str(delay), str(rate)],
                       stderr=subprocess.DEVNULL)
        # Persist
        src = read_file(I3_CONF)
        src = re.sub(r'^exec --no-startup-id xset r rate.*$', '', src, flags=re.M)
        src = src.rstrip() + f'\nexec --no-startup-id xset r rate {delay} {rate}\n'
        write_file(I3_CONF, src)

    def _apply_mouse(self, _):
        a = int(self.mouse_accel.get_value())
        subprocess.run(["xset", "m", str(a), "2"], stderr=subprocess.DEVNULL)

    def _apply_layout(self, _):
        layouts = self.layout_entry.get_text().strip()
        grp = self.grp_combo.get_active_text() or "grp:alt_shift_toggle"
        subprocess.run(["setxkbmap", "-layout", layouts, "-option", grp],
                       stderr=subprocess.DEVNULL)
        # Persist
        src = read_file(I3_CONF)
        src = re.sub(r'^exec --no-startup-id setxkbmap.*$', '', src, flags=re.M)
        src = src.rstrip() + f'\nexec --no-startup-id setxkbmap -layout {layouts} -option {grp}\n'
        write_file(I3_CONF, src)
        self._toast(f"Layout: {layouts} ({grp})")

    # ============ Autostart Manager ============

    def _parse_autostart(self):
        """Return list of exec lines (without --no-startup-id prefix)."""
        src = read_file(I3_CONF)
        entries = []
        for line in src.splitlines():
            m = re.match(r'^exec(_always)?\s+(--no-startup-id\s+)?(.*)$', line)
            if m:
                entries.append((line, m.group(3).strip()))
        return entries

    def _page_autostart(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(20)
        scroll.add(box)

        box.pack_start(section_title("Autostart"), False, False, 0)

        info = Gtk.Label()
        info.set_markup('<span size="small" color="#9c9c9c">Toggle startup commands from your i3 config.</span>')
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)

        self.autostart_switches = {}
        for line, cmd in self._parse_autostart():
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            lbl = Gtk.Label(label=cmd[:60] + ("..." if len(cmd) > 60 else ""))
            lbl.set_xalign(0)
            lbl.set_ellipsize(3)
            lbl.get_style_context().add_class("param-label")
            row.pack_start(lbl, True, True, 0)

            sw = Gtk.Switch()
            sw.set_active(True)  # active = line exists uncommented
            sw.connect("notify::active", self._apply_autostart, line, cmd)
            row.pack_end(sw, False, False, 0)
            box.pack_start(row, False, False, 0)

        return scroll

    def _apply_autostart(self, sw, line, cmd):
        active = sw.get_active()
        src = read_file(I3_CONF)
        if active:
            # Uncomment if commented
            if line.startswith("#"):
                src = src.replace(line, line[1:].strip())
        else:
            # Comment out
            if not line.startswith("#"):
                src = src.replace(line, "# " + line)
        write_file(I3_CONF, src, do_backup=False)
        subprocess.run(["i3-msg", "reload"], stderr=subprocess.DEVNULL)

    # ============ Kitty ============

    def _page_kitty(self):
        scroll, box = self._scroll()

        box.pack_start(section_title("Kitty terminal"), False, False, 0)

        # Font family
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl = Gtk.Label(label="Font"); lbl.set_width_chars(14); lbl.set_xalign(0)
        lbl.get_style_context().add_class("param-label")
        row.pack_start(lbl, False, False, 0)
        self.kitty_font = Gtk.Entry()
        v = get_ini_val(KITTY_CONF, "font_family") or "monospace"
        self.kitty_font.set_text(v)
        self.kitty_font.set_hexpand(True)
        self.kitty_font.connect("activate", self._apply_kitty_font)
        row.pack_start(self.kitty_font, True, True, 0)
        btn = Gtk.Button(label="Apply")
        btn.connect("clicked", self._apply_kitty_font)
        row.pack_start(btn, False, False, 0)
        box.pack_start(row, False, False, 0)

        # Font size
        box.pack_start(section_title("Font size"), False, False, 8)
        v = get_ini_val(KITTY_CONF, "font_size")
        cur = int(float(v)) if v else 11
        row, self.kitty_size = make_slider("Font size", 6, 24, 1, cur, self._apply_kitty_size)
        box.pack_start(row, False, False, 0)

        # Opacity
        box.pack_start(section_title("Background opacity"), False, False, 8)
        v = get_ini_val(KITTY_CONF, "background_opacity")
        cur = int(float(v) * 100) if v else 95
        row, self.kitty_opacity = make_slider("Opacity (%)", 50, 100, 1, cur, self._apply_kitty_opacity)
        box.pack_start(row, False, False, 0)

        # Padding
        box.pack_start(section_title("Padding"), False, False, 8)
        v = get_ini_val(KITTY_CONF, "window_padding_width")
        cur = int(v) if v and v.isdigit() else 8
        row, self.kitty_padding = make_slider("Padding (px)", 0, 40, 1, cur, self._apply_kitty_padding)
        box.pack_start(row, False, False, 0)

        # Cursor shape
        box.pack_start(section_title("Cursor shape"), False, False, 8)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl = Gtk.Label(label="Shape"); lbl.set_width_chars(14); lbl.set_xalign(0)
        lbl.get_style_context().add_class("param-label")
        row.pack_start(lbl, False, False, 0)
        self.kitty_cursor = Gtk.ComboBoxText()
        for shape in ["block", "beam", "underline"]:
            self.kitty_cursor.append_text(shape)
        v = get_ini_val(KITTY_CONF, "cursor_shape") or "block"
        idx = ["block", "beam", "underline"].index(v) if v in ["block", "beam", "underline"] else 0
        self.kitty_cursor.set_active(idx)
        self.kitty_cursor.connect("changed", self._apply_kitty_cursor)
        row.pack_start(self.kitty_cursor, False, False, 0)
        box.pack_start(row, False, False, 0)

        # Hide tab bar
        row, self.kitty_tabbar = make_switch(
            "Hide window decorations",
            get_ini_val(KITTY_CONF, "hide_window_decorations") == "yes",
            self._apply_kitty_tabbar,
        )
        box.pack_start(row, False, False, 8)

        # Audio bell
        row, self.kitty_bell = make_switch(
            "Enable audio bell",
            get_ini_val(KITTY_CONF, "enable_audio_bell") == "yes",
            self._apply_kitty_bell,
        )
        box.pack_start(row, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 10)
        btn = Gtk.Button(label="Open kitty.conf in editor")
        btn.get_style_context().add_class("action-btn")
        btn.connect("clicked", lambda _: subprocess.Popen(["micro", KITTY_CONF]))
        box.pack_start(btn, False, False, 0)

        return scroll

    def _kitty_set(self, key, value):
        src = read_file(KITTY_CONF)
        if re.search(rf'^\s*{re.escape(key)}\s', src, re.M):
            src = re.sub(rf'^\s*{re.escape(key)}\s.*$', f'{key} {value}', src, flags=re.M)
        else:
            src = src.rstrip() + f'\n{key} {value}\n'
        write_file(KITTY_CONF, src, do_backup=False)
        # Signal kitty to reload
        subprocess.run(
            ["kitty", "@", "--to", "unix:/tmp/kitty-socket", "load-config"],
            stderr=subprocess.DEVNULL)

    def _apply_kitty_font(self, _):
        v = self.kitty_font.get_text().strip()
        if v: self._kitty_set("font_family", v)

    def _apply_kitty_size(self, v):
        self._kitty_set("font_size", str(int(v)))

    def _apply_kitty_opacity(self, v):
        self._kitty_set("background_opacity", f"{v/100:.2f}")

    def _apply_kitty_padding(self, v):
        self._kitty_set("window_padding_width", str(int(v)))

    def _apply_kitty_cursor(self, combo):
        v = combo.get_active_text()
        if v: self._kitty_set("cursor_shape", v)

    def _apply_kitty_tabbar(self, active):
        self._kitty_set("hide_window_decorations", "yes" if active else "no")

    def _apply_kitty_bell(self, active):
        self._kitty_set("enable_audio_bell", "yes" if active else "no")

    # ============ Wallpaper ============

    def _page_wallpaper(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(20)
        scroll.add(box)

        box.pack_start(section_title("Wallpaper"), False, False, 0)

        info = Gtk.Label()
        info.set_markup(f'<span size="small" color="#9c9c9c">Directory: {WALL_DIR}</span>')
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)

        flow = Gtk.FlowBox()
        flow.set_valign(Gtk.Align.START)
        flow.set_max_children_per_line(3)
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_row_spacing(10)
        flow.set_column_spacing(10)

        files = sorted([
            f for f in os.listdir(WALL_DIR)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ])

        if not files:
            lbl = Gtk.Label(label="No images found. Drop some into the folder.")
            box.pack_start(lbl, False, False, 10)
        else:
            for f in files:
                path = os.path.join(WALL_DIR, f)
                btn = Gtk.Button()
                btn.get_style_context().add_class("wallpaper-btn")
                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                try:
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 200, 120, True)
                    img = Gtk.Image.new_from_pixbuf(pb)
                except Exception:
                    img = Gtk.Image.new_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
                vbox.pack_start(img, False, False, 0)
                name_lbl = Gtk.Label(label=f[:24] + ("..." if len(f) > 24 else ""))
                name_lbl.get_style_context().add_class("wallpaper-name")
                vbox.pack_start(name_lbl, False, False, 0)
                btn.add(vbox)
                btn.connect("clicked", lambda _, p=path: self._set_wallpaper(p))
                flow.add(btn)

        box.pack_start(flow, False, False, 0)

        return scroll

    def _set_wallpaper(self, path):
        subprocess.run(["feh", "--bg-scale", path])
        src = read_file(I3_CONF)
        src = re.sub(r'^exec --no-startup-id feh --bg-scale.*$', '', src, flags=re.M)
        src = src.rstrip() + f'\nexec --no-startup-id feh --bg-scale {path}\n'
        write_file(I3_CONF, src)
        subprocess.Popen(["betterlockscreen", "-u", path, "--fx", "blur"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._toast("Wallpaper set")

    # ============ Colorscheme ============

    def _page_colors(self):
        scroll, box = self._scroll()
        box.pack_start(section_title("Colorscheme"), False, False, 0)

        info = Gtk.Label()
        info.set_markup('<span size="small" color="#9c9c9c">'
                        'Applies colors to Polybar, Dunst, Kitty.</span>')
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)

        group = None
        for name, colors in COLORSCHEMES.items():
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            rb = Gtk.RadioButton.new_with_label_from_widget(group, name.capitalize())
            if group is None: group = rb
            row.pack_start(rb, False, False, 0)

            for key in ("bg", "blue", "red", "green", "yellow"):
                sw = Gtk.DrawingArea()
                sw.set_size_request(20, 20)
                c = colors[key]
                sw.connect("draw", self._draw_swatch, c)
                row.pack_start(sw, False, False, 0)

            rb.connect("toggled", lambda w, n=name: self._apply_colorscheme(n) if w.get_active() else None)
            box.pack_start(row, False, False, 0)

        return scroll

    def _draw_swatch(self, widget, cr, color):
        r = int(color[1:3], 16) / 255
        g = int(color[3:5], 16) / 255
        b = int(color[5:7], 16) / 255
        cr.set_source_rgb(r, g, b)
        cr.rectangle(0, 0, 20, 20)
        cr.fill()

    def _apply_colorscheme(self, name):
        if name not in COLORSCHEMES:
            return
        c = COLORSCHEMES[name]

        src = read_file(POLY_CONF)
        for key, val in c.items():
            src = re.sub(rf'^(\s*{key}\s*=).*$', rf'\g<1> {val}', src, flags=re.M)
        write_file(POLY_CONF, src, do_backup=False)

        src = read_file(DUNST_CONF)
        if src:
            replacements = {"background": c["bg"], "foreground": c["fg"], "frame_color": c["blue"]}
            for key, val in replacements.items():
                src = re.sub(rf'^(\s*{key}\s*=\s*").*(")', rf'\g<1>{val}\g<2>', src, flags=re.M)
            write_file(DUNST_CONF, src, do_backup=False)

        src = read_file(KITTY_CONF)
        if src:
            src = re.sub(r'\n?# ===== rice colors =====.*$', '', src, flags=re.S)
            src += f'''

# ===== rice colors =====
background {c["bg"]}
foreground {c["fg"]}
cursor {c["accent"]}
selection_background {c["blue"]}
selection_foreground {c["bg"]}
'''
            write_file(KITTY_CONF, src, do_backup=False)

        reload_polybar()
        subprocess.run(["pkill", "dunst"], stderr=subprocess.DEVNULL)
        time.sleep(0.3)
        subprocess.Popen(["dunst"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        self._toast(f"Colorscheme: {name}")

    # ============ Presets ============

    def _page_presets(self):
        scroll, box = self._scroll()
        box.pack_start(section_title("Presets"), False, False, 0)

        info = Gtk.Label()
        info.set_markup('<span size="small" color="#9c9c9c">'
                        'Apply a full configuration in one click.</span>')
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)

        presets = [
            ("Minimal",  "No gaps · thin border · no blur · no corners", "minimal"),
            ("Standard", "Medium gaps · Nord · blur 4 · corners 8",       "standard"),
            ("Maximal",  "Big gaps · heavy blur · corners 16 · shadows",  "maximal"),
        ]
        for label, desc, key in presets:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name_lbl = Gtk.Label()
            name_lbl.set_markup(f'<span weight="bold">{label}</span>')
            name_lbl.set_xalign(0)
            vbox.pack_start(name_lbl, False, False, 0)
            desc_lbl = Gtk.Label()
            desc_lbl.set_markup(f'<span size="small" color="#9c9c9c">{desc}</span>')
            desc_lbl.set_xalign(0)
            vbox.pack_start(desc_lbl, False, False, 0)
            row.pack_start(vbox, True, True, 0)

            btn = Gtk.Button(label="Apply")
            btn.get_style_context().add_class("action-btn")
            btn.connect("clicked", lambda _, k=key: self._apply_preset(k))
            row.pack_end(btn, False, False, 0)

            box.pack_start(row, False, False, 6)

        return scroll

    def _apply_preset(self, key):
        src = read_file(I3_CONF)
        if key == "minimal":
            src = re.sub(r'^gaps inner \d+', 'gaps inner 0', src, flags=re.M)
            src = re.sub(r'^gaps outer \d+', 'gaps outer 0', src, flags=re.M)
            src = re.sub(r'^default_border .*', 'default_border pixel 1', src, flags=re.M)
            src = re.sub(r'^default_floating_border .*', 'default_floating_border pixel 1', src, flags=re.M)
        elif key == "standard":
            src = re.sub(r'^gaps inner \d+', 'gaps inner 8', src, flags=re.M)
            src = re.sub(r'^gaps outer \d+', 'gaps outer 4', src, flags=re.M)
            src = re.sub(r'^default_border .*', 'default_border pixel 2', src, flags=re.M)
            src = re.sub(r'^default_floating_border .*', 'default_floating_border pixel 2', src, flags=re.M)
        elif key == "maximal":
            src = re.sub(r'^gaps inner \d+', 'gaps inner 12', src, flags=re.M)
            src = re.sub(r'^gaps outer \d+', 'gaps outer 8', src, flags=re.M)
            src = re.sub(r'^default_border .*', 'default_border pixel 3', src, flags=re.M)
            src = re.sub(r'^default_floating_border .*', 'default_floating_border pixel 3', src, flags=re.M)
        write_file(I3_CONF, src)

        src = read_file(PICOM_CONF)
        if key == "minimal":
            src = re.sub(r'^shadow = .*', 'shadow = false', src, flags=re.M)
            src = re.sub(r'^corner-radius = .*', 'corner-radius = 0', src, flags=re.M)
            src = re.sub(r'\n?blur\s*\{[^}]*\}\s*;?\s*', '\n', src)
        elif key == "standard":
            src = re.sub(r'^shadow = .*', 'shadow = true', src, flags=re.M)
            if not re.search(r'^corner-radius', src, re.M):
                src += '\ncorner-radius = 8\n'
            else:
                src = re.sub(r'^corner-radius = .*', 'corner-radius = 8', src, flags=re.M)
        elif key == "maximal":
            src = re.sub(r'^shadow = .*', 'shadow = true', src, flags=re.M)
            if not re.search(r'^corner-radius', src, re.M):
                src += '\ncorner-radius = 16\n'
            else:
                src = re.sub(r'^corner-radius = .*', 'corner-radius = 16', src, flags=re.M)
            if not re.search(r'^\s*blur\s*\{', src, re.M):
                src = src.rstrip() + '''

blur {
  method = "dual_kawase";
  strength = 8;
};
'''
        write_file(PICOM_CONF, src)

        subprocess.run(["i3-msg", "reload"], stderr=subprocess.DEVNULL)
        reload_picom()
        self._toast(f"Preset: {key}")

    # ============ Backup ============

    def _page_backup(self):
        scroll, box = self._scroll()
        box.pack_start(section_title("Backup"), False, False, 0)

        info = Gtk.Label()
        info.set_markup(f'<span size="small" color="#9c9c9c">Folder: {BACKUP_DIR}</span>')
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)

        btn = Gtk.Button(label="Create Full Backup Now")
        btn.get_style_context().add_class("action-btn")
        btn.connect("clicked", self._create_full_backup)
        box.pack_start(btn, False, False, 8)

        btn = Gtk.Button(label="Restore Latest Backups")
        btn.get_style_context().add_class("danger-btn")
        btn.connect("clicked", self._restore_latest)
        box.pack_start(btn, False, False, 8)

        box.pack_start(Gtk.Separator(), False, False, 10)
        box.pack_start(section_title("Recent Backups"), False, False, 0)

        files = sorted(os.listdir(BACKUP_DIR), reverse=True)[:20]
        tv_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        for f in files:
            size = os.path.getsize(os.path.join(BACKUP_DIR, f))
            lbl = Gtk.Label(label=f"{f}  ({size} bytes)")
            lbl.set_xalign(0)
            lbl.get_style_context().add_class("backup-row")
            tv_box.pack_start(lbl, False, False, 0)
        box.pack_start(tv_box, False, False, 0)

        return scroll

    def _create_full_backup(self, _):
        for f in [I3_CONF, PICOM_CONF, POLY_CONF, KITTY_CONF, DUNST_CONF]:
            if os.path.exists(f):
                backup(f)
        self._toast("Full backup created")

    def _restore_latest(self, _):
        dialog = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Restore latest backups?",
        )
        dialog.format_secondary_text(
            "This will overwrite current configs with the most recent backups.")
        resp = dialog.run()
        dialog.destroy()
        if resp != Gtk.ResponseType.YES:
            return

        pairs = [
            ("config",     I3_CONF),
            ("picom.conf", PICOM_CONF),
            ("config.ini", POLY_CONF),
            ("kitty.conf", KITTY_CONF),
            ("dunstrc",    DUNST_CONF),
        ]
        for prefix, target in pairs:
            files = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith(prefix + ".")],
                           reverse=True)
            if files and os.path.exists(target):
                shutil.copy2(os.path.join(BACKUP_DIR, files[0]), target)

        subprocess.run(["i3-msg", "reload"], stderr=subprocess.DEVNULL)
        reload_picom()
        reload_polybar()
        self._toast("Restored from backups")

    # ============ Session ============

    def _page_session(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(20)

        box.pack_start(section_title("Session"), False, False, 0)

        for label, action in [
            ("Reload i3",       reload_i3),
            ("Restart Picom",   reload_picom),
            ("Restart Polybar", reload_polybar),
        ]:
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("action-btn")
            btn.connect("clicked", lambda _, a=action: a())
            box.pack_start(btn, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 10)

        btn = Gtk.Button(label="Log out of i3")
        btn.get_style_context().add_class("danger-btn")
        btn.connect("clicked", lambda _: subprocess.run(["i3-msg", "exit"]))
        box.pack_start(btn, False, False, 0)

        return box

    # ============ Toast ============

    def _toast(self, message):
        dlg = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        GLib.timeout_add_seconds(2, lambda: (dlg.response(Gtk.ResponseType.OK), False)[1])
        dlg.run()
        dlg.destroy()


if __name__ == "__main__":
    app = TrinitySettings()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

def _toggle_i3_line(line):
    """Toggle i3 config line (add if not present, remove if present)."""
    src = read_file(I3_CONF)
    if line in src:
        src = re.sub(rf'^{re.escape(line)}\s*$', '', src, flags=re.M)
    else:
        src = src.rstrip() + f'\n{line}\n'
    write_file(I3_CONF, src)


def _set_i3_workspace_layout(layout):
    src = read_file(I3_CONF)
    if re.search(r'^workspace_layout ', src, re.M):
        src = re.sub(r'^workspace_layout .*$', f'workspace_layout {layout}', src, flags=re.M)
    else:
        src = src.rstrip() + f'\nworkspace_layout {layout}\n'
    write_file(I3_CONF, src)


def _set_i3_font(font):
    src = read_file(I3_CONF)
    if re.search(r'^font ', src, re.M):
        src = re.sub(r'^font .*$', f'font {font}', src, flags=re.M)
    else:
        src = f'font {font}\n' + src
    write_file(I3_CONF, src)

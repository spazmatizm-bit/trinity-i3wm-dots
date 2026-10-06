#!/usr/bin/env python3
"""Trinity Welcome — 5-step first-time setup wizard."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

import os
import shutil
import subprocess
import sys
import json
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


RICE_NAME = "Trinity"
FLAG = os.path.expanduser("~/.config/.trinity-installed")
THEMES_FILE = os.path.expanduser("~/dotfiles/themes/themes.json")
THEME_SWITCH = os.path.expanduser("~/.config/i3/scripts/theme-switch.sh")
CURRENT_THEME = os.path.expanduser("~/.config/theme-current")

DEPS = [
    ("i3-wm",                  "i3",              "Window manager"),
    ("polybar",                "polybar",         "Status bar"),
    ("picom",                  "picom",           "Compositor"),
    ("kitty",                  "kitty",           "Terminal"),
    ("rofi",                   "rofi",            "Launcher"),
    ("dunst",                  "dunst",           "Notifications"),
    ("feh",                    "feh",             "Wallpaper"),
    ("fish",                   "fish",            "Shell"),
    ("fastfetch",              "fastfetch",       "System info"),
    ("playerctl",              "playerctl",       "Media control"),
    ("mpv",                    "mpv",             "Media player"),
    ("xclip",                  "xclip",           "Clipboard"),
    ("maim",                   "maim",            "Screenshots"),
    ("socat",                  "socat",           "IPC bridge"),
    ("jq",                     "jq",              "JSON tools"),
    ("bc",                     "bc",              "Calculator"),
    ("micro",                  "micro",           "Editor"),
    ("cava",                   "cava",            "Audio visualizer"),
    ("cmatrix",                "cmatrix",         "Matrix rain"),
    ("ttf-jetbrains-mono-nerd","",                "Nerd Font"),
    ("ttf-font-awesome",       "",                "Font Awesome"),
    ("papirus-icon-theme",     "",                "Icon theme"),
    ("python-gobject",         "",                "GTK bindings"),
    ("gtk3",                   "",                "GTK toolkit"),
]

AUR_DEPS = [
    ("betterlockscreen",       "betterlockscreen",  "Lock screen"),
    ("rofi-greenclip",         "greenclip",         "Clipboard manager"),
    ("playerctld-systemd-unit","",                   "MPRIS aggregator"),
]

KEYBINDS = [
    ("$mod+q",          "Terminal (kitty)"),
    ("$mod+p",          "Launcher (rofi)"),
    ("$mod+F2",         "Trinity Settings"),
    ("$mod+Shift+t",    "Change theme"),
    ("$mod+v",          "Clipboard history"),
    ("$mod+Shift+x",    "Power menu"),
    ("$mod+l",          "Lock screen"),
    ("$mod+Shift+End",  "Screenshot"),
    ("$mod+grave",      "Scratchpad terminal"),
    ("$mod+Return",     "Swap master/stack"),
    ("$mod+1..0",       "Switch workspace"),
    ("$mod+F1",         "Cheatsheet (all binds)"),
]


def check(cmd):
    return shutil.which(cmd) is not None if cmd else True


def run(cmd, sudo=False):
    try:
        args = ["sudo"] + cmd if sudo else cmd
        r = subprocess.run(args, capture_output=True, text=True, timeout=600)
        return r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return False, str(e)


def load_themes():
    try:
        with open(THEMES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def current_theme():
    try:
        with open(CURRENT_THEME) as f:
            return f.read().strip()
    except Exception:
        return ""


class Welcome(Gtk.Window):
    def __init__(self):
        super().__init__(title="Trinity — Setup")
        self.set_default_size(760, 640)
        self.set_size_request(760, 640)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_name("welcome")
        self.set_wmclass("trinity-welcome", "TrinityWelcome")
        self.set_role("trinity-welcome")
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)

        css = os.path.join(os.path.dirname(__file__), "style.css")
        if os.path.exists(css):
            p = Gtk.CssProvider()
            p.load_from_path(css)
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), p,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(200)
        root.pack_start(self.stack, True, True, 0)

        self.stack.add_named(self._page_welcome(),   "welcome")
        self.stack.add_named(self._page_deps(),      "deps")
        self.stack.add_named(self._page_theme(),     "theme")
        self.stack.add_named(self._page_keybinds(),  "keybinds")
        self.stack.add_named(self._page_finish(),    "finish")

        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        nav.set_border_width(16)
        nav.get_style_context().add_class("nav-bar")
        root.pack_start(nav, False, False, 0)

        self.back_btn = Gtk.Button(label="← Back")
        self.back_btn.connect("clicked", self._go_back)
        nav.pack_start(self.back_btn, False, False, 0)

        self.step_label = Gtk.Label()
        self.step_label.set_hexpand(True)
        nav.pack_start(self.step_label, True, True, 0)

        self.next_btn = Gtk.Button(label="Next →")
        self.next_btn.get_style_context().add_class("action-btn")
        self.next_btn.connect("clicked", self._go_next)
        nav.pack_end(self.next_btn, False, False, 0)

        self._update_nav()
        self.connect("key-press-event", self._on_key)

    def _page_welcome(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_border_width(40)
        box.set_valign(Gtk.Align.CENTER)

        logo = Gtk.Label()
        logo.set_markup('<span size="40000" weight="bold" color="#88c0d0">Trinity</span>')
        box.pack_start(logo, False, False, 0)

        sub = Gtk.Label()
        sub.set_markup('<span size="large" color="#9c9c9c">A minimal i3wm rice</span>')
        box.pack_start(sub, False, False, 0)

        desc = Gtk.Label()
        desc.set_markup(
            '<span size="medium">\n\n'
            'First-time setup will take a few minutes:\n\n'
            '  1.  Check and install dependencies\n'
            '  2.  Pick a color theme\n'
            '  3.  Show main keybindings\n'
            '  4.  Done'
            '\n\n'
            'After that, you are all set.'
            '</span>'
        )
        desc.set_line_wrap(True)
        desc.set_justify(Gtk.Justification.CENTER)
        box.pack_start(desc, False, False, 0)

        return box

    def _page_deps(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(24)

        title = Gtk.Label()
        title.set_markup('<span size="x-large" weight="bold">Dependencies</span>')
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)

        sub = Gtk.Label()
        sub.set_markup('<span color="#9c9c9c">Uncheck packages you do not need.</span>')
        sub.set_xalign(0)
        box.pack_start(sub, False, False, 0)

        missing_repo = [(p, d) for p, c, d in DEPS if not check(c)]
        missing_aur = [(p, d) for p, c, d in AUR_DEPS if not check(c)]
        installed = len([1 for p, c, d in DEPS if check(c)]) + len([1 for p, c, d in AUR_DEPS if check(c)])
        total_missing = len(missing_repo) + len(missing_aur)

        summary = Gtk.Label()
        summary.set_markup(
            '<span size="medium">Installed: <b>' + str(installed) + '</b> · '
            'Missing: <b>' + str(total_missing) + '</b></span>'
        )
        summary.set_xalign(0)
        summary.set_margin_top(10)
        box.pack_start(summary, False, False, 0)

        self.checks = {}

        if total_missing == 0:
            ok = Gtk.Label()
            ok.set_markup('<span size="x-large">✅ Everything is installed!</span>')
            ok.set_margin_top(40)
            ok.set_margin_bottom(40)
            box.pack_start(ok, False, False, 0)
        else:
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            sw = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            sw.set_border_width(6)
            scroll.add(sw)

            if missing_repo:
                lbl = Gtk.Label()
                lbl.set_markup('<b>Repository (pacman)</b>')
                lbl.set_xalign(0)
                lbl.set_margin_top(6)
                lbl.set_margin_bottom(4)
                sw.pack_start(lbl, False, False, 0)
                for pkg, d in missing_repo:
                    cb = Gtk.CheckButton(label=pkg + "  —  " + d)
                    cb.set_active(True)
                    sw.pack_start(cb, False, False, 0)
                    self.checks[pkg] = cb

            if missing_aur:
                sep = Gtk.Separator()
                sep.set_margin_top(10)
                sep.set_margin_bottom(6)
                sw.pack_start(sep, False, False, 0)
                lbl = Gtk.Label()
                lbl.set_markup('<b>AUR (via yay)</b>')
                lbl.set_xalign(0)
                lbl.set_margin_bottom(4)
                sw.pack_start(lbl, False, False, 0)
                for pkg, d in missing_aur:
                    cb = Gtk.CheckButton(label=pkg + "  —  " + d)
                    cb.set_active(True)
                    sw.pack_start(cb, False, False, 0)
                    self.checks["AUR:" + pkg] = cb

            box.pack_start(scroll, True, True, 0)

            self.log = Gtk.TextView()
            self.log.set_editable(False)
            self.log.set_monospace(True)
            self.log.set_size_request(-1, 90)
            log_sw = Gtk.ScrolledWindow()
            log_sw.add(self.log)
            box.pack_start(log_sw, False, False, 0)

            install_btn = Gtk.Button(label="Install selected")
            install_btn.get_style_context().add_class("action-btn")
            install_btn.connect("clicked", self._install)
            box.pack_start(install_btn, False, False, 0)

        return box

    def _page_theme(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_border_width(24)

        title = Gtk.Label()
        title.set_markup('<span size="x-large" weight="bold">Color theme</span>')
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)

        sub = Gtk.Label()
        sub.set_markup('<span color="#9c9c9c">Pick a theme. You can change it later with <b>$mod+Shift+t</b>.</span>')
        sub.set_xalign(0)
        box.pack_start(sub, False, False, 0)

        themes = load_themes()
        cur = current_theme()

        if not themes:
            warn = Gtk.Label()
            warn.set_markup('<span color="#bf616a">No themes found in ~/dotfiles/themes/themes.json</span>')
            box.pack_start(warn, False, False, 20)
            self._selected_theme = None
            return box

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        flow = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        flow.set_border_width(6)
        scroll.add(flow)

        self.theme_buttons = {}
        self._selected_theme = cur if cur in themes else list(themes.keys())[0]

        first_radio = None
        for name, t in themes.items():
            if name == "custom":
                continue
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.set_margin_top(4)
            row.set_margin_bottom(4)

            if first_radio is None:
                rb = Gtk.RadioButton()
                first_radio = rb
            else:
                rb = Gtk.RadioButton.new_from_widget(first_radio)
            rb.set_active(name == self._selected_theme)
            rb.connect("toggled", self._select_theme, name)
            row.pack_start(rb, False, False, 0)

            for key in ("bg", "blue", "blue_dim", "red", "green"):
                sw = Gtk.DrawingArea()
                sw.set_size_request(24, 24)
                c = t.get(key, "#000000")
                sw.connect("draw", self._draw_swatch, c)
                row.pack_start(sw, False, False, 0)

            nm = Gtk.Label()
            nm.set_markup('<b>' + t.get("name", name) + '</b>')
            nm.set_width_chars(12)
            nm.set_xalign(0)
            row.pack_start(nm, False, False, 0)

            id_lbl = Gtk.Label()
            id_lbl.set_markup('<span size="small" color="#9c9c9c">' + name + '</span>')
            id_lbl.set_xalign(0)
            row.pack_start(id_lbl, True, True, 0)

            flow.pack_start(row, False, False, 0)

        box.pack_start(scroll, True, True, 0)

        info = Gtk.Label()
        info.set_markup('<span size="small" color="#9c9c9c">Theme will be applied when setup finishes.</span>')
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)

        return box

    def _page_keybinds(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(24)

        title = Gtk.Label()
        title.set_markup('<span size="x-large" weight="bold">Main keybindings</span>')
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)

        sub = Gtk.Label()
        sub.set_markup('<span color="#9c9c9c">Modifier = <b>Super</b> (Windows key)</span>')
        sub.set_xalign(0)
        box.pack_start(sub, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(20)
        grid.set_border_width(10)
        scroll.add(grid)

        for i, (key, action) in enumerate(KEYBINDS):
            key_lbl = Gtk.Label()
            key_lbl.set_markup('<span font_family="monospace" weight="bold" color="#88c0d0">' + key + '</span>')
            key_lbl.set_xalign(0)
            key_lbl.set_size_request(180, -1)
            grid.attach(key_lbl, 0, i, 1, 1)

            act_lbl = Gtk.Label(label=action)
            act_lbl.set_xalign(0)
            grid.attach(act_lbl, 1, i, 1, 1)

        box.pack_start(scroll, True, True, 0)

        hint = Gtk.Label()
        hint.set_markup('<span size="small" color="#9c9c9c">Press <b>$mod+F1</b> to see all keybindings.</span>')
        hint.set_xalign(0)
        box.pack_start(hint, False, False, 0)

        return box

    def _page_finish(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(40)
        box.set_valign(Gtk.Align.CENTER)

        icon = Gtk.Label()
        icon.set_markup('<span size="40000" color="#a3be8c">✓</span>')
        box.pack_start(icon, False, False, 0)

        title = Gtk.Label()
        title.set_markup('<span size="xx-large" weight="bold">Done</span>')
        box.pack_start(title, False, False, 0)

        desc = Gtk.Label()
        desc.set_markup(
            '<span size="medium">\n'
            'Trinity is installed and configured.\n\n'
            'Quick reference:\n\n'
            '   $mod+F2 — Trinity Settings\n'
            '   $mod+Shift+t — change theme\n'
            '   $mod+q — terminal\n'
            '   $mod+F1 — all keybindings\n\n'
            'Enjoy.'
            '</span>'
        )
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_line_wrap(True)
        box.pack_start(desc, False, False, 0)

        return box

    def _draw_swatch(self, widget, cr, color):
        try:
            r = int(color[1:3], 16) / 255
            g = int(color[3:5], 16) / 255
            b = int(color[5:7], 16) / 255
            cr.set_source_rgb(r, g, b)
        except Exception:
            cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.rectangle(0, 0, widget.get_allocated_width(), widget.get_allocated_height())
        cr.fill()

    def _select_theme(self, radio, name):
        if radio.get_active():
            self._selected_theme = name

    NAMES = ["welcome", "deps", "theme", "keybinds", "finish"]

    def _current_index(self):
        cur = self.stack.get_visible_child_name()
        return self.NAMES.index(cur) if cur in self.NAMES else 0

    def _go_next(self, *_):
        idx = self._current_index()
        if idx >= len(self.NAMES) - 1:
            self._finish()
            return
        self.stack.set_visible_child_name(self.NAMES[idx + 1])
        self._update_nav()

    def _go_back(self, *_):
        idx = self._current_index()
        if idx == 0:
            return
        self.stack.set_visible_child_name(self.NAMES[idx - 1])
        self._update_nav()

    def _update_nav(self):
        idx = self._current_index()
        total = len(self.NAMES)
        self.step_label.set_markup('<span color="#9c9c9c">Step ' + str(idx + 1) + ' / ' + str(total) + '</span>')
        self.back_btn.set_sensitive(idx > 0)
        if idx == total - 1:
            self.next_btn.set_label("Finish")
        else:
            self.next_btn.set_label("Next →")

    def _on_key(self, _, event):
        if event.keyval == Gdk.KEY_Escape:
            self._finish()
            return True
        if event.keyval == Gdk.KEY_Right:
            self._go_next()
            return True
        if event.keyval == Gdk.KEY_Left:
            self._go_back()
            return True
        return False

    def _log(self, text):
        if not hasattr(self, "log"):
            return
        buf = self.log.get_buffer()
        buf.insert(buf.get_end_iter(), text + "\n")
        mark = buf.create_mark(None, buf.get_end_iter(), False)
        self.log.scroll_to_mark(mark, 0, False, 0, 0)

    def _install(self, _):
        repo, aur = [], []
        for pkg, cb in self.checks.items():
            if not cb.get_active():
                continue
            if pkg.startswith("AUR:"):
                aur.append(pkg[4:])
            else:
                repo.append(pkg)

        if repo:
            self._log("=== pacman -S " + " ".join(repo) + " ===")
            ok, out = run(["pacman", "-S", "--needed", "--noconfirm"] + repo, sudo=True)
            self._log(out[-1200:] if len(out) > 1200 else out)
            self._log("→ " + ("OK" if ok else "FAILED"))
        if aur:
            if not shutil.which("yay"):
                self._log("!!! yay not installed")
            else:
                self._log("=== yay -S " + " ".join(aur) + " ===")
                ok, out = run(["yay", "-S", "--needed", "--noconfirm"] + aur)
                self._log(out[-1200:] if len(out) > 1200 else out)
                self._log("→ " + ("OK" if ok else "FAILED"))

        self._log("")
        self._log("Done. Нажми Далее.")

    def _finish(self, *_):
        # 1. Hide window immediately to prevent click capture
        try:
            self.hide()
        except Exception:
            pass

        # 2. Apply theme in background (after window hidden)
        theme = getattr(self, "_selected_theme", None)
        if theme and os.path.exists(THEME_SWITCH):
            try:
                subprocess.Popen(
                    ["bash", THEME_SWITCH, theme],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            except Exception:
                pass

        # 3. Create flag
        try:
            os.makedirs(os.path.dirname(FLAG), exist_ok=True)
            with open(FLAG, "w") as f:
                f.write("installed
")
        except Exception:
            pass

        # 4. Schedule quit — give GTK time to process hide
        GLib.timeout_add(200, Gtk.main_quit)
        return False


if __name__ == "__main__":
    if "--force" in sys.argv:
        print("Force mode — ignoring flag")
    elif os.path.exists(FLAG):
        print("Already installed: " + FLAG)
        print("Use --force to show again")
        sys.exit(0)

    app = Welcome()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

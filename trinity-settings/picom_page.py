"""Enhanced Picom settings with Apply button (uses config_utils)."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import os, re, subprocess
from apply_mixin import ApplyBar, DeferredSection
from config_utils import picom as PC

PICOM_CONF = os.path.expanduser("~/.config/picom/picom.conf")
BACKUP_DIR = os.path.expanduser("~/.config/trinity-backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


def read():
    try:
        return open(PICOM_CONF).read()
    except Exception:
        return ""


def write(content, backup=True):
    if backup:
        import shutil
        from datetime import datetime as _dt
        try:
            ts = _dt.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(PICOM_CONF, os.path.join(BACKUP_DIR, f"picom.conf.{ts}"))
        except Exception:
            pass
    open(PICOM_CONF, "w").write(content)


def st(t):
    l = Gtk.Label(); l.set_markup(f'<span size="large" weight="bold">{t}</span>')
    l.set_xalign(0); l.get_style_context().add_class("section-title"); return l


def slider(label, mn, mx, step, init, cb):
    b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label=label); l.set_width_chars(24); l.set_xalign(0)
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


def combo(label, options, current, cb):
    b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    l = Gtk.Label(label=label); l.set_width_chars(24); l.set_xalign(0)
    l.get_style_context().add_class("param-label"); b.pack_start(l, False, False, 0)
    c = Gtk.ComboBoxText()
    for o in options: c.append_text(o)
    if current in options: c.set_active(options.index(current))
    c.connect("changed", lambda w: cb(w.get_active_text()))
    b.pack_start(c, True, True, 0)
    return b


def build_page(parent):
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    box.set_border_width(20)
    scroll.add(box)

    def on_apply(pending):
        p = PC()
        for key, val in pending.items():
            p.set(key, val)

    def on_reload():
        subprocess.run(["pkill", "picom"], stderr=subprocess.DEVNULL)
        import time; time.sleep(0.4)
        subprocess.Popen(["picom", "--config", PICOM_CONF, "-b"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    section = DeferredSection(on_apply=on_apply, on_reload=on_reload)
    p = PC()

    p_src = read()

    title = Gtk.Label()
    title.set_markup('<span size="x-large" weight="bold">Picom Compositor</span>')
    title.set_xalign(0)
    box.pack_start(title, False, False, 0)

    info = Gtk.Label()
    info.set_markup('<span size="small" color="#9c9c9c">Changes are applied when you click Apply at the bottom.</span>')
    info.set_xalign(0)
    box.pack_start(info, False, False, 0)

    # Backend
    box.pack_start(st("Backend &amp; Performance"), False, False, 10)
    box.pack_start(combo("Backend", ["glx", "xrender", "vulkan"],
        p.get("backend", "glx"), lambda v: section.set("backend", v)), False, False, 0)
    box.pack_start(combo("VSync", ["true", "false", "opengl-swc", "opengl"],
        p.get("vsync", "true"), lambda v: section.set("vsync", v)), False, False, 0)
    box.pack_start(toggle("Use damage (faster)",
        p.get("use-damage", "true") == "true", lambda v: section.set("use-damage", v)), False, False, 0)
    box.pack_start(toggle("Unredirect fullscreen",
        p.get("unredir-if-possible", "false") == "true", lambda v: section.set("unredir-if-possible", v)), False, False, 0)

    box.pack_start(toggle("Detect client opacity",
        p.get("detect-client-opacity", "true") == "true",
        lambda v: section.set("detect-client-opacity", v)), False, False, 0)
    box.pack_start(toggle("Mark wmwin focused",
        p.get("mark-wmwin-focused", "true") == "true",
        lambda v: section.set("mark-wmwin-focused", v)), False, False, 0)

    # Shadows
    box.pack_start(st("Shadows"), False, False, 10)
    box.pack_start(toggle("Enable shadows", p.get("shadow", "true") == "true",
        lambda v: section.set("shadow", v)), False, False, 0)
    r, _ = slider("Shadow radius", 0, 30, 1, int(float(p.get("shadow-radius", 10))),
                  lambda v: section.set("shadow-radius", int(v)))
    box.pack_start(r, False, False, 0)
    r, _ = slider("Shadow opacity (%)", 0, 100, 5, int(float(p.get("shadow-opacity", 0.5)) * 100),
                  lambda v: section.set("shadow-opacity", f"{v/100:.2f}"))
    box.pack_start(r, False, False, 0)
    r, _ = slider("Shadow offset X", -30, 0, 1, int(float(p.get("shadow-offset-x", -8))),
                  lambda v: section.set("shadow-offset-x", int(v)))
    box.pack_start(r, False, False, 0)
    r, _ = slider("Shadow offset Y", -30, 0, 1, int(float(p.get("shadow-offset-y", -8))),
                  lambda v: section.set("shadow-offset-y", int(v)))
    box.pack_start(r, False, False, 0)

    # Fading
    box.pack_start(st("Fading"), False, False, 10)
    box.pack_start(toggle("Enable fading", p.get("fading", "true") == "true",
        lambda v: section.set("fading", v)), False, False, 0)
    r, _ = slider("Fade in step ×100", 1, 20, 1, int(float(p.get("fade-in-step", 0.05)) * 100),
                  lambda v: section.set("fade-in-step", f"{v/100:.2f}"))
    box.pack_start(r, False, False, 0)
    r, _ = slider("Fade out step ×100", 1, 20, 1, int(float(p.get("fade-out-step", 0.05)) * 100),
                  lambda v: section.set("fade-out-step", f"{v/100:.2f}"))
    box.pack_start(r, False, False, 0)

    # Opacity
    box.pack_start(st("Opacity"), False, False, 10)
    r, _ = slider("Active opacity (%)", 50, 100, 1, int(float(p.get("active-opacity", 1.0)) * 100),
                  lambda v: section.set("active-opacity", f"{v/100:.2f}"))
    box.pack_start(r, False, False, 0)
    r, _ = slider("Inactive opacity (%)", 50, 100, 1, int(float(p.get("inactive-opacity", 0.9)) * 100),
                  lambda v: section.set("inactive-opacity", f"{v/100:.2f}"))
    box.pack_start(r, False, False, 0)
    r, _ = slider("Inactive dim ×100", 0, 50, 1, int(float(p.get("inactive-dim", 0.1)) * 100),
                  lambda v: section.set("inactive-dim", f"{v/100:.2f}"))
    box.pack_start(r, False, False, 0)

    # Corners
    box.pack_start(st("Rounded Corners"), False, False, 10)
    r, _ = slider("Corner radius", 0, 30, 1, int(float(p.get("corner-radius", 8))),
                  lambda v: section.set("corner-radius", int(v)))
    box.pack_start(r, False, False, 0)

    # === Blur (extended) ===
    box.pack_start(st("Blur (matte effect)"), False, False, 10)

    # Blur enabled toggle
    blur_enabled = bool(re.search(r'blur\s*\{', p_src))
    box.pack_start(toggle("Enable blur", blur_enabled,
        lambda v: section.stage(lambda: _set_blur_enabled(v))), False, False, 0)

    # Blur method
    current_method = "dual_kawase"
    m = re.search(r'blur\s*\{[^}]*?method\s*=\s*"([^"]+)"', p_src, re.DOTALL)
    if m: current_method = m.group(1)
    box.pack_start(combo("Blur method",
        ["dual_kawase", "kawase", "gaussian", "box"],
        current_method,
        lambda v: section.stage(lambda: _set_blur_method(v))), False, False, 0)

    # Blur strength
    current_strength = 4
    m = re.search(r'blur\s*\{[^}]*?strength\s*=\s*(\d+)', p_src, re.DOTALL)
    if m: current_strength = int(m.group(1))
    r, _ = slider("Blur strength", 1, 20, 1, current_strength,
                  lambda v: section.stage(lambda: _set_blur_strength(int(v))))
    box.pack_start(r, False, False, 0)

    # Gaussian kernel (if gaussian method)
    current_kernel = "11x11gaussian"
    m = re.search(r'blur\s*\{[^}]*?kernel\s*=\s*"([^"]+)"', p_src, re.DOTALL)
    if m: current_kernel = m.group(1)
    box.pack_start(combo("Blur kernel (gaussian)",
        ["3x3box", "5x5box", "7x7box", "9x9box", "11x11box",
         "3x3gaussian", "5x5gaussian", "7x7gaussian", "9x9gaussian",
         "11x11gaussian", "13x13gaussian", "15x15gaussian"],
        current_kernel,
        lambda v: section.stage(lambda: _set_blur_kernel(v))), False, False, 0)

    # Matte frame opacity
    current_frame = 1.0
    m = re.search(r'frame-opacity\s*=\s*([\d.]+)', p_src)
    if m: current_frame = float(m.group(1))
    r, _ = slider("Frame opacity ×100", 50, 100, 1, int(current_frame * 100),
                  lambda v: section.set("frame-opacity", f"{v/100:.2f}"))
    box.pack_start(r, False, False, 0)

    # Actions
    box.pack_start(Gtk.Separator(), False, False, 10)
    rb = Gtk.Button(label="Restart Picom now")
    rb.get_style_context().add_class("action-btn")
    rb.connect("clicked", lambda _: on_reload())
    box.pack_start(rb, False, False, 0)
    ob = Gtk.Button(label="Open picom.conf in editor")
    ob.connect("clicked", lambda _: subprocess.Popen(["micro", PICOM_CONF]))
    box.pack_start(ob, False, False, 0)

    bar = ApplyBar(on_apply=section.apply, on_reset=section.reset)
    section.attach_bar(bar)
    box.pack_start(Gtk.Separator(), False, False, 10)
    box.pack_start(bar, False, False, 0)

    return scroll

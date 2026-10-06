"""ApplyBar with Apply/Reset/Save/Load preset buttons."""
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import subprocess
import os


class ApplyBar(Gtk.Box):
    """Bottom bar with Apply / Reset / Save As / Load buttons."""

    def __init__(self, on_apply, on_reset=None, on_reload=None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.set_margin_top(10)
        self.set_margin_bottom(5)
        self.on_apply = on_apply
        self.on_reset = on_reset
        self.on_reload = on_reload
        self._dirty = False

        # Status label
        self.status = Gtk.Label()
        self.status.set_markup('<span color="#9c9c9c">No changes</span>')
        self.status.set_xalign(0)
        self.status.set_hexpand(True)
        self.pack_start(self.status, True, True, 0)

        # Load preset
        load_btn = Gtk.Button(label="Load")
        load_btn.set_tooltip_text("Load a saved preset")
        load_btn.connect("clicked", self._on_load)
        self.pack_end(load_btn, False, False, 0)

        # Save As preset
        save_btn = Gtk.Button(label="Save As…")
        save_btn.set_tooltip_text("Save current config as a preset")
        save_btn.connect("clicked", self._on_save)
        self.pack_end(save_btn, False, False, 0)

        # Reset
        self.reset_btn = Gtk.Button(label="Reset")
        self.reset_btn.set_tooltip_text("Undo unsaved changes")
        self.reset_btn.set_sensitive(False)
        self.reset_btn.connect("clicked", self._reset)
        self.pack_end(self.reset_btn, False, False, 0)

        # Apply
        self.apply_btn = Gtk.Button(label="Apply")
        self.apply_btn.get_style_context().add_class("action-btn")
        self.apply_btn.set_tooltip_text("Apply changes")
        self.apply_btn.set_sensitive(False)
        self.apply_btn.connect("clicked", self._apply)
        self.pack_end(self.apply_btn, False, False, 0)

    def mark_dirty(self):
        if not self._dirty:
            self._dirty = True
            self.apply_btn.set_sensitive(True)
            self.reset_btn.set_sensitive(True)
            self.status.set_markup('<span color="#ebcb8b">● Unsaved changes</span>')

    def mark_clean(self):
        self._dirty = False
        self.apply_btn.set_sensitive(False)
        self.reset_btn.set_sensitive(False)
        self.status.set_markup('<span color="#a3be8c">✓ Saved</span>')

    def _apply(self, _):
        try:
            self.on_apply()
            self.mark_clean()
            if self.on_reload:
                self.on_reload()
        except Exception as e:
            self.status.set_markup(f'<span color="#bf616a">✗ {e}</span>')

    def _reset(self, _):
        if self.on_reset:
            try: self.on_reset()
            except: pass
        self.mark_clean()

    def _on_save(self, _):
        """Save current configs as a preset."""
        dialog = Gtk.Dialog(title="Save Preset", transient_for=self.get_toplevel(), flags=0)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)
        dialog.set_default_size(400, 220)
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_border_width(15)

        content.add(Gtk.Label(label="Preset name:", xalign=0))
        name_entry = Gtk.Entry()
        name_entry.set_text("my-preset-" + __import__("datetime").datetime.now().strftime("%Y%m%d"))
        content.add(name_entry)

        content.add(Gtk.Label(label="Description (optional):", xalign=0))
        desc_entry = Gtk.Entry()
        content.add(desc_entry)

        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            name = name_entry.get_text().strip()
            desc = desc_entry.get_text().strip()
            if name:
                try:
                    import sys
                    sys.path.insert(0, os.path.expanduser("~/Documents/trinity-settings"))
                    from config_presets import save_preset
                    path, count = save_preset(name, desc)
                    subprocess.Popen(["dunstify", "-a", "trinity", "-u", "low",
                                      "Preset saved", f"{name} ({count} files)"])
                except Exception as e:
                    subprocess.Popen(["dunstify", "-a", "trinity", "-u", "critical",
                                      "Save failed", str(e)])
        dialog.destroy()

    def _on_load(self, _):
        """Load a preset."""
        try:
            import sys
            sys.path.insert(0, os.path.expanduser("~/Documents/trinity-settings"))
            from config_presets import list_presets, load_preset
            presets = list_presets()
        except Exception as e:
            subprocess.Popen(["dunstify", "-a", "trinity", "-u", "critical", "Error", str(e)])
            return

        if not presets:
            subprocess.Popen(["dunstify", "-a", "trinity", "No presets",
                              "Save one first with Save As…"])
            return

        dialog = Gtk.Dialog(title="Load Preset", transient_for=self.get_toplevel(), flags=0)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Load", Gtk.ResponseType.OK)
        dialog.set_default_size(500, 400)
        content = dialog.get_content_area()
        content.set_spacing(10)
        content.set_border_width(15)

        content.add(Gtk.Label(label="Select preset to load:", xalign=0))

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        rows = {}
        for p in presets:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            hbox.set_margin_top(6); hbox.set_margin_bottom(6)
            hbox.set_margin_start(8); hbox.set_margin_end(8)
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            name_lbl = Gtk.Label()
            name_lbl.set_markup(f'<b>{p["name"]}</b>')
            name_lbl.set_xalign(0)
            vbox.pack_start(name_lbl, False, False, 0)
            meta_lbl = Gtk.Label()
            meta_lbl.set_markup(f'<span size="small" color="#9c9c9c">{p["timestamp"]} · {p["theme"]} · {p["description"]}</span>')
            meta_lbl.set_xalign(0)
            vbox.pack_start(meta_lbl, False, False, 0)
            hbox.pack_start(vbox, True, True, 0)
            row.add(hbox)
            listbox.add(row)
            rows[row] = p
        scrolled.add(listbox)
        content.add(scrolled)

        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            selected = listbox.get_selected_row()
            if selected and selected in rows:
                p = rows[selected]
                try:
                    count, backup = load_preset(p["name"])
                    subprocess.Popen(["dunstify", "-a", "trinity", "-u", "normal",
                                      f"Loaded: {p['name']}",
                                      f"{count} files restored"])
                except Exception as e:
                    subprocess.Popen(["dunstify", "-a", "trinity", "-u", "critical",
                                      "Load failed", str(e)])
        dialog.destroy()


class DeferredSection:
    def __init__(self, on_apply=None, on_reload=None):
        self.pending = {}
        self.staged_funcs = []
        self.on_apply = on_apply
        self.on_reload = on_reload
        self.bar = None

    def attach_bar(self, bar):
        self.bar = bar

    def set(self, key, value):
        self.pending[key] = value
        if self.bar:
            self.bar.mark_dirty()

    def stage(self, func):
        self.staged_funcs.append(func)
        if self.bar:
            self.bar.mark_dirty()

    def apply(self):
        if self.pending and self.on_apply:
            self.on_apply(self.pending)
        for fn in self.staged_funcs:
            try: fn()
            except: pass
        self.pending.clear()
        self.staged_funcs.clear()
        if self.on_reload:
            try: self.on_reload()
            except: pass

    def reset(self):
        self.pending.clear()
        self.staged_funcs.clear()

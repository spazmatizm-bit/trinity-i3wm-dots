#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, AppIndicator3
import subprocess

ICON_PLAY = "media-playback-start"
ICON_PAUSE = "media-playback-pause"

def run(cmd):
    subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

class MusicTray:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            "music-tray",
            ICON_PLAY,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

    def build_menu(self):
        menu = Gtk.Menu()

        item_playlist = Gtk.MenuItem(label="Choose Playlist")
        item_playlist.connect("activate", lambda _: run("~/.config/polybar/scripts/playlist-picker.sh"))
        menu.append(item_playlist)

        item_toggle = Gtk.MenuItem(label="Play / Pause")
        item_toggle.connect("activate", lambda _: run("~/.config/polybar/scripts/player-ctl.sh toggle"))
        menu.append(item_toggle)

        item_next = Gtk.MenuItem(label="Next")
        item_next.connect("activate", lambda _: run("~/.config/polybar/scripts/player-ctl.sh next"))
        menu.append(item_next)

        item_prev = Gtk.MenuItem(label="Previous")
        item_prev.connect("activate", lambda _: run("~/.config/polybar/scripts/player-ctl.sh prev"))
        menu.append(item_prev)

        menu.append(Gtk.SeparatorMenuItem())

        item_stop = Gtk.MenuItem(label="Stop")
        item_stop.connect("activate", lambda _: run("~/.config/polybar/scripts/player-ctl.sh stop"))
        menu.append(item_stop)

        item_quit = Gtk.MenuItem(label="Quit Tray")
        item_quit.connect("activate", lambda _: Gtk.main_quit())
        menu.append(item_quit)

        menu.show_all()
        return menu

if __name__ == "__main__":
    tray = MusicTray()
    Gtk.main()

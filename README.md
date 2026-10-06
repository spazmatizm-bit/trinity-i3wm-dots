# Trinity

A minimal i3wm rice for Arch Linux, built around five interchangeable color themes and a GTK settings panel for live configuration.

## Overview

Trinity is a personal desktop setup built on X11, targeting systems where Wayland is not viable (for example, NVIDIA Pascal GPUs). It provides a themed i3 + Polybar + Picom environment with a Python/GTK3 control panel for editing configuration without touching config files by hand.

## Components

| Component | Purpose |
| --- | --- |
| i3 | Window manager |
| Polybar | Status bar |
| Picom | Compositor (blur, shadows, rounded corners) |
| Kitty | Terminal emulator |
| Rofi | Application launcher |
| Dunst | Notification daemon |
| Fish | Shell |
| Fastfetch | System information |
| Cava | Audio visualizer |
| Cmatrix | Terminal animation |
| Betterlockscreen | Lock screen |
| Greenclip | Clipboard history |
| Trinity Settings | GTK3 configuration panel |

## Themes

Five themes are included, each with a matching wallpaper, color palette, and Rofi/Dunst/Kitty/Cava configuration:

- forest
- nordy
- sakura
- alps
- neon

Themes are applied with `theme-switch.sh <theme>` or from the Themes section in Trinity Settings. Each theme defines a full color set (background, foreground, accent, dim, red, green, yellow, cyan) and gradient colors for Cava. A theme can also be generated from an image via the "Generate theme from image" action.

## Requirements

- Arch Linux
- An AUR helper (paru or yay; paru is installed automatically if neither is present)
- X11 session (i3)

## Installation

Clone the repository and run the installer:

    git clone https://github.com/spazmatizm-bit/trinity-rice.git
    cd trinity-rice
    chmod +x install.sh
    ./install.sh

Or run the bootstrap script directly:

    bash <(curl -fsSL https://raw.githubusercontent.com/spazmatizm-bit/trinity-rice/main/bootstrap.sh)

The installer performs the following steps:

1. Verifies the system is Arch Linux
2. Installs base-devel and git
3. Installs an AUR helper if none is present
4. Installs all required packages from the official repositories
5. Installs AUR packages (betterlockscreen, rofi-greenclip, playerctld-systemd-unit)
6. Backs up existing configuration directories to `~/.config.bak.<timestamp>`
7. Copies Trinity configurations into `~/.config/`
8. Copies Trinity Settings, wallpapers, and theme files
9. Applies the default theme (forest)
10. Builds the lockscreen cache

After installation, log out and log back in, or run `i3-msg restart`.

## Post-installation

Two values must be adjusted for the target machine before the setup is functional:

Monitor name, in `~/.config/i3/config`:

    xrandr --query | grep connected

Replace the output name (for example `HDMI-0`) in the `xrandr --output` line.

Network interface, in `~/.config/polybar/config.ini`:

    ip link | grep -v lo

Replace the interface name (for example `enp3s0`) in the `interface =` line.

## Key bindings

The modifier key is Super.

| Key | Action |
| --- | --- |
| `$mod+q` | Terminal (kitty) |
| `$mod+p` | Application launcher (rofi) |
| `$mod+F1` | Keybinding cheatsheet |
| `$mod+F2` | Trinity Settings |
| `$mod+Shift+t` | Change theme |
| `$mod+v` | Clipboard history |
| `$mod+Shift+x` | Power menu |
| `$mod+l` | Lock screen |
| `$mod+Shift+End` | Screenshot |
| `$mod+grave` | Scratchpad terminal |
| `$mod+h/j/k/l` | Focus left/down/up/right |
| `$mod+Shift+h/j/k/l` | Move window |
| `$mod+1..0` | Switch workspace |
| `$mod+Shift+1..0` | Move window to workspace |
| `$mod+f` | Toggle floating |
| `$mod+t` | Split horizontally |
| `$mod+Shift+v` | Split vertically |
| `$mod+r` | Resize mode |
| `$mod+g` | Gaps adjustment mode |

## Trinity Settings

Trinity Settings is a GTK3 application that reads and writes the live configuration files. It provides sections for Appearance, Compositor, Keybindings, Bar Modules, Display, Input Devices, Autostart, Kitty, Cava, Fastfetch, Dunst, Wallpaper, Colorscheme, Presets, Themes, Backup, Export, and Session.

Changes are staged and applied with an Apply button, which backs up the affected file before writing. A Save As action stores a full snapshot of all configuration files, and a Load action restores one. Presets are stored in `~/.config/trinity-presets/`.

## Directory layout

    trinity-rice/
    ├── install.sh
    ├── bootstrap.sh
    ├── i3/
    │   └── config
    ├── i3-scripts/
    │   ├── theme-switch.sh
    │   ├── theme-from-image.sh
    │   ├── theme-picker.sh
    │   ├── cheatsheet.sh
    │   ├── powermenu.sh
    │   ├── scratchpad.sh
    │   ├── fullshot.sh
    │   └── ...
    ├── polybar/
    │   ├── config.ini
    │   └── launch.sh
    ├── polybar-scripts/
    ├── picom/
    │   └── picom.conf
    ├── kitty/
    │   └── kitty.conf
    ├── rofi/
    │   ├── config.rasi
    │   └── theme.rasi
    ├── dunst/
    │   └── dunstrc
    ├── fish/
    │   ├── config.fish
    │   └── functions/
    ├── fastfetch/
    │   ├── config.jsonc
    │   └── trixity-ascii.txt
    ├── cava/
    │   └── config
    ├── trinity-settings/
    │   └── *.py, style.css
    ├── themes/
    │   └── themes.json
    └── wallpapers/
        └── *.png

## Notes

The T/A ASCII logo shown by fastfetch is generated from `trixity-ascii.txt` and recolored on every theme change.

Configuration files are backed up before every write by Trinity Settings and by the installer. Existing backups are located in `~/.config/trinity-backups/` and `~/.config.bak.<timestamp>/`.

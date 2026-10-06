#!/bin/bash
# ==========================================
# Trinity Rice — Smart Auto Installer
# ==========================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; N='\033[0m'
ok()   { echo -e "    ${G}✓${N} $1"; }
warn() { echo -e "    ${Y}⚠${N} $1"; }
err()  { echo -e "    ${R}✗${N} $1"; }
info() { echo -e "    ${B}→${N} $1"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Trinity Rice Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ==========================================
# 0. Checks
# ==========================================
command -v pacman >/dev/null || { err "Arch Linux required (pacman not found)"; exit 1; }
[ "$EUID" -eq 0 ] && { err "Don't run as root. Run as normal user."; exit 1; }
ok "Arch Linux detected"

# ==========================================
# 1. Update package DB
# ==========================================
echo ""
echo "==> 1/8 Updating package database..."
sudo pacman -Sy --noconfirm 2>&1 | tail -2
ok "Database updated"

# ==========================================
# 2. Determine GPU and kernel
# ==========================================
echo ""
echo "==> 2/8 Detecting hardware..."

GPU=""
if lspci | grep -qi "vga.*nvidia\|3d.*nvidia"; then
    GPU="nvidia"
    ok "NVIDIA GPU detected"
elif lspci | grep -qi "vga.*amd\|3d.*amd\|vga.*ati"; then
    GPU="amd"
    ok "AMD GPU detected"
elif lspci | grep -qi "vga.*intel\|3d.*intel"; then
    GPU="intel"
    ok "Intel GPU detected"
else
    GPU="unknown"
    warn "GPU not detected (will skip driver install)"
fi

KERNEL=$(uname -r)
case "$KERNEL" in
    *-zen*)    HEADERS="linux-zen-headers"; KNAME="linux-zen" ;;
    *-lts*)    HEADERS="linux-lts-headers"; KNAME="linux-lts" ;;
    *-hardened*) HEADERS="linux-hardened-headers"; KNAME="linux-hardened" ;;
    *)         HEADERS="linux-headers";    KNAME="linux" ;;
esac
ok "Running kernel: $KNAME ($HEADERS)"

# ==========================================
# 3. Install base packages (smart)
# ==========================================
echo ""
echo "==> 3/8 Installing base packages..."

BASE_PKGS=(
    base-devel git wget curl
)

TO_INSTALL=()
for pkg in "${BASE_PKGS[@]}"; do
    if ! pacman -Qi "$pkg" >/dev/null 2>&1; then
        TO_INSTALL+=("$pkg")
        info "+ $pkg"
    fi
done

if [ ${#TO_INSTALL[@]} -gt 0 ]; then
    sudo pacman -S --needed --noconfirm "${TO_INSTALL[@]}" 2>&1 | tail -2
    ok "Installed ${#TO_INSTALL[@]} base packages"
else
    ok "All base packages already installed"
fi

# ==========================================
# 4. Install kernel headers (for DKMS)
# ==========================================
echo ""
echo "==> 4/8 Kernel headers..."
if ! pacman -Qi "$HEADERS" >/dev/null 2>&1; then
    sudo pacman -S --needed --noconfirm "$HEADERS" 2>&1 | tail -2
    ok "Installed $HEADERS"
else
    ok "$HEADERS already installed"
fi

# ==========================================
# 5. Setup AUR helper (smart)
# ==========================================
echo ""
echo "==> 5/8 AUR helper..."

AUR_HELPER=""
if command -v paru >/dev/null; then
    AUR_HELPER="paru"
    ok "paru already installed"
elif command -v yay >/dev/null; then
    AUR_HELPER="yay"
    ok "yay already installed"
else
    info "Neither paru nor yay found — installing paru..."
    TMP=$(mktemp -d)
    git clone https://aur.archlinux.org/paru.git "$TMP/paru" 2>&1 | tail -1
    (cd "$TMP/paru" && makepkg -si --noconfirm)
    rm -rf "$TMP"
    AUR_HELPER="paru"
    ok "paru installed"
fi

# ==========================================
# 6. Install all runtime packages (smart)
# ==========================================
echo ""
echo "==> 6/8 Installing runtime packages..."

# Official packages — full Trinity stack
RUNTIME_PKGS=(
    # i3 core
    i3-wm i3lock-color
    # Bar + compositor
    polybar picom
    # Terminal
    kitty
    # Launcher
    rofi
    # Notifications
    dunst
    # Wallpaper
    feh imagemagick
    # Shell
    fish
    # Info
    fastfetch jq bc
    # Media
    mpv playerctl cava cmatrix
    # Clipboard + scripts
    socat xclip maim
    # GTK (Trinity Settings)
    python-gobject gtk3 python-pillow python-colorthief
    # Fonts + icons
    ttf-jetbrains-mono-nerd ttf-font-awesome
    papirus-icon-theme
    # Editor + tools
    micro less unzip libnewt
    # X11 utils
    xorg-xrandr xorg-xset xorg-xsetroot xorg-xprop
    # Audio
    pulseaudio
    # Network
    networkmanager network-manager-applet
    # Bluetooth
    bluez bluez-utils blueman
)

MISSING=()
for pkg in "${RUNTIME_PKGS[@]}"; do
    if ! pacman -Qi "$pkg" >/dev/null 2>&1; then
        MISSING+=("$pkg")
    fi
done

TOTAL=${#RUNTIME_PKGS[@]}
HAVE=$((TOTAL - ${#MISSING[@]}))
echo ""
info "Already installed: $HAVE / $TOTAL"

if [ ${#MISSING[@]} -gt 0 ]; then
    info "Installing ${#MISSING[@]} missing packages:"
    for pkg in "${MISSING[@]}"; do echo "      + $pkg"; done
    echo ""
    sudo pacman -S --needed --noconfirm "${MISSING[@]}" 2>&1 | tail -3
    ok "Runtime packages installed"
else
    ok "All runtime packages already installed"
fi

# ==========================================
# 7. GPU drivers (smart)
# ==========================================
echo ""
echo "==> 7/8 GPU drivers..."

case "$GPU" in
    nvidia)
        # NVIDIA Pascal and older — need 580xx from AUR
        if lspci | grep -qi "GeForce GTX 10[0-9][0-9]\|GeForce GTX 9[0-9][0-9]\|GeForce GT 7[0-9][0-9]"; then
            warn "Pascal/Maxwell detected — 580xx legacy driver required"
            if ! pacman -Qi nvidia-580xx-dkms >/dev/null 2>&1; then
                $AUR_HELPER -S --needed --noconfirm nvidia-580xx-dkms nvidia-580xx-utils lib32-nvidia-580xx-utils 2>&1 | tail -3
                ok "NVIDIA 580xx (legacy) installed"
            else
                ok "NVIDIA 580xx already installed"
            fi
            # Deep color fix for HDMI 240Hz
            echo "options nvidia-modeset hdmi_deepcolor=0" | sudo tee /etc/modprobe.d/nvidia-deepcolor.conf >/dev/null
            ok "HDMI deepcolor fix applied"
        else
            # Turing or newer — use official driver
            if ! pacman -Qi nvidia-dkms >/dev/null 2>&1; then
                sudo pacman -S --needed --noconfirm nvidia-dkms nvidia-utils lib32-nvidia-utils 2>&1 | tail -3
                ok "NVIDIA current driver installed"
            else
                ok "NVIDIA current driver already installed"
            fi
        fi
        ;;
    amd)
        ok "AMD uses mesa (included in system)"
        ;;
    intel)
        ok "Intel uses mesa (included in system)"
        ;;
    *)
        warn "Skipping GPU driver install"
        ;;
esac

# ==========================================
# 8. AUR packages (smart)
# ==========================================
echo ""
echo "==> 8/8 AUR packages..."

AUR_PKGS=(
    betterlockscreen
    rofi-greenclip
    playerctld-systemd-unit
)

AUR_MISSING=()
for pkg in "${AUR_PKGS[@]}"; do
    if ! pacman -Qi "$pkg" >/dev/null 2>&1; then
        AUR_MISSING+=("$pkg")
    fi
done

if [ ${#AUR_MISSING[@]} -gt 0 ]; then
    info "Installing ${#AUR_MISSING[@]} AUR packages..."
    $AUR_HELPER -S --needed --noconfirm "${AUR_MISSING[@]}" 2>&1 | tail -3 || \
        warn "Some AUR packages failed"
    ok "AUR packages done"
else
    ok "All AUR packages already installed"
fi

# Enable playerctld
systemctl --user enable --now playerctld 2>/dev/null || true

# ==========================================
# Configs install
# ==========================================
echo ""
echo "==> Installing Trinity configs..."

BACKUP="$HOME/.config.bak.$(date +%s)"
mkdir -p "$BACKUP"

for d in i3 polybar picom kitty rofi dunst fish fastfetch cava; do
    if [ -d "$SCRIPT_DIR/$d" ]; then
        [ -d "$HOME/.config/$d" ] && cp -r "$HOME/.config/$d" "$BACKUP/$d"
        mkdir -p "$HOME/.config/$d"
        cp -r "$SCRIPT_DIR/$d/"* "$HOME/.config/$d/" 2>/dev/null || true
        ok ".config/$d"
    fi
done

# Trinity Settings
[ -d "$SCRIPT_DIR/trinity-settings" ] && {
    mkdir -p "$HOME/Documents/trinity-settings"
    cp -r "$SCRIPT_DIR/trinity-settings/"* "$HOME/Documents/trinity-settings/"
    chmod +x "$HOME/Documents/trinity-settings/"*.py 2>/dev/null || true
    ok "trinity-settings"
}

# Wallpapers
[ -d "$SCRIPT_DIR/wallpapers" ] && {
    mkdir -p "$HOME/Pictures/wallpapers"
    cp -n "$SCRIPT_DIR/wallpapers/"* "$HOME/Pictures/wallpapers/" 2>/dev/null || true
    ok "wallpapers"
}

# Themes
[ -d "$SCRIPT_DIR/themes" ] && {
    mkdir -p "$HOME/dotfiles/themes"
    cp -r "$SCRIPT_DIR/themes/"* "$HOME/dotfiles/themes/" 2>/dev/null || true
    ok "themes"
}

# T/A logo
[ -f "$SCRIPT_DIR/fastfetch/trixity-ascii.txt" ] && {
    mkdir -p "$HOME/.config/fastfetch"
    cp "$SCRIPT_DIR/fastfetch/trixity-ascii.txt" "$HOME/.config/fastfetch/"
    ok "T/A logo"
}

# i3 scripts
[ -d "$SCRIPT_DIR/i3-scripts" ] && {
    mkdir -p "$HOME/.config/i3/scripts"
    cp -r "$SCRIPT_DIR/i3-scripts/"* "$HOME/.config/i3/scripts/" 2>/dev/null || true
    chmod +x "$HOME/.config/i3/scripts/"* 2>/dev/null || true
    ok "i3 scripts"
}

# Polybar scripts
[ -d "$SCRIPT_DIR/polybar-scripts" ] && {
    mkdir -p "$HOME/.config/polybar/scripts"
    cp -r "$SCRIPT_DIR/polybar-scripts/"* "$HOME/.config/polybar/scripts/" 2>/dev/null || true
    chmod +x "$HOME/.config/polybar/scripts/"* 2>/dev/null || true
    ok "polybar scripts"
}

chmod +x "$HOME/.config/polybar/launch.sh" 2>/dev/null || true

# ==========================================
# First-run setup
# ==========================================
echo ""
echo "==> First-run setup..."

# Theme
[ -f "$HOME/.config/i3/scripts/theme-switch.sh" ] && {
    bash "$HOME/.config/i3/scripts/theme-switch.sh" forest >/dev/null 2>&1 || true
    ok "Applied forest theme"
}

# Wallpaper + lockscreen
[ -f "$HOME/Pictures/wallpapers/forest.png" ] && {
    feh --bg-scale "$HOME/Pictures/wallpapers/forest.png" 2>/dev/null || true
    info "Building lockscreen cache (~30s)..."
    betterlockscreen -u "$HOME/Pictures/wallpapers/forest.png" --fx blur 2>/dev/null || true
    ok "Lockscreen ready"
}

# Fish shell
if command -v fish >/dev/null; then
    grep -q "$(which fish)" /etc/shells 2>/dev/null || \
        echo "$(which fish)" | sudo tee -a /etc/shells >/dev/null
    if [ "$SHELL" != "$(which fish)" ]; then
        read -p "    Set fish as default shell? [y/N] " -n 1 -r
        echo ""
        [[ $REPLY =~ ^[Yy]$ ]] && chsh -s "$(which fish)"
    fi
fi

# ==========================================
# Done
# ==========================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Trinity Installed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Log out and log back in (or: i3-msg restart)"
echo ""
echo "⚠️  Edit for YOUR hardware:"
echo ""
echo "  Monitor name:"
echo "    xrandr --query | grep connected"
echo "    Edit ~/.config/i3/config: xrandr --output HDMI-0 ..."
echo ""
echo "  Network interface:"
echo "    ip link | grep -v lo"
echo "    Edit ~/.config/polybar/config.ini: interface = enp3s0"
echo ""
echo "Key binds:"
echo "  \$mod+q       → Terminal"
echo "  \$mod+p       → Rofi"
echo "  \$mod+F2      → Trinity Settings"
echo "  \$mod+Shift+t → Change theme"
echo "  \$mod+F1      → Cheatsheet"
echo ""
echo "Backup: $BACKUP"

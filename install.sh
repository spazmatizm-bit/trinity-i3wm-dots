#!/bin/bash
# ==========================================
# Trinity Rice — Auto Installer
# ==========================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Trinity Rice Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ==========================================
# 1. Check Arch
# ==========================================
echo "==> 1/8 Checking system..."

if ! command -v pacman >/dev/null; then
    echo "    ✗ ERROR: pacman not found. Trinity requires Arch Linux."
    exit 1
fi

if [ "$EUID" -eq 0 ]; then
    echo "    ✗ ERROR: Don't run as root. Run as normal user."
    exit 1
fi

echo "    ✓ pacman found"

# ==========================================
# 2. base-devel + git
# ==========================================
echo ""
echo "==> 2/8 Installing base packages..."

if ! pacman -Qi base-devel >/dev/null 2>&1; then
    sudo pacman -S --needed --noconfirm base-devel
fi

if ! command -v git >/dev/null; then
    sudo pacman -S --needed --noconfirm git
fi

echo "    ✓ base-devel, git ready"

# ==========================================
# 3. AUR helper
# ==========================================
echo ""
echo "==> 3/8 Setting up AUR helper..."

AUR_HELPER=""
if command -v paru >/dev/null; then
    AUR_HELPER="paru"
    echo "    ✓ paru found"
elif command -v yay >/dev/null; then
    AUR_HELPER="yay"
    echo "    ✓ yay found"
else
    echo "    Installing paru from AUR (may take 2-3 min)..."
    TMP=$(mktemp -d)
    git clone https://aur.archlinux.org/paru.git "$TMP/paru"
    (cd "$TMP/paru" && makepkg -si --noconfirm)
    rm -rf "$TMP"
    AUR_HELPER="paru"
    echo "    ✓ paru installed"
fi

# ==========================================
# 4. Official packages
# ==========================================
echo ""
echo "==> 4/8 Installing official packages..."
echo "    (~30 packages, this takes 3-5 min)"

PACKAGES=(
    i3-wm i3lock-color polybar picom
    kitty fish micro less unzip
    rofi dunst
    feh imagemagick
    fastfetch jq bc
    mpv playerctl cava cmatrix
    socat xclip maim
    python-gobject gtk3 python-pillow python-colorthief
    ttf-jetbrains-mono-nerd ttf-font-awesome
    papirus-icon-theme
    libnewt
)

sudo pacman -S --needed --noconfirm "${PACKAGES[@]}" 2>&1 | tail -3
echo "    ✓ Official packages installed"

# ==========================================
# 5. AUR packages
# ==========================================
echo ""
echo "==> 5/8 Installing AUR packages..."

"$AUR_HELPER" -S --needed --noconfirm \
    betterlockscreen \
    rofi-greenclip \
    playerctld-systemd-unit 2>&1 | tail -3 || \
    echo "    ⚠ Some AUR packages failed"

systemctl --user enable --now playerctld 2>/dev/null || true
echo "    ✓ AUR packages installed"

# ==========================================
# 6. Backup
# ==========================================
echo ""
echo "==> 6/8 Backing up existing configs..."

BACKUP="$HOME/.config.bak.$(date +%s)"
mkdir -p "$BACKUP"

for d in i3 polybar picom kitty rofi dunst fish fastfetch cava; do
    if [ -d "$HOME/.config/$d" ]; then
        cp -r "$HOME/.config/$d" "$BACKUP/$d"
    fi
done
echo "    ✓ Backup: $BACKUP"

# ==========================================
# 7. Install Trinity configs
# ==========================================
echo ""
echo "==> 7/8 Installing Trinity configs..."

for d in i3 polybar picom kitty rofi dunst fish fastfetch cava; do
    if [ -d "$SCRIPT_DIR/$d" ]; then
        mkdir -p "$HOME/.config/$d"
        cp -r "$SCRIPT_DIR/$d/"* "$HOME/.config/$d/" 2>/dev/null || true
        echo "    ✓ .config/$d"
    fi
done

if [ -d "$SCRIPT_DIR/trinity-settings" ]; then
    mkdir -p "$HOME/Documents/trinity-settings"
    cp -r "$SCRIPT_DIR/trinity-settings/"* "$HOME/Documents/trinity-settings/"
    chmod +x "$HOME/Documents/trinity-settings/"*.py 2>/dev/null || true
    echo "    ✓ trinity-settings"
fi

if [ -d "$SCRIPT_DIR/wallpapers" ]; then
    mkdir -p "$HOME/Pictures/wallpapers"
    cp -n "$SCRIPT_DIR/wallpapers/"* "$HOME/Pictures/wallpapers/" 2>/dev/null || true
    echo "    ✓ wallpapers"
fi

if [ -f "$SCRIPT_DIR/fastfetch/trixity-ascii.txt" ]; then
    mkdir -p "$HOME/.config/fastfetch"
    cp "$SCRIPT_DIR/fastfetch/trixity-ascii.txt" "$HOME/.config/fastfetch/"
fi

if [ -d "$SCRIPT_DIR/themes" ]; then
    mkdir -p "$HOME/dotfiles/themes"
    cp -r "$SCRIPT_DIR/themes/"* "$HOME/dotfiles/themes/" 2>/dev/null || true
fi

if [ -d "$SCRIPT_DIR/i3-scripts" ]; then
    mkdir -p "$HOME/.config/i3/scripts"
    cp -r "$SCRIPT_DIR/i3-scripts/"* "$HOME/.config/i3/scripts/" 2>/dev/null || true
    chmod +x "$HOME/.config/i3/scripts/"* 2>/dev/null || true
fi

if [ -d "$SCRIPT_DIR/polybar-scripts" ]; then
    mkdir -p "$HOME/.config/polybar/scripts"
    cp -r "$SCRIPT_DIR/polybar-scripts/"* "$HOME/.config/polybar/scripts/" 2>/dev/null || true
    chmod +x "$HOME/.config/polybar/scripts/"* 2>/dev/null || true
fi

chmod +x "$HOME/.config/polybar/launch.sh" 2>/dev/null || true

# ==========================================
# 8. First-run setup
# ==========================================
echo ""
echo "==> 8/8 First-run setup..."

if [ -f "$HOME/.config/i3/scripts/theme-switch.sh" ]; then
    echo "    Applying default theme: forest"
    bash "$HOME/.config/i3/scripts/theme-switch.sh" forest >/dev/null 2>&1 || true
fi

if [ -f "$HOME/Pictures/wallpapers/forest.png" ]; then
    feh --bg-scale "$HOME/Pictures/wallpapers/forest.png" 2>/dev/null || true
    echo "    Building lockscreen cache (~30s)..."
    betterlockscreen -u "$HOME/Pictures/wallpapers/forest.png" --fx blur 2>/dev/null || true
fi

# Fish as default shell
if command -v fish >/dev/null; then
    if ! grep -q "$(which fish)" /etc/shells 2>/dev/null; then
        echo "$(which fish)" | sudo tee -a /etc/shells >/dev/null
    fi
    read -p "    Set fish as default shell? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        chsh -s "$(which fish)"
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
echo "Next steps:"
echo "  1. Log out and back in (or: i3-msg restart)"
echo ""
echo "⚠️  EDIT FOR YOUR HARDWARE:"
echo ""
echo "  Monitor name (i3 config):"
echo "    xrandr --query | grep connected"
echo "    Change 'HDMI-0' in ~/.config/i3/config"
echo ""
echo "  Network interface (Polybar):"
echo "    ip link | grep -v lo"
echo "    Change 'enp3s0' in ~/.config/polybar/config.ini"
echo ""
echo "Key binds (Super = Mod):"
echo "  \$mod+q       → Terminal (kitty)"
echo "  \$mod+p       → Rofi launcher"
echo "  \$mod+F2      → Trinity Settings"
echo "  \$mod+Shift+t → Change theme"
echo "  \$mod+F1      → Cheatsheet"
echo "  \$mod+v       → Clipboard"
echo "  \$mod+Shift+x → Power menu"
echo "  \$mod+l       → Lock screen"
echo ""
echo "Backup of your old configs: $BACKUP"

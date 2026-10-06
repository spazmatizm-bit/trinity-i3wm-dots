#!/bin/bash
# ==========================================
# Trinity Rice — Installer
# ==========================================
set -euo pipefail

DRY_RUN=0
SKIP_GPU=0
ASSUME_YES=0

for arg in "$@"; do
    case "$arg" in
        --dry-run)  DRY_RUN=1 ;;
        --skip-gpu) SKIP_GPU=1 ;;
        --yes|-y)   ASSUME_YES=1 ;;
        --help|-h)
            cat <<EOF
Usage: ./install.sh [options]

  --dry-run     show what would happen, change nothing
  --skip-gpu    skip GPU driver install
  --yes, -y     no prompts
  --help, -h    this
EOF
            exit 0 ;;
        *) echo "unknown flag: $arg"; exit 1 ;;
    esac
done

# no curl | bash
if [ ! -t 0 ]; then
    echo "Don't pipe this into bash."
    echo "Clone the repo and run ./install.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HOME/trinity-install-$(date +%Y%m%d-%H%M%S).log"

exec > >(tee -a "$LOG") 2>&1

G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; N='\033[0m'
ok()   { echo -e "    ${G}ok${N}   $1"; }
warn() { echo -e "    ${Y}warn${N} $1"; }
err()  { echo -e "    ${R}fail${N} $1"; }
info() { echo -e "    ${B}..${N}   $1"; }
die()  { err "$1"; exit 1; }

run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "    [dry] $*"
    else
        "$@"
    fi
}

echo "Trinity Rice installer"
echo "log: $LOG"
echo ""

# ==========================================
# sanity
# ==========================================
echo "== sanity"

command -v pacman >/dev/null || die "this is for arch (no pacman found)"
[ "$EUID" -eq 0 ] && die "don't run as root"

REQUIRED_DIRS=(i3 polybar picom kitty rofi dunst fish fastfetch cava)
MISSING_DIRS=()
for d in "${REQUIRED_DIRS[@]}"; do
    [ -d "$SCRIPT_DIR/$d" ] || MISSING_DIRS+=("$d")
done

if [ ${#MISSING_DIRS[@]} -gt 0 ]; then
    err "config dirs missing next to install.sh:"
    for d in "${MISSING_DIRS[@]}"; do echo "        - $d"; done
    echo ""
    echo "    script_dir: $SCRIPT_DIR"
    echo "    contents:"
    ls -la "$SCRIPT_DIR" | sed 's/^/        /'
    echo ""
    die "run install.sh from the repo root, not from somewhere else"
fi
ok "found all config dirs"

ping -c1 -W2 archlinux.org >/dev/null 2>&1 || warn "no internet, package installs will fail"

AVAIL=$(df -BG "$HOME" | awk 'NR==2 {gsub("G","",$4); print $4}')
[ "${AVAIL:-0}" -lt 5 ] && warn "only ${AVAIL}G free in \$HOME"

# ==========================================
# pacman db
# ==========================================
echo ""
echo "== pacman -Sy"
run sudo pacman -Sy --noconfirm
ok "done"

# ==========================================
# hardware
# ==========================================
echo ""
echo "== hardware"

GPU="unknown"
if lspci | grep -qi "vga.*nvidia\|3d.*nvidia"; then
    GPU="nvidia"; ok "nvidia"
elif lspci | grep -qi "vga.*amd\|3d.*amd\|vga.*ati"; then
    GPU="amd"; ok "amd"
elif lspci | grep -qi "vga.*intel\|3d.*intel"; then
    GPU="intel"; ok "intel"
else
    warn "gpu not detected"
fi

KERNEL=$(uname -r)
case "$KERNEL" in
    *-zen*)      HEADERS="linux-zen-headers";     KNAME="linux-zen" ;;
    *-lts*)      HEADERS="linux-lts-headers";     KNAME="linux-lts" ;;
    *-hardened*) HEADERS="linux-hardened-headers"; KNAME="linux-hardened" ;;
    *)           HEADERS="linux-headers";          KNAME="linux" ;;
esac
ok "kernel: $KNAME ($HEADERS)"

# ==========================================
# base packages
# ==========================================
echo ""
echo "== base packages"

BASE_PKGS=(base-devel git wget curl)
TO_INSTALL=()
for pkg in "${BASE_PKGS[@]}"; do
    pacman -Qi "$pkg" >/dev/null 2>&1 || TO_INSTALL+=("$pkg")
done

if [ ${#TO_INSTALL[@]} -gt 0 ]; then
    info "installing: ${TO_INSTALL[*]}"
    run sudo pacman -S --needed --noconfirm "${TO_INSTALL[@]}"
    ok "done"
else
    ok "already there"
fi

# ==========================================
# kernel headers
# ==========================================
echo ""
echo "== kernel headers"
if ! pacman -Qi "$HEADERS" >/dev/null 2>&1; then
    run sudo pacman -S --needed --noconfirm "$HEADERS"
    ok "installed $HEADERS"
else
    ok "$HEADERS already there"
fi

# ==========================================
# aur helper
# ==========================================
echo ""
echo "== aur helper"
AUR_HELPER=""
if command -v paru >/dev/null; then
    AUR_HELPER="paru"; ok "paru"
elif command -v yay >/dev/null; then
    AUR_HELPER="yay"; ok "yay"
else
    info "building paru"
    TMP=$(mktemp -d)
    git clone https://aur.archlinux.org/paru.git "$TMP/paru"
    if (cd "$TMP/paru" && makepkg -si --noconfirm); then
        AUR_HELPER="paru"
        ok "paru installed"
    else
        rm -rf "$TMP"
        die "couldn't build paru. check base-devel and pacman-key"
    fi
    rm -rf "$TMP"
fi

# ==========================================
# runtime packages
# ==========================================
echo ""
echo "== runtime packages"

RUNTIME_PKGS=(
    i3-wm i3lock-color
    polybar picom
    kitty
    rofi
    dunst
    feh imagemagick
    fish
    fastfetch jq bc
    mpv playerctl cava cmatrix
    socat xclip maim
    python-gobject gtk3 python-pillow python-colorthief
    ttf-jetbrains-mono-nerd ttf-font-awesome
    papirus-icon-theme
    micro less unzip libnewt
    xorg-xrandr xorg-xset xorg-xsetroot xorg-xprop
    pulseaudio
    networkmanager network-manager-applet
    bluez bluez-utils blueman
)

MISSING=()
for pkg in "${RUNTIME_PKGS[@]}"; do
    pacman -Qi "$pkg" >/dev/null 2>&1 || MISSING+=("$pkg")
done

TOTAL=${#RUNTIME_PKGS[@]}
HAVE=$((TOTAL - ${#MISSING[@]}))
info "$HAVE / $TOTAL already installed"

if [ ${#MISSING[@]} -gt 0 ]; then
    for pkg in "${MISSING[@]}"; do echo "        + $pkg"; done
    if ! run sudo pacman -S --needed --noconfirm "${MISSING[@]}"; then
        err "some packages failed, check the log"
        warn "continuing anyway"
    else
        ok "installed"
    fi
else
    ok "nothing to do"
fi

# ==========================================
# gpu drivers
# ==========================================
echo ""
echo "== gpu drivers"
if [ "$SKIP_GPU" -eq 1 ]; then
    warn "skipped (--skip-gpu)"
else
    case "$GPU" in
        nvidia)
            if lspci | grep -qi "GeForce GTX 10[0-9][0-9]\|GeForce GTX 9[0-9][0-9]\|GeForce GT 7[0-9][0-9]"; then
                warn "pascal/maxwell -> legacy 580xx"
                if ! pacman -Qi nvidia-580xx-dkms >/dev/null 2>&1; then
                    run $AUR_HELPER -S --needed --noconfirm nvidia-580xx-dkms nvidia-580xx-utils lib32-nvidia-580xx-utils
                    ok "580xx installed"
                else
                    ok "580xx already there"
                fi
                echo "options nvidia-modeset hdmi_deepcolor=0" | run sudo tee /etc/modprobe.d/nvidia-deepcolor.conf >/dev/null
                ok "hdmi deepcolor fix"
            else
                if ! pacman -Qi nvidia-dkms >/dev/null 2>&1; then
                    run sudo pacman -S --needed --noconfirm nvidia-dkms nvidia-utils lib32-nvidia-utils
                    ok "nvidia current installed"
                else
                    ok "nvidia current already there"
                fi
            fi
            ;;
        amd|intel) ok "$GPU uses mesa" ;;
        *) warn "unknown gpu, skipping" ;;
    esac
fi

# ==========================================
# aur packages
# ==========================================
echo ""
echo "== aur packages"
AUR_PKGS=(betterlockscreen rofi-greenclip playerctld-systemd-unit)
AUR_MISSING=()
for pkg in "${AUR_PKGS[@]}"; do
    pacman -Qi "$pkg" >/dev/null 2>&1 || AUR_MISSING+=("$pkg")
done

if [ ${#AUR_MISSING[@]} -gt 0 ]; then
    info "${AUR_MISSING[*]}"
    if ! run $AUR_HELPER -S --needed --noconfirm "${AUR_MISSING[@]}"; then
        warn "some aur packages failed"
    else
        ok "done"
    fi
else
    ok "already there"
fi

[ "$DRY_RUN" -eq 0 ] && (systemctl --user enable --now playerctld 2>/dev/null || true)

# ==========================================
# configs
# ==========================================
echo ""
echo "== configs"

EXISTING=()
for d in "${REQUIRED_DIRS[@]}"; do
    [ -d "$HOME/.config/$d" ] && EXISTING+=("$d")
done

if [ ${#EXISTING[@]} -gt 0 ] && [ "$ASSUME_YES" -eq 0 ]; then
    warn "existing: ${EXISTING[*]}"
    read -p "    overwrite? (backup goes to ~/.config.bak.*) [y/N] " -n 1 -r
    echo ""
    [[ $REPLY =~ ^[Yy]$ ]] || die "aborted"
fi

BACKUP="$HOME/.config.bak.$(date +%s)"
run mkdir -p "$BACKUP"

for d in "${REQUIRED_DIRS[@]}"; do
    [ -d "$HOME/.config/$d" ] && run cp -r "$HOME/.config/$d" "$BACKUP/$d"
    run mkdir -p "$HOME/.config/$d"

    if [ "$DRY_RUN" -eq 1 ]; then
        echo "    [dry] cp -r $SCRIPT_DIR/$d/* ~/.config/$d/"
        continue
    fi

    if cp -r "$SCRIPT_DIR/$d/"* "$HOME/.config/$d/"; then
        ok ".config/$d"
    else
        err ".config/$d failed to copy"
    fi
done

# verify the files that matter
echo ""
echo "    -- checking critical files"
CRITICAL_FILES=(
    "$HOME/.config/i3/config"
    "$HOME/.config/polybar/config.ini"
    "$HOME/.config/picom/picom.conf"
    "$HOME/.config/kitty/kitty.conf"
    "$HOME/.config/rofi/config.rasi"
)
MISSING_CRIT=0
for f in "${CRITICAL_FILES[@]}"; do
    if [ -f "$f" ]; then
        ok "$f"
    else
        err "missing: $f"
        MISSING_CRIT=$((MISSING_CRIT+1))
    fi
done

if [ "$MISSING_CRIT" -gt 0 ] && [ "$DRY_RUN" -eq 0 ]; then
    err "critical configs missing - i3 will boot to a black screen"
    err "check the log: $LOG"
    exit 1
fi

[ -d "$SCRIPT_DIR/trinity-settings" ] && {
    run mkdir -p "$HOME/Documents/trinity-settings"
    run cp -r "$SCRIPT_DIR/trinity-settings/"* "$HOME/Documents/trinity-settings/"
    [ "$DRY_RUN" -eq 0 ] && chmod +x "$HOME/Documents/trinity-settings/"*.py 2>/dev/null || true
    ok "trinity-settings"
}

[ -d "$SCRIPT_DIR/wallpapers" ] && {
    run mkdir -p "$HOME/Pictures/wallpapers"
    run cp -n "$SCRIPT_DIR/wallpapers/"* "$HOME/Pictures/wallpapers/" 2>/dev/null || true
    ok "wallpapers"
}

[ -d "$SCRIPT_DIR/themes" ] && {
    run mkdir -p "$HOME/dotfiles/themes"
    run cp -r "$SCRIPT_DIR/themes/"* "$HOME/dotfiles/themes/"
    ok "themes"
}

[ -d "$SCRIPT_DIR/i3-scripts" ] && {
    run mkdir -p "$HOME/.config/i3/scripts"
    run cp -r "$SCRIPT_DIR/i3-scripts/"* "$HOME/.config/i3/scripts/"
    [ "$DRY_RUN" -eq 0 ] && chmod +x "$HOME/.config/i3/scripts/"* 2>/dev/null || true
    ok "i3 scripts"
}

[ -d "$SCRIPT_DIR/polybar-scripts" ] && {
    run mkdir -p "$HOME/.config/polybar/scripts"
    run cp -r "$SCRIPT_DIR/polybar-scripts/"* "$HOME/.config/polybar/scripts/"
    [ "$DRY_RUN" -eq 0 ] && chmod +x "$HOME/.config/polybar/scripts/"* 2>/dev/null || true
    ok "polybar scripts"
}

[ "$DRY_RUN" -eq 0 ] && chmod +x "$HOME/.config/polybar/launch.sh" 2>/dev/null || true

# ==========================================
# first run
# ==========================================
if [ "$DRY_RUN" -eq 0 ]; then
    echo ""
    echo "== first run"

    [ -f "$HOME/.config/i3/scripts/theme-switch.sh" ] && {
        bash "$HOME/.config/i3/scripts/theme-switch.sh" forest >/dev/null 2>&1 || true
        ok "theme: forest"
    }

    [ -f "$HOME/Pictures/wallpapers/forest.png" ] && {
        feh --bg-scale "$HOME/Pictures/wallpapers/forest.png" 2>/dev/null || true
        info "building lockscreen cache, takes a moment"
        betterlockscreen -u "$HOME/Pictures/wallpapers/forest.png" --fx blur 2>/dev/null || true
        ok "lockscreen ready"
    }

    if command -v fish >/dev/null; then
        grep -q "$(which fish)" /etc/shells 2>/dev/null || \
            echo "$(which fish)" | sudo tee -a /etc/shells >/dev/null
        if [ "$SHELL" != "$(which fish)" ] && [ "$ASSUME_YES" -eq 0 ]; then
            read -p "    set fish as default shell? [y/N] " -n 1 -r
            echo ""
            [[ $REPLY =~ ^[Yy]$ ]] && chsh -s "$(which fish)"
        fi
    fi
fi

# ==========================================
# done
# ==========================================
echo ""
if [ "$DRY_RUN" -eq 1 ]; then
    echo "dry run done, nothing changed"
else
    echo "done. log out and back in, or: i3-msg restart"
fi
echo ""
echo "log:    $LOG"
echo "backup: $BACKUP"
echo ""
echo "you probably need to edit for your hardware:"
echo "  monitors:  xrandr --query | grep connected"
echo "             -> ~/.config/i3/config"
echo "  network:   ip link | grep -v lo"
echo "             -> ~/.config/polybar/config.ini"

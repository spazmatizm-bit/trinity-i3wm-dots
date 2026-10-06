#!/bin/bash
# ==========================================
# i3 Rice Settings — TUI control panel
# ==========================================
set -e

I3_CONF="$HOME/.config/i3/config"
PICOM_CONF="$HOME/.config/picom/picom.conf"
POLY_CONF="$HOME/.config/polybar/config.ini"
KITTY_CONF="$HOME/.config/kitty/kitty.conf"
DUNST_CONF="$HOME/.config/dunst/dunstrc"
BACKUP_DIR="$HOME/.config/rice-backups"

mkdir -p "$BACKUP_DIR"

# ==========================================
# Helpers
# ==========================================

backup() {
    local file="$1"
    if [ -f "$file" ]; then
        local name=$(basename "$file")
        cp "$file" "$BACKUP_DIR/${name}.$(date +%Y%m%d_%H%M%S)"
        # Keep only last 20 backups per file
        ls -t "$BACKUP_DIR/${name}."* 2>/dev/null | tail -n +21 | xargs -r rm
    fi
}

msg() {
    whiptail --title "$1" --msgbox "$2" 12 60
}

confirm() {
    whiptail --title "$1" --yesno "$2" 10 60
}

# Get current value from config file
get_val() {
    local file="$1" key="$2"
    grep -E "^\s*${key}\s*=" "$file" 2>/dev/null | head -1 | sed -E "s/^\s*${key}\s*=\s*//" | tr -d '"' | tr -d ';'
}

# Set value in config file (replace or append)
set_val() {
    local file="$1" key="$2" value="$3"
    backup "$file"
    if grep -qE "^\s*${key}\s*=" "$file"; then
        sed -i -E "s|^\s*${key}\s*=.*|${key} = ${value}|" "$file"
    else
        echo "${key} = ${value}" >> "$file"
    fi
}

# Reload i3 with validation
reload_i3() {
    if i3 -C -c "$I3_CONF" 2>/tmp/i3check.log; then
        i3-msg reload >/dev/null 2>&1
        return 0
    else
        msg "i3 config error" "Config is invalid:\n\n$(cat /tmp/i3check.log)"
        return 1
    fi
}

# Reload picom
reload_picom() {
    pkill picom 2>/dev/null || true
    sleep 0.5
    picom --config "$PICOM_CONF" -b 2>/dev/null || \
        notify-send "Picom failed" "Check $PICOM_CONF"
}

# Reload polybar
reload_polybar() {
    killall polybar 2>/dev/null || true
    sleep 0.5
    if [ -x "$HOME/.config/polybar/launch.sh" ]; then
        "$HOME/.config/polybar/launch.sh" >/dev/null 2>&1
    else
        polybar main >/dev/null 2>&1 &
    fi
}

# Reload kitty (only affects new windows)
reload_kitty() {
    kitty @ --to unix:/tmp/kitty-socket load-config 2>/dev/null || true
}

# ==========================================
# Sections
# ==========================================

section_appearance() {
    while true; do
        CHOICE=$(whiptail --title "Appearance" --menu "Choose:" 20 70 10 \
            "1" "Wallpaper" \
            "2" "Gaps (inner / outer)" \
            "3" "Border width" \
            "4" "Font size (bar)" \
            "5" "Colorscheme" \
            "6" "Back" \
            3>&1 1>&2 2>&3) || return

        case "$CHOICE" in
            "1") appearance_wallpaper ;;
            "2") appearance_gaps ;;
            "3") appearance_border ;;
            "4") appearance_bar_font ;;
            "5") appearance_colorscheme ;;
            "6") return ;;
        esac
    done
}

appearance_wallpaper() {
    # Find wallpapers
    WALL_DIR="$HOME/Pictures/wallpapers"
    if [ ! -d "$WALL_DIR" ]; then
        msg "Wallpaper" "Directory not found:\n$WALL_DIR"
        return
    fi

    FILES=$(find "$WALL_DIR" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) 2>/dev/null)
    if [ -z "$FILES" ]; then
        msg "Wallpaper" "No images in $WALL_DIR"
        return
    fi

    # Build menu
    MENU=()
    i=1
    while IFS= read -r f; do
        MENU+=("$i" "$(basename "$f")")
        i=$((i + 1))
    done <<< "$FILES"

    CHOICE=$(whiptail --title "Wallpaper" --menu "Choose:" 20 70 10 "${MENU[@]}" 3>&1 1>&2 2>&3) || return

    WALL=$(echo "$FILES" | sed -n "${CHOICE}p")
    [ -f "$WALL" ] || return

    feh --bg-scale "$WALL"

    # Save path to i3 config
    backup "$I3_CONF"
    sed -i '/feh --bg-scale/d' "$I3_CONF"
    echo "exec --no-startup-id feh --bg-scale $WALL" >> "$I3_CONF"

    msg "Wallpaper" "Applied: $(basename "$WALL")"
}

appearance_gaps() {
    CUR_INNER=$(grep -oP '^gaps inner \K\d+' "$I3_CONF" | head -1)
    CUR_OUTER=$(grep -oP '^gaps outer \K\d+' "$I3_CONF" | head -1)
    CUR_INNER=${CUR_INNER:-0}
    CUR_OUTER=${CUR_OUTER:-0}

    NEW_INNER=$(whiptail --title "Gaps" --inputbox "Inner gaps:" 10 60 "$CUR_INNER" 3>&1 1>&2 2>&3) || return
    NEW_OUTER=$(whiptail --title "Gaps" --inputbox "Outer gaps:" 10 60 "$CUR_OUTER" 3>&1 1>&2 2>&3) || return

    if ! [[ "$NEW_INNER" =~ ^[0-9]+$ ]] || ! [[ "$NEW_OUTER" =~ ^[0-9]+$ ]]; then
        msg "Error" "Must be non-negative integers"
        return
    fi

    backup "$I3_CONF"
    # Remove old gap lines
    sed -i '/^gaps inner /d' "$I3_CONF"
    sed -i '/^gaps outer /d' "$I3_CONF"
    # Add new
    echo "gaps inner $NEW_INNER" >> "$I3_CONF"
    echo "gaps outer $NEW_OUTER" >> "$I3_CONF"

    i3-msg gaps inner all set "$NEW_INNER" >/dev/null 2>&1 || true
    i3-msg gaps outer all set "$NEW_OUTER" >/dev/null 2>&1 || true

    msg "Gaps" "Applied: inner=$NEW_INNER outer=$NEW_OUTER"
}

appearance_border() {
    CUR=$(grep -oP '^default_border pixel \K\d+' "$I3_CONF" | head -1)
    CUR=${CUR:-2}

    NEW=$(whiptail --title "Border width" --inputbox "Pixel width (0-10):" 10 60 "$CUR" 3>&1 1>&2 2>&3) || return

    if ! [[ "$NEW" =~ ^[0-9]+$ ]]; then
        msg "Error" "Must be a number"
        return
    fi

    backup "$I3_CONF"
    sed -i '/^default_border /d' "$I3_CONF"
    sed -i '/^default_floating_border /d' "$I3_CONF"
    echo "default_border pixel $NEW" >> "$I3_CONF"
    echo "default_floating_border pixel $NEW" >> "$I3_CONF"

    if reload_i3; then
        msg "Border" "Applied: pixel $NEW"
    fi
}

appearance_bar_font() {
    CUR=$(grep -oP '^font-0 = "[^:]+:size=\K\d+' "$POLY_CONF" | head -1)
    CUR=${CUR:-10}

    NEW=$(whiptail --title "Bar font size" --inputbox "Font size (8-16):" 10 60 "$CUR" 3>&1 1>&2 2>&3) || return

    if ! [[ "$NEW" =~ ^[0-9]+$ ]] || [ "$NEW" -lt 6 ] || [ "$NEW" -gt 20 ]; then
        msg "Error" "Must be 6-20"
        return
    fi

    backup "$POLY_CONF"
    sed -i -E "s|(font-0 = \"[^:]+:size=)[0-9]+|\1${NEW}|" "$POLY_CONF"
    sed -i -E "s|(font-1 = \"[^:]+(:style=[A-Za-z]+)?:size=)[0-9]+|\1${NEW}|" "$POLY_CONF"

    reload_polybar
    msg "Font" "Bar font size set to $NEW"
}

appearance_colorscheme() {
    CHOICE=$(whiptail --title "Colorscheme" --menu "Apply preset colorscheme:" 15 70 5 \
        "1" "Nord (blue/gray)" \
        "2" "Gruvbox (warm brown/orange)" \
        "3" "Catppuccin Mocha (purple/pink)" \
        "4" "Cancel" \
        3>&1 1>&2 2>&3) || return

    case "$CHOICE" in
        "1") apply_preset nord ;;
        "2") apply_preset gruvbox ;;
        "3") apply_preset catppuccin ;;
        "4") return ;;
    esac
}

section_compositor() {
    while true; do
        CHOICE=$(whiptail --title "Compositor (Picom)" --menu "Choose:" 20 70 10 \
            "1" "Toggle blur" \
            "2" "Toggle shadows" \
            "3" "Toggle rounded corners" \
            "4" "Blur strength" \
            "5" "Corner radius" \
            "6" "Restart picom" \
            "7" "Back" \
            3>&1 1>&2 2>&3) || return

        case "$CHOICE" in
            "1") compositor_toggle_blur ;;
            "2") compositor_toggle_shadows ;;
            "3") compositor_toggle_corners ;;
            "4") compositor_blur_strength ;;
            "5") compositor_corner_radius ;;
            "6") reload_picom; msg "Picom" "Restarted" ;;
            "7") return ;;
        esac
    done
}

compositor_toggle_blur() {
    if grep -qE "^\s*method\s*=" "$PICOM_CONF" 2>/dev/null; then
        # Blur is on — comment it out
        backup "$PICOM_CONF"
        sed -i 's/^\(\s*method\s*=.*\)/# \1/' "$PICOM_CONF"
        sed -i 's/^\(\s*blur-background-exclude\s*\)/# \1/' "$PICOM_CONF"
        msg "Blur" "Blur DISABLED"
    else
        # Blur off — add it back
        backup "$PICOM_CONF"
        cat >> "$PICOM_CONF" <<'EOF'

blur {
  method = "dual_kawase";
  strength = 4;
};
blur-background-exclude = [
  "window_type = 'dock'",
  "window_type = 'desktop'"
];
EOF
        msg "Blur" "Blur ENABLED"
    fi
    reload_picom
}

compositor_toggle_shadows() {
    CUR=$(get_val "$PICOM_CONF" "shadow")
    if [ "$CUR" = "true" ]; then
        set_val "$PICOM_CONF" "shadow" "false"
        msg "Shadows" "Shadows DISABLED"
    else
        set_val "$PICOM_CONF" "shadow" "true"
        msg "Shadows" "Shadows ENABLED"
    fi
    reload_picom
}

compositor_toggle_corners() {
    CUR=$(get_val "$PICOM_CONF" "corner-radius")
    if [ -n "$CUR" ] && [ "$CUR" != "0" ]; then
        set_val "$PICOM_CONF" "corner-radius" "0"
        msg "Corners" "Rounded corners DISABLED"
    else
        set_val "$PICOM_CONF" "corner-radius" "8"
        msg "Corners" "Rounded corners ENABLED (radius 8)"
    fi
    reload_picom
}

compositor_blur_strength() {
    CUR=$(grep -oP 'strength\s*=\s*\K\d+' "$PICOM_CONF" | head -1)
    CUR=${CUR:-4}

    NEW=$(whiptail --title "Blur strength" --inputbox "Strength (1-20):" 10 60 "$CUR" 3>&1 1>&2 2>&3) || return

    if ! [[ "$NEW" =~ ^[0-9]+$ ]] || [ "$NEW" -lt 1 ] || [ "$NEW" -gt 20 ]; then
        msg "Error" "Must be 1-20"
        return
    fi

    backup "$PICOM_CONF"
    sed -i -E "s|(strength\s*=\s*)[0-9]+|\1${NEW}|" "$PICOM_CONF"

    reload_picom
    msg "Blur" "Strength set to $NEW"
}

compositor_corner_radius() {
    CUR=$(get_val "$PICOM_CONF" "corner-radius")
    CUR=${CUR:-8}

    NEW=$(whiptail --title "Corner radius" --inputbox "Radius in px (0-30):" 10 60 "$CUR" 3>&1 1>&2 2>&3) || return

    if ! [[ "$NEW" =~ ^[0-9]+$ ]] || [ "$NEW" -gt 30 ]; then
        msg "Error" "Must be 0-30"
        return
    fi

    set_val "$PICOM_CONF" "corner-radius" "$NEW"
    reload_picom
    msg "Corners" "Radius set to $NEW"
}

section_bar() {
    while true; do
        CHOICE=$(whiptail --title "Bar (Polybar)" --menu "Choose:" 20 70 10 \
            "1" "Restart polybar" \
            "2" "Edit config in editor" \
            "3" "Toggle modules" \
            "4" "Change bar height" \
            "5" "Back" \
            3>&1 1>&2 2>&3) || return

        case "$CHOICE" in
            "1") reload_polybar; msg "Bar" "Polybar restarted" ;;
            "2") micro "$POLY_CONF" ;;
            "3") bar_toggle_modules ;;
            "4") bar_height ;;
            "5") return ;;
        esac
    done
}

bar_toggle_modules() {
    # Get current modules-right
    CUR=$(grep -oP '^modules-right = \K.*' "$POLY_CONF" | head -1)

    # Show checklist
    MENU=()
    for m in i3 date volume cpu memory pulseaudio battery network systray music-ctl; do
        if echo "$CUR" | grep -qw "$m"; then
            MENU+=("$m" "" "on")
        else
            MENU+=("$m" "" "off")
        fi
    done

    SELECTED=$(whiptail --title "Modules (right side)" --checklist "Select modules:" 20 70 12 "${MENU[@]}" 3>&1 1>&2 2>&3) || return

    NEW=$(echo "$SELECTED" | tr -d '"')
    backup "$POLY_CONF"
    sed -i "s|^modules-right = .*|modules-right = $NEW|" "$POLY_CONF"

    reload_polybar
    msg "Modules" "Applied: $NEW"
}

bar_height() {
    CUR=$(get_val "$POLY_CONF" "height")
    CUR=${CUR:-24}

    NEW=$(whiptail --title "Bar height" --inputbox "Height in px (18-40):" 10 60 "$CUR" 3>&1 1>&2 2>&3) || return

    if ! [[ "$NEW" =~ ^[0-9]+$ ]] || [ "$NEW" -lt 16 ] || [ "$NEW" -gt 50 ]; then
        msg "Error" "Must be 16-50"
        return
    fi

    set_val "$POLY_CONF" "height" "$NEW"
    reload_polybar
    msg "Bar" "Height set to $NEW"
}

section_presets() {
    CHOICE=$(whiptail --title "Presets" --menu "Apply configuration preset:" 20 75 8 \
        "1" "Minimal — no effects, thin bar, no gaps" \
        "2" "Standard — Nord, blur, moderate effects" \
        "3" "Maximal — heavy blur, big corners, all modules" \
        "4" "Cancel" \
        3>&1 1>&2 2>&3) || return

    case "$CHOICE" in
        "1") apply_preset minimal ;;
        "2") apply_preset standard ;;
        "3") apply_preset maximal ;;
        "4") return ;;
    esac
}

apply_preset() {
    local preset="$1"
    # Backup everything
    for f in "$I3_CONF" "$PICOM_CONF" "$POLY_CONF"; do
        backup "$f"
    done

    case "$preset" in
        minimal)
            # i3: no gaps, thin border
            sed -i '/^gaps inner /d; /^gaps outer /d' "$I3_CONF"
            echo "gaps inner 0" >> "$I3_CONF"
            echo "gaps outer 0" >> "$I3_CONF"
            sed -i 's/^default_border .*/default_border pixel 1/' "$I3_CONF"

            # Picom: minimal
            sed -i 's/^shadow = .*/shadow = false/' "$PICOM_CONF"
            set_val "$PICOM_CONF" "corner-radius" "0"
            # Remove blur block
            python3 -c "
import re
p='$PICOM_CONF'
src=open(p).read()
src=re.sub(r'\n?blur\s*\{.*?\};\s*','\n',src,flags=re.S)
src=re.sub(r'\n?blur-background-exclude\s*=\s*\[.*?\];\s*','\n',src,flags=re.S)
open(p,'w').write(src)
"

            reload_picom
            reload_i3
            msg "Preset" "Minimal applied"
            ;;

        standard)
            sed -i '/^gaps inner /d; /^gaps outer /d' "$I3_CONF"
            echo "gaps inner 8" >> "$I3_CONF"
            echo "gaps outer 4" >> "$I3_CONF"
            sed -i 's/^default_border .*/default_border pixel 2/' "$I3_CONF"

            set_val "$PICOM_CONF" "shadow" "true"
            set_val "$PICOM_CONF" "corner-radius" "8"

            reload_picom
            reload_i3
            msg "Preset" "Standard applied"
            ;;

        maximal)
            sed -i '/^gaps inner /d; /^gaps outer /d' "$I3_CONF"
            echo "gaps inner 12" >> "$I3_CONF"
            echo "gaps outer 8" >> "$I3_CONF"
            sed -i 's/^default_border .*/default_border pixel 3/' "$I3_CONF"

            set_val "$PICOM_CONF" "shadow" "true"
            set_val "$PICOM_CONF" "corner-radius" "16"

            # Ensure blur is on
            if ! grep -q "^blur {" "$PICOM_CONF"; then
                cat >> "$PICOM_CONF" <<'EOF'

blur {
  method = "dual_kawase";
  strength = 8;
};
EOF
            fi

            reload_picom
            reload_i3
            msg "Preset" "Maximal applied"
            ;;
    esac
}

section_session() {
    while true; do
        CHOICE=$(whiptail --title "Session" --menu "Choose:" 20 70 8 \
            "1" "Reload i3" \
            "2" "Restart i3" \
            "3" "Restart picom" \
            "4" "Restart polybar" \
            "5" "Log out" \
            "6" "Back" \
            3>&1 1>&2 2>&3) || return

        case "$CHOICE" in
            "1") reload_i3; msg "Session" "i3 reloaded" ;;
            "2") i3-msg restart >/dev/null; exit 0 ;;
            "3") reload_picom; msg "Session" "Picom restarted" ;;
            "4") reload_polybar; msg "Session" "Polybar restarted" ;;
            "5") if confirm "Log out" "Log out of i3?"; then i3-msg exit; fi ;;
            "6") return ;;
        esac
    done
}

section_backup() {
    while true; do
        CHOICE=$(whiptail --title "Backup" --menu "Choose:" 20 70 8 \
            "1" "Create full backup now" \
            "2" "List backups" \
            "3" "Restore latest backup" \
            "4" "Open backup folder" \
            "5" "Back" \
            3>&1 1>&2 2>&3) || return

        case "$CHOICE" in
            "1") create_full_backup ;;
            "2") list_backups ;;
            "3") restore_latest ;;
            "4") xdg-open "$BACKUP_DIR" 2>/dev/null || msg "Backup" "Folder: $BACKUP_DIR" ;;
            "5") return ;;
        esac
    done
}

create_full_backup() {
    for f in "$I3_CONF" "$PICOM_CONF" "$POLY_CONF" "$KITTY_CONF" "$DUNST_CONF"; do
        [ -f "$f" ] && backup "$f"
    done
    msg "Backup" "Full backup created in:\n$BACKUP_DIR"
}

list_backups() {
    ls -1 "$BACKUP_DIR" | tail -30 | whiptail --title "Backups (last 30)" --scrolltext --msgbox "$(ls -1 "$BACKUP_DIR" | tail -30)" 25 80
}

restore_latest() {
    if confirm "Restore" "Restore latest backup of EVERYTHING?\n\nThis will overwrite current configs."; then
        for name in config picom.conf config.ini kitty.conf dunstrc; do
            latest=$(ls -t "$BACKUP_DIR/${name}."* 2>/dev/null | head -1)
            [ -z "$latest" ] && continue
            case "$name" in
                "config")      [ -f "$I3_CONF" ] && cp "$latest" "$I3_CONF" ;;
                "picom.conf")  [ -f "$PICOM_CONF" ] && cp "$latest" "$PICOM_CONF" ;;
                "config.ini")  [ -f "$POLY_CONF" ] && cp "$latest" "$POLY_CONF" ;;
                "kitty.conf")  [ -f "$KITTY_CONF" ] && cp "$latest" "$KITTY_CONF" ;;
                "dunstrc")     [ -f "$DUNST_CONF" ] && cp "$latest" "$DUNST_CONF" ;;
            esac
        done
        reload_i3
        reload_picom
        reload_polybar
        msg "Restore" "Restored and reloaded."
    fi
}

# ==========================================
# Main menu
# ==========================================

while true; do
    CHOICE=$(whiptail --title "i3 Rice Settings" --menu "Choose a category:" 22 75 12 \
        "1" "Appearance (wallpaper, gaps, fonts, colors)" \
        "2" "Compositor (blur, shadows, corners)" \
        "3" "Bar (polybar, modules, height)" \
        "4" "Presets (minimal / standard / maximal)" \
        "5" "Session (reload, restart, logout)" \
        "6" "Backup (create / restore)" \
        "7" "Exit" \
        3>&1 1>&2 2>&3) || exit 0

    case "$CHOICE" in
        "1") section_appearance ;;
        "2") section_compositor ;;
        "3") section_bar ;;
        "4") section_presets ;;
        "5") section_session ;;
        "6") section_backup ;;
        "7") exit 0 ;;
    esac
done

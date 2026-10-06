"""Save/load full config presets — snapshots of all Trinity configs."""
import os
import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

PRESETS_DIR = Path.home() / ".config/trinity-presets"
PRESETS_DIR.mkdir(parents=True, exist_ok=True)

# Files to snapshot
CONFIG_FILES = [
    ".config/i3/config",
    ".config/polybar/config.ini",
    ".config/picom/picom.conf",
    ".config/kitty/kitty.conf",
    ".config/rofi/config.rasi",
    ".config/rofi/theme.rasi",
    ".config/dunst/dunstrc",
    ".config/fish/config.fish",
    ".config/fish/functions/fish_prompt.fish",
    ".config/fastfetch/config.jsonc",
    ".config/cava/config",
    ".config/theme-current",
    ".config/theme-current.json",
    "dotfiles/themes/themes.json",
]

def list_presets():
    """Return list of (name, timestamp, path)."""
    result = []
    for entry in sorted(PRESETS_DIR.iterdir(), reverse=True):
        if entry.is_dir():
            meta_file = entry / "meta.json"
            meta = {}
            if meta_file.exists():
                try: meta = json.loads(meta_file.read_text())
                except: pass
            result.append({
                "name": entry.name,
                "path": str(entry),
                "timestamp": meta.get("saved_at", ""),
                "description": meta.get("description", ""),
                "theme": meta.get("theme", ""),
            })
    return result


def save_preset(name, description=""):
    """Save current configs as a preset."""
    # Sanitize name
    safe_name = "".join(c for c in name if c.isalnum() or c in "-_ ").strip()
    if not safe_name:
        safe_name = datetime.now().strftime("%Y%m%d_%H%M%S")

    dest = PRESETS_DIR / safe_name
    if dest.exists():
        # Add timestamp to avoid overwrite
        dest = PRESETS_DIR / f"{safe_name}_{datetime.now().strftime('%H%M%S')}"

    dest.mkdir(parents=True)

    # Copy each config file
    home = Path.home()
    copied = 0
    for rel in CONFIG_FILES:
        src = home / rel
        if src.exists():
            # Preserve dir structure inside preset
            dst = dest / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1

    # Save metadata
    theme = ""
    try:
        theme = (home / ".config/theme-current").read_text().strip()
    except: pass

    meta = {
        "name": safe_name,
        "description": description,
        "theme": theme,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files_count": copied,
    }
    (dest / "meta.json").write_text(json.dumps(meta, indent=2))

    return dest, copied


def load_preset(name):
    """Load preset — copy files back to their original locations."""
    src = PRESETS_DIR / name
    if not src.is_dir():
        raise FileNotFoundError(f"Preset not found: {name}")

    # Backup current configs first
    backup_dir = Path.home() / ".config/trinity-backups" / f"pre-restore-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    home = Path.home()
    restored = 0
    for rel in CONFIG_FILES:
        src_file = src / rel
        if src_file.exists():
            dst = home / rel
            # Backup current
            if dst.exists():
                bak = backup_dir / rel
                bak.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, bak)
            # Restore
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst)
            restored += 1

    # Apply — reload everything
    time.sleep(0.3)
    subprocess.run(["i3-msg", "reload"], stderr=subprocess.DEVNULL)
    subprocess.run(["killall", "polybar"], stderr=subprocess.DEVNULL)
    time.sleep(0.4)
    launcher = home / ".config/polybar/launch.sh"
    if launcher.exists():
        subprocess.Popen(["bash", str(launcher)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "dunst"], stderr=subprocess.DEVNULL)
    time.sleep(0.2)
    subprocess.Popen(["dunst"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "picom"], stderr=subprocess.DEVNULL)
    time.sleep(0.2)
    subprocess.Popen(["picom", "--config", str(home / ".config/picom/picom.conf"), "-b"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Reload kitty
    subprocess.run(["kitty", "@", "--to", "unix:/tmp/kitty-socket", "load-config"], stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-SIGUSR1", "kitty"], stderr=subprocess.DEVNULL)

    return restored, str(backup_dir)


def delete_preset(name):
    """Delete a preset."""
    src = PRESETS_DIR / name
    if src.is_dir():
        shutil.rmtree(src)
        return True
    return False


def preset_exists(name):
    return (PRESETS_DIR / name).is_dir()

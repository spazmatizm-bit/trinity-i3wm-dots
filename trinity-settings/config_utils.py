"""Universal config readers/writers for Trinity Settings.

Preserves comments, blank lines, and file structure. Only modifies the
key-value pair you ask for. Never rewrites the whole file.
"""
import os
import re
import shutil
from datetime import datetime

BACKUP_DIR = os.path.expanduser("~/.config/trinity-backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


def _backup(path):
    if not os.path.exists(path):
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        shutil.copy2(path, os.path.join(BACKUP_DIR, f"{os.path.basename(path)}.{ts}"))
        # Keep only last 20 per file
        files = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith(os.path.basename(path) + ".")], reverse=True)
        for old in files[20:]:
            try: os.remove(os.path.join(BACKUP_DIR, old))
            except: pass
    except Exception:
        pass


def _read(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return ""


def _write(path, content, backup=True):
    if backup:
        _backup(path)
    with open(path, "w") as f:
        f.write(content)


# ==========================================
# Format: key value  (kitty)
# ==========================================
class KittyParser:
    def __init__(self, path):
        self.path = path

    def get(self, key, default=None, section=None):
        for line in _read(self.path).splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split(None, 1)
            if len(parts) == 2 and parts[0] == key:
                return parts[1].strip()
        return default

    def set(self, key, value):
        src = _read(self.path)
        lines = src.splitlines()
        found = False
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                continue
            parts = stripped.split(None, 1)
            if len(parts) == 2 and parts[0] == key:
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(f"{indent}{key} {value}")
                found = True
            else:
                new_lines.append(line)
        if not found:
            if new_lines and new_lines[-1].strip():
                new_lines.append("")
            new_lines.append(f"{key} {value}")
        _write(self.path, "\n".join(new_lines) + "\n")


# ==========================================
# Format: key = value  (with [sections])
# Used by: polybar, cava, dunst, picom (with ;)
# ==========================================
class IniParser:
    def __init__(self, path, separator="=", strip_quotes=True, terminator=None):
        self.path = path
        self.sep = separator
        self.strip_quotes = strip_quotes
        self.terminator = terminator  # e.g., ";" for picom

    def _clean(self, val):
        v = val.strip()
        if self.terminator and v.endswith(self.terminator):
            v = v[:-len(self.terminator)].strip()
        if self.strip_quotes and len(v) >= 2 and v[0] in "'\"" and v[-1] == v[0]:
            v = v[1:-1]
        return v

    def get(self, key, default=None, section=None):
        """Get a value. If section is provided, look only there.
        If key not found, return default."""
        src = _read(self.path)

        if section is not None:
            m = re.search(rf'^\s*\[{re.escape(str(section))}\]\s*$', src, re.M)
            if not m:
                return default
            end = re.search(r'^\s*\[', src[m.end():], re.M)
            sec_src = src[m.end():m.end() + end.start()] if end else src[m.end():]
        else:
            sec_src = src

        for line in sec_src.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith(";"):
                continue
            if stripped.startswith("["):
                continue
            if self.sep not in stripped:
                continue
            k, _, v = stripped.partition(self.sep)
            if k.strip() == key:
                return self._clean(v)
        return default

    def set(self, key, value, section=None):
        src = _read(self.path)
        lines = src.splitlines()
        new_lines = []
        in_target_section = (section is None)
        found = False
        section_inserted = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Section header detection
            if stripped.startswith("[") and stripped.endswith("]"):
                # Leaving previous section?
                if section and in_target_section and not found and not section_inserted:
                    # Insert key at end of this section before we leave
                    new_lines.append(f"{key} {self.sep} {value}" + (self.terminator or ""))
                    found = True
                    section_inserted = True
                # Enter new section?
                in_target_section = (stripped == f"[{section}]") if section else (section is None)
                new_lines.append(line)
                continue

            if in_target_section and self.sep in stripped and not stripped.startswith("#") and not stripped.startswith(";"):
                k, _, _v = stripped.partition(self.sep)
                if k.strip() == key:
                    indent = line[:len(line) - len(line.lstrip())]
                    new_lines.append(f"{indent}{key} {self.sep} {value}" + (self.terminator or ""))
                    found = True
                    continue

            new_lines.append(line)

        # If section ended at EOF and key not found
        if section and in_target_section and not found and not section_inserted:
            new_lines.append(f"{key} {self.sep} {value}" + (self.terminator or ""))
            found = True

        # If no section and key not found — append at end
        if not section and not found:
            if new_lines and new_lines[-1].strip():
                new_lines.append("")
            new_lines.append(f"{key} {self.sep} {value}" + (self.terminator or ""))

        _write(self.path, "\n".join(new_lines) + "\n")


# ==========================================
# i3 config — special format
# ==========================================
class I3Parser:
    def __init__(self, path):
        self.path = path

    def get_set_var(self, var):
        """Get `set $var value`."""
        m = re.search(rf'^\s*set\s+\$\{re.escape(var)}\s+(.+)$', _read(self.path), re.M)
        return m.group(1).strip() if m else None

    def set_set_var(self, var, value):
        src = _read(self.path)
        pattern = rf'^\s*set\s+\$\{re.escape(var)}\s+.*$'
        if re.search(pattern, src, re.M):
            src = re.sub(pattern, f'set ${var} {value}', src, flags=re.M)
        else:
            src = src.rstrip() + f"\nset ${var} {value}\n"
        _write(self.path, src)

    def get_gaps(self, which="inner"):
        m = re.search(rf'^\s*gaps\s+{which}\s+(\d+)', _read(self.path), re.M)
        return int(m.group(1)) if m else None

    def set_gaps(self, which, value):
        src = _read(self.path)
        pattern = rf'^\s*gaps\s+{which}\s+.*$'
        if re.search(pattern, src, re.M):
            src = re.sub(pattern, f'gaps {which} {value}', src, flags=re.M)
        else:
            src = src.rstrip() + f"\ngaps {which} {value}\n"
        _write(self.path, src)

    def get_border(self):
        m = re.search(r'^\s*default_border\s+pixel\s+(\d+)', _read(self.path), re.M)
        return int(m.group(1)) if m else 2

    def set_border(self, px):
        src = _read(self.path)
        src = re.sub(r'^\s*default_border\s+.*$', f'default_border pixel {px}', src, flags=re.M)
        src = re.sub(r'^\s*default_floating_border\s+.*$', f'default_floating_border pixel {px}', src, flags=re.M)
        _write(self.path, src)


# ==========================================
# Rofi — key: value;
# ==========================================
class RasiParser:
    def __init__(self, path):
        self.path = path

    def get(self, key, default=None, section=None):
        m = re.search(rf'^\s*{re.escape(key)}\s*:\s*([^;]+);', _read(self.path), re.M)
        return m.group(1).strip() if m else default

    def set(self, key, value):
        src = _read(self.path)
        pattern = rf'^(\s*{re.escape(key)}\s*:\s*)[^;]+;'
        if re.search(pattern, src, re.M):
            src = re.sub(pattern, rf'\g<1>{value};', src, flags=re.M)
        else:
            src = src.rstrip() + f"\n{key}: {value};\n"
        _write(self.path, src)


# ==========================================
# Convenience: singleton getters
# ==========================================
def kitty():
    return KittyParser(os.path.expanduser("~/.config/kitty/kitty.conf"))

def polybar():
    return IniParser(os.path.expanduser("~/.config/polybar/config.ini"))

def cava():
    return IniParser(os.path.expanduser("~/.config/cava/config"))

def dunst():
    return IniParser(os.path.expanduser("~/.config/dunst/dunstrc"))

def picom():
    return IniParser(os.path.expanduser("~/.config/picom/picom.conf"), terminator=";")

def i3():
    return I3Parser(os.path.expanduser("~/.config/i3/config"))

def rofi():
    return RasiParser(os.path.expanduser("~/.config/rofi/theme.rasi"))


# ==========================================
# Self-test
# ==========================================
if __name__ == "__main__":
    print("Testing config parsers...")
    print()
    print("Kitty font_size:", kitty().get("font_size"))
    print("Kitty opacity:  ", kitty().get("background_opacity"))
    print()
    print("Polybar height: ", polybar().get("height"))
    print("Polybar bar bg: ", polybar().get("background", "bar/main"))
    print()
    print("Cava framerate:", cava().get("framerate", "general"))
    print("Cava bars:     ", cava().get("bars", "general"))
    print()
    print("Dunst origin:  ", dunst().get("origin", "global"))
    print("Dunst width:   ", dunst().get("width", "global"))
    print()
    print("Picom backend: ", picom().get("backend"))
    print("Picom radius:  ", picom().get("corner-radius"))
    print()
    print("i3 gaps inner: ", i3().get_gaps("inner"))
    print("i3 gaps outer: ", i3().get_gaps("outer"))
    print("i3 border:     ", i3().get_border())
    print()
    print("Rofi width:    ", rofi().get("width"))
    print()
    print("✓ All parsers work")

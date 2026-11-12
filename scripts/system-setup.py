#!/usr/bin/env python3
"""One-time root setup for the currently installed SDDM theme."""

import os
from pathlib import Path
import pwd
import re
import shutil
import sys

THEME = Path("/usr/share/sddm/themes/sddm")
CONFIG = THEME / "theme.conf"
METADATA = THEME / "metadata.desktop"
BACKUP = THEME / "theme.conf.noctail-backup"
DATA_DIR = Path("/var/lib/noctail-sddm-wallpaper")
DEST = DATA_DIR / "background.png"


def install(username):
    user = pwd.getpwnam(username)
    if not CONFIG.is_file():
        raise RuntimeError("Expected SDDM theme is not installed")
    if not METADATA.is_file() or "QtVersion=6" not in METADATA.read_text():
        raise RuntimeError("Expected Qt 6 Noctalia SDDM theme is not installed")
    original = CONFIG.read_text()
    if not BACKUP.exists():
        shutil.copy2(CONFIG, BACKUP)
    DATA_DIR.mkdir(mode=0o755, parents=True, exist_ok=True)
    os.chown(DATA_DIR, user.pw_uid, user.pw_gid)
    os.chmod(DATA_DIR, 0o755)
    if not DEST.exists():
        old = THEME / "Assets/background.png"
        shutil.copy2(old, DEST)
    os.chown(DEST, user.pw_uid, user.pw_gid)
    os.chmod(DEST, 0o644)
    value = "background=file://" + str(DEST)
    updated, count = re.subn(r"(?m)^background=.*$", value, original, count=1)
    if count != 1:
        raise RuntimeError("theme.conf has no background entry")
    CONFIG.write_text(updated)
    print("SDDM background now uses", DEST)


def uninstall():
    if not BACKUP.is_file():
        raise RuntimeError("No theme.conf backup found")
    shutil.copy2(BACKUP, CONFIG)
    BACKUP.unlink()
    print("Original SDDM theme.conf restored; wallpaper data was kept at", DATA_DIR)


if __name__ == "__main__":
    try:
        if os.geteuid() != 0:
            raise RuntimeError("Run this script as root")
        if len(sys.argv) == 3 and sys.argv[1] == "install":
            install(sys.argv[2])
        elif len(sys.argv) == 2 and sys.argv[1] == "uninstall":
            uninstall()
        else:
            raise RuntimeError("Usage: system-setup.py install USER | uninstall")
    except (OSError, RuntimeError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

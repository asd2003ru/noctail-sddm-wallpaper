#!/usr/bin/env python3
"""One-time root setup for the currently installed SDDM theme."""

import os
from pathlib import Path
import pwd
import re
import shutil
import sys
import tempfile

THEME = Path("/usr/share/sddm/themes/sddm")
CONFIG = THEME / "theme.conf"
METADATA = THEME / "metadata.desktop"
BACKUP = THEME / "theme.conf.noctail-backup"
DATA_DIR = Path("/var/lib/noctail-sddm-wallpaper")
DEST = DATA_DIR / "background.jpg"


def install(username, source_path):
    user = pwd.getpwnam(username)
    source = Path(source_path).expanduser().resolve(strict=True)
    if source.suffix.lower() not in (".jpg", ".jpeg"):
        raise RuntimeError("Installation requires a JPEG wallpaper (.jpg or .jpeg)")
    with source.open("rb") as stream:
        if stream.read(3) != b"\xff\xd8\xff":
            raise RuntimeError("Installation wallpaper is not a valid JPEG")
    if not CONFIG.is_file():
        raise RuntimeError("Expected SDDM theme is not installed")
    if not METADATA.is_file() or "QtVersion=6" not in METADATA.read_text():
        raise RuntimeError("Expected Qt 6 Noctalia SDDM theme is not installed")
    original = CONFIG.read_text()
    value = "background=file://" + str(DEST)
    updated, count = re.subn(r"(?m)^background=.*$", value, original, count=1)
    if count != 1:
        raise RuntimeError("theme.conf has no background entry")
    if not BACKUP.exists():
        shutil.copy2(CONFIG, BACKUP)
    DATA_DIR.mkdir(mode=0o755, parents=True, exist_ok=True)
    os.chown(DATA_DIR, user.pw_uid, user.pw_gid)
    os.chmod(DATA_DIR, 0o755)
    fd, name = tempfile.mkstemp(prefix=".background-", suffix=".jpg", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "wb") as target, source.open("rb") as source_stream:
            shutil.copyfileobj(source_stream, target)
            target.flush()
            os.fsync(target.fileno())
        os.chown(name, user.pw_uid, user.pw_gid)
        os.chmod(name, 0o644)
        os.replace(name, DEST)
    finally:
        if os.path.exists(name):
            os.unlink(name)
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
        if len(sys.argv) == 4 and sys.argv[1] == "install":
            install(sys.argv[2], sys.argv[3])
        elif len(sys.argv) == 2 and sys.argv[1] == "uninstall":
            uninstall()
        else:
            raise RuntimeError("Usage: system-setup.py install USER JPEG_PATH | uninstall")
    except (OSError, RuntimeError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

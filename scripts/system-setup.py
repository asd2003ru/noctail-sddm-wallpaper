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
SDDM_CONFIG = Path("/etc/sddm.conf")
SDDM_CONFIG_BACKUP = Path("/etc/sddm.conf.noctail-backup")
SDDM_CONFIG_ABSENT = Path("/etc/sddm.conf.noctail-absent")
DATA_DIR = Path("/var/lib/noctail-sddm-wallpaper")
DEST = DATA_DIR / "background.jpg"
DATA_CONFIG = DATA_DIR / "theme.conf"


def select_theme():
    original = SDDM_CONFIG.read_text() if SDDM_CONFIG.exists() else ""
    section = re.search(r"(?ms)^\[Theme\][ \t]*\n(?P<body>.*?)(?=^\[|\Z)", original)
    if section:
        body, count = re.subn(r"(?m)^Current=.*$", "Current=sddm", section.group("body"), count=1)
        if not count:
            body = "Current=sddm\n" + body
        updated = original[:section.start("body")] + body + original[section.end("body"):]
    else:
        updated = original.rstrip("\n") + "\n\n[Theme]\nCurrent=sddm\n"
    if updated == original:
        return
    if not SDDM_CONFIG_BACKUP.exists() and not SDDM_CONFIG_ABSENT.exists():
        if SDDM_CONFIG.exists():
            shutil.copy2(SDDM_CONFIG, SDDM_CONFIG_BACKUP)
        else:
            SDDM_CONFIG_ABSENT.touch()
    SDDM_CONFIG.write_text(updated)


def install(username, source_path, theme_source_path):
    user = pwd.getpwnam(username)
    source = Path(source_path).expanduser().resolve(strict=True)
    theme_source = Path(theme_source_path).resolve(strict=True)
    theme_metadata = theme_source / "metadata.desktop"
    if not theme_metadata.is_file() or "Name=Noctalia" not in theme_metadata.read_text() or "QtVersion=6" not in theme_metadata.read_text():
        raise RuntimeError("Bundled Noctalia SDDM theme is incomplete")
    if not (theme_source / "Main.qml").is_file() or not (theme_source / "theme.conf").is_file():
        raise RuntimeError("Bundled Noctalia SDDM theme is incomplete")
    if source.suffix.lower() not in (".jpg", ".jpeg"):
        raise RuntimeError("Installation requires a JPEG wallpaper (.jpg or .jpeg)")
    with source.open("rb") as stream:
        if stream.read(3) != b"\xff\xd8\xff":
            raise RuntimeError("Installation wallpaper is not a valid JPEG")
    if THEME.is_symlink():
        raise RuntimeError("Existing SDDM theme path is a symlink; cannot install safely")
    if not THEME.exists():
        shutil.copytree(theme_source, THEME)
    if not CONFIG.is_file() or not METADATA.is_file() or "Name=Noctalia" not in METADATA.read_text() or "QtVersion=6" not in METADATA.read_text():
        raise RuntimeError("Existing sddm theme is not the Noctalia Qt 6 theme")
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
    config_fd, config_name = tempfile.mkstemp(prefix=".theme-", suffix=".conf", dir=DATA_DIR)
    try:
        with os.fdopen(config_fd, "w") as target:
            target.write(updated)
            target.flush()
            os.fsync(target.fileno())
        os.chown(config_name, user.pw_uid, user.pw_gid)
        os.chmod(config_name, 0o644)
        os.replace(config_name, DATA_CONFIG)
    finally:
        if os.path.exists(config_name):
            os.unlink(config_name)
    link_name = THEME / ".theme.conf.noctail-link"
    link_name.unlink(missing_ok=True)
    os.symlink(DATA_CONFIG, link_name)
    os.replace(link_name, CONFIG)
    select_theme()
    print("SDDM background now uses", DEST)


def uninstall():
    if not BACKUP.is_file():
        raise RuntimeError("No theme.conf backup found")
    CONFIG.unlink(missing_ok=True)
    shutil.copy2(BACKUP, CONFIG)
    BACKUP.unlink()
    if SDDM_CONFIG_BACKUP.exists():
        shutil.copy2(SDDM_CONFIG_BACKUP, SDDM_CONFIG)
        SDDM_CONFIG_BACKUP.unlink()
    elif SDDM_CONFIG_ABSENT.exists():
        SDDM_CONFIG.unlink(missing_ok=True)
        SDDM_CONFIG_ABSENT.unlink()
    print("Original SDDM theme.conf restored; wallpaper data was kept at", DATA_DIR)


if __name__ == "__main__":
    try:
        if os.geteuid() != 0:
            raise RuntimeError("Run this script as root")
        if len(sys.argv) == 5 and sys.argv[1] == "install":
            install(sys.argv[2], sys.argv[3], sys.argv[4])
        elif len(sys.argv) == 2 and sys.argv[1] == "uninstall":
            uninstall()
        else:
            raise RuntimeError("Usage: system-setup.py install USER JPEG_PATH THEME_DIR | uninstall")
    except (OSError, RuntimeError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

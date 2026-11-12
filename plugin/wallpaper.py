#!/usr/bin/env python3
"""Unprivileged wallpaper state and image updater for the SDDM plugin."""

import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

DEST = Path("/var/lib/noctail-sddm-wallpaper/background.jpg")
DATA_CONFIG = DEST.parent / "theme.conf"
STATE_HOME = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
STATE_DIR = STATE_HOME / "noctail-sddm-wallpaper"
STATE_FILE = STATE_DIR / "state.json"


def state_dir():
    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STATE_DIR, 0o700)


def load_state():
    try:
        data = json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    return {
        "mode": data.get("mode") if data.get("mode") in ("sync", "manual") else "sync",
        "connector": data.get("connector") if isinstance(data.get("connector"), str) else "",
        "image": data.get("image") if isinstance(data.get("image"), str) else "",
        "colors_sync": data.get("colors_sync") if isinstance(data.get("colors_sync"), bool) else True,
    }


def save_state(data):
    state_dir()
    fd, name = tempfile.mkstemp(prefix=".state-", dir=STATE_DIR)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, 0o600)
        os.replace(name, STATE_FILE)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def require_installed():
    if not DEST.parent.is_dir() or not os.access(DEST.parent, os.W_OK):
        raise RuntimeError("SDDM integration is missing; run scripts/install.sh")


def validate_jpeg(source):
    source = Path(source).expanduser().resolve(strict=True)
    if not source.is_file():
        raise RuntimeError("Selected path is not a file")
    if source.suffix.lower() not in (".jpg", ".jpeg"):
        if source.suffix.lower() == ".png":
            raise RuntimeError("PNG is not supported. Choose a JPEG wallpaper (.jpg or .jpeg).")
        raise RuntimeError("Only JPEG wallpapers (.jpg or .jpeg) are supported.")
    with source.open("rb") as stream:
        if stream.read(3) != b"\xff\xd8\xff":
            raise RuntimeError("Selected file is not a valid JPEG")
    return source


def copy_image(source):
    require_installed()
    source = validate_jpeg(source)
    fd, name = tempfile.mkstemp(prefix=".background-", suffix=".jpg", dir=DEST.parent)
    try:
        with os.fdopen(fd, "wb") as target, source.open("rb") as original:
            shutil.copyfileobj(original, target)
            target.flush()
            os.fsync(target.fileno())
        os.chmod(name, 0o644)
        os.replace(name, DEST)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return str(source)


def needs_update(source, state):
    source = validate_jpeg(source)
    return (
        state["image"] != str(source)
        or not DEST.is_file()
        or source.stat().st_mtime_ns > DEST.stat().st_mtime_ns
    )


COLOR_KEYS = (
    "mPrimary", "mOnPrimary", "mSecondary", "mOnSecondary", "mTertiary", "mOnTertiary",
    "mError", "mOnError", "mSurface", "mOnSurface", "mSurfaceVariant",
    "mOnSurfaceVariant", "mOutline", "mShadow", "mHover", "mOnHover",
)


def write_colors(raw):
    colors = json.loads(raw)
    if not isinstance(colors, dict) or set(colors) != set(COLOR_KEYS):
        raise RuntimeError("Incomplete Noctalia color palette")
    if any(not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value) for value in colors.values()):
        raise RuntimeError("Invalid Noctalia color value")
    require_installed()
    if not DATA_CONFIG.is_file():
        raise RuntimeError("SDDM theme configuration is missing; rerun scripts/install.sh")
    original = DATA_CONFIG.read_text()
    updated = original
    for key in COLOR_KEYS:
        updated, count = re.subn(r"(?m)^" + key + r"=.*$", key + "=" + colors[key], updated, count=1)
        if count != 1:
            raise RuntimeError("SDDM theme is missing color " + key)
    if updated == original:
        return
    fd, name = tempfile.mkstemp(prefix=".theme-", suffix=".conf", dir=DATA_CONFIG.parent)
    try:
        with os.fdopen(fd, "w") as target:
            target.write(updated)
            target.flush()
            os.fsync(target.fileno())
        os.chmod(name, 0o644)
        os.replace(name, DATA_CONFIG)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main():
    if len(sys.argv) < 2:
        raise RuntimeError("Usage: wallpaper.py status|seed-source|check-jpeg|sync-source|manual|mode|connector")
    command = sys.argv[1]
    if command == "status":
        state = load_state()
        state["installed"] = DEST.is_file() and os.access(DEST.parent, os.W_OK)
        print(json.dumps(state))
        return
    if command == "seed-source":
        state = load_state()
        if state["mode"] == "manual":
            print(state["image"])
        return
    if command == "check-jpeg" and len(sys.argv) == 3:
        validate_jpeg(sys.argv[2])
        return

    state_dir()
    with (STATE_DIR / "lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load_state()
        if command == "colors" and len(sys.argv) == 3:
            if state["colors_sync"]:
                write_colors(sys.argv[2])
        elif command == "color-mode" and len(sys.argv) == 3 and sys.argv[2] == "off":
            state["colors_sync"] = False
            save_state(state)
        elif command == "color-mode" and len(sys.argv) == 4 and sys.argv[2] == "on":
            write_colors(sys.argv[3])
            state["colors_sync"] = True
            save_state(state)
        elif command == "sync-source" and len(sys.argv) == 4:
            if state["mode"] == "manual":
                return
            connector, source = sys.argv[2:4]
            if not connector or not source:
                raise RuntimeError("Missing output or wallpaper path")
            if not state["connector"]:
                state["connector"] = connector
                save_state(state)
            if state["connector"] != connector:
                return
            if needs_update(source, state):
                state["image"] = copy_image(source)
                save_state(state)
        elif command == "manual" and len(sys.argv) == 3:
            state["image"] = copy_image(sys.argv[2])
            state["mode"] = "manual"
            save_state(state)
        elif command == "mode" and len(sys.argv) == 5 and sys.argv[2] == "sync":
            connector, source = sys.argv[3:5]
            if not connector or not source:
                raise RuntimeError("Missing output or wallpaper path")
            state["connector"] = connector
            state["image"] = copy_image(source)
            state["mode"] = "sync"
            save_state(state)
        elif command == "connector" and len(sys.argv) == 4:
            connector, source = sys.argv[2:4]
            if not connector or not source:
                raise RuntimeError("Missing output or wallpaper path")
            if state["mode"] == "sync":
                state["image"] = copy_image(source)
            state["connector"] = connector
            save_state(state)
        else:
            raise RuntimeError("Invalid command or arguments")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

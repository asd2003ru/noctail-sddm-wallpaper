#!/usr/bin/env python3
"""Unprivileged wallpaper state and image updater for the SDDM plugin."""

import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

DEST = Path("/var/lib/noctail-sddm-wallpaper/background.png")
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


def copy_image(source):
    require_installed()
    source = Path(source).expanduser().resolve(strict=True)
    if not source.is_file():
        raise RuntimeError("Selected path is not a file")
    fd, name = tempfile.mkstemp(prefix=".background-", suffix=".png", dir=DEST.parent)
    os.close(fd)
    try:
        process = subprocess.run(
            ["magick", str(source), "-auto-orient", "-strip", "PNG:" + name],
            capture_output=True, text=True, timeout=50, check=False,
        )
        if process.returncode:
            raise RuntimeError(process.stderr.strip() or "ImageMagick could not decode the image")
        os.chmod(name, 0o644)
        os.replace(name, DEST)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return str(source)


def needs_update(source, state):
    source = Path(source).expanduser().resolve(strict=True)
    return (
        state["image"] != str(source)
        or not DEST.is_file()
        or source.stat().st_mtime_ns > DEST.stat().st_mtime_ns
    )


def main():
    if len(sys.argv) < 2:
        raise RuntimeError("Usage: wallpaper.py status|sync|manual|mode|connector")
    command = sys.argv[1]
    if command == "status":
        state = load_state()
        state["installed"] = DEST.is_file() and os.access(DEST.parent, os.W_OK)
        print(json.dumps(state))
        return

    state_dir()
    with (STATE_DIR / "lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load_state()
        if command == "sync-source" and len(sys.argv) == 4:
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
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

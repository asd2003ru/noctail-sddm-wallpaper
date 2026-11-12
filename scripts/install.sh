#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
plugin_dir="$data_home/noctalia/plugins/noctail-sddm-wallpaper"

if [ "$(id -u)" -eq 0 ]; then
    echo 'Run scripts/install.sh as your regular user.' >&2
    exit 1
fi

for dependency in git python3 magick zenity sudo noctalia sddm-greeter-qt6; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        echo "Missing requirement: $dependency" >&2
        exit 1
    fi
done

if [ ! -f /usr/share/sddm/themes/sddm/theme.conf ] ||
   [ ! -f /usr/share/sddm/themes/sddm/Assets/background.png ]; then
    echo 'Missing requirement: Noctalia SDDM theme at /usr/share/sddm/themes/sddm' >&2
    exit 1
fi

if ! noctalia msg status >/dev/null 2>&1; then
    echo 'Noctalia must be running in your Niri session during installation.' >&2
    exit 1
fi

noctalia plugins lint "$repo_dir/plugin"

sudo python3 "$repo_dir/scripts/system-setup.py" install "$(id -un)"
mkdir -p "$plugin_dir"
install -m 644 "$repo_dir/plugin/plugin.toml" "$repo_dir/plugin/panel.luau" \
    "$repo_dir/plugin/service.luau" "$repo_dir/plugin/launcher.luau" "$plugin_dir/"
install -m 755 "$repo_dir/plugin/wallpaper.py" "$plugin_dir/wallpaper.py"

noctalia msg config-reload
noctalia msg plugins enable noctail/sddm-wallpaper
noctalia msg plugin noctail/sddm-wallpaper:sync all sync

echo "Installed SDDM Wallpaper. Open Noctalia Launcher and enter /sddm."

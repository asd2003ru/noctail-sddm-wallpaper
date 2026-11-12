#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
plugin_dir="$data_home/noctalia/plugins/noctail-sddm-wallpaper"
config_home=${NOCTALIA_CONFIG_HOME:-${XDG_CONFIG_HOME:-"$HOME/.config"}}
hook_file="$config_home/noctalia/sddm-wallpaper.toml"
hook_command='wallpaper_changed = "noctalia msg plugin noctail/sddm-wallpaper:sync all sync"'

if [ "$(id -u)" -eq 0 ]; then
    echo 'Run scripts/install.sh as your regular user.' >&2
    exit 1
fi

for dependency in git python3 zenity sudo noctalia sddm-greeter-qt6; do
    if ! command -v "$dependency" >/dev/null 2>&1; then
        echo "Missing requirement: $dependency" >&2
        exit 1
    fi
done

if [ ! -f /usr/share/sddm/themes/sddm/theme.conf ]; then
    echo 'Missing Noctalia SDDM theme at /usr/share/sddm/themes/sddm; see README.md.' >&2
    exit 1
fi

if ! noctalia msg status >/dev/null 2>&1; then
    echo 'Noctalia must be running in your Niri session during installation.' >&2
    exit 1
fi

noctalia plugins lint "$repo_dir/plugin"

if [ -f "$hook_file" ] && ! grep -Fqx "$hook_command" "$hook_file"; then
    echo "Existing $hook_file does not contain the expected wallpaper hook; merge it manually." >&2
    exit 1
fi

seed_source=$(python3 "$repo_dir/plugin/wallpaper.py" seed-source)
if [ -z "$seed_source" ]; then
    seed_source=$(noctalia msg wallpaper-get)
fi
python3 "$repo_dir/plugin/wallpaper.py" check-jpeg "$seed_source"

sudo python3 "$repo_dir/scripts/system-setup.py" install "$(id -un)" "$seed_source"
mkdir -p "$plugin_dir"
install -m 644 "$repo_dir/plugin/plugin.toml" "$repo_dir/plugin/panel.luau" \
    "$repo_dir/plugin/service.luau" "$repo_dir/plugin/launcher.luau" "$plugin_dir/"
install -m 755 "$repo_dir/plugin/wallpaper.py" "$plugin_dir/wallpaper.py"

if [ ! -f "$hook_file" ]; then
    mkdir -p "$(dirname -- "$hook_file")"
    printf '[hooks]\n%s\n' "$hook_command" > "$hook_file"
fi

noctalia msg config-reload
if ! noctalia msg plugins enable noctail/sddm-wallpaper; then
    echo 'Plugin enable reported an error; checking whether the existing plugin is active.' >&2
fi
noctalia msg plugin noctail/sddm-wallpaper:sync all sync

echo "Installed SDDM Wallpaper. Open Noctalia Launcher and enter /sddm."

# Repository Guidelines

## Purpose and structure

This repository provides the `noctail/sddm-wallpaper` plugin for Noctalia v5. It synchronizes one selected output's wallpaper with the bundled Noctalia SDDM theme, or keeps a separate manually selected image.

- `plugin/plugin.toml` declares the Noctalia panel, background service, and launcher provider. Keep the plugin ID and entry IDs consistent with IPC commands and the installer.
- `plugin/launcher.luau` exposes the panel through global launcher search and the `/sddm` prefix.
- `plugin/panel.luau` implements the user interface; `plugin/service.luau` handles wallpaper and palette events; `plugin/wallpaper.py` stores settings, copies JPEG images without changing their resolution, and writes validated theme colors.
- `theme/` contains the vendored Noctalia SDDM theme, including its source and license notices. Keep its assets relative and do not replace a different installed theme at the same path.
- `scripts/install.sh` checks requirements, performs privileged SDDM setup, installs and enables the plugin, then triggers initial sync. `scripts/system-setup.py` installs the bundled theme, selects it in SDDM, and restores prior configuration on uninstall.
- `tests/test_wallpaper.py` exercises wallpaper replacement, mode persistence, and theme configuration restore. The project has no bundled wallpapers or build step.

## Development and checks

Run these commands from the repository root:

```sh
noctalia plugins lint plugin
python3 -m unittest discover -s tests
sh -n scripts/install.sh
```

Requirements and installation commands are in `README.md`. Development targets Noctalia v5.4.1 with plugin API 43 and SDDM 0.21. Preview the installed theme with `sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/sddm`; the Qt 5 greeter cannot load this theme's Qt 6 imports. Inspect the login screen at a common desktop resolution for wallpaper and control legibility. Do not require a system-wide installation to run unit tests or lint the plugin.

## Implementation conventions

Use four-space indentation in Luau and Python, and keep subprocess arguments as arrays rather than shell-assembled strings when paths or user input are involved. Keep image references relative to the plugin or use the configured SDDM data path; do not commit machine-specific home paths or wallpaper assets. The panel and service must agree on the helper's commands and persistent state format.

The default mode follows Noctalia's wallpaper on the selected output. The service and panel obtain the current source through `noctalia.wallpaperPath(connector)` and pass that path to the Python helper; the helper must not query Noctalia CLI for it. The service reconciles once at startup, on output changes, and when Noctalia's `wallpaper_changed` hook invokes its IPC handler; it does not poll. Color sync is independent of wallpaper mode, uses `noctalia.getColor` roles, and responds to `colors_changed` without polling; disabling it keeps the last colors. Accept only JPEG (`.jpg` and `.jpeg`), notify for PNG, and preserve the image bytes and resolution. Manual selection persists until the user explicitly returns to sync mode. Preserve the last valid SDDM image if source validation or copying fails. Keep image and theme configuration writes atomic and readable by the SDDM greeter. Avoid changing other settings in the installed theme.

## Installation and review safety

Keep privileged work limited to `scripts/system-setup.py`. Back up `theme.conf` and any changed SDDM selection before changing them, and keep uninstall able to restore them. The installer manages its dedicated Noctalia wallpaper hook file without overwriting different content. Installation must remain repeatable and run from the repository root.

Use short, imperative commit subjects. Pull requests should describe the user-visible change, list lint/test and preview steps, and include a screenshot when the login screen appearance changes.

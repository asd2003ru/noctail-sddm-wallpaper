# Noctail SDDM Wallpaper

## Requirements

- Niri with Noctalia v5.4.1 running (plugin API 43 or newer).
- SDDM 0.21 with Qt 6. The required Noctalia SDDM theme is included in this repository and installed by the script; standard SDDM themes are not supported. On Arch Linux, install `qt6-declarative` and `qt6-5compat`.
- Python 3.11+, `zenity`, `sudo`, and Git.
- JPEG wallpapers (`.jpg` or `.jpeg`). PNG is not supported; the plugin shows a notification if one is selected.

## Installation

On Arch Linux, install SDDM, the Qt 6 modules, and `zenity` (the wallpaper file chooser):

```sh
sudo pacman -S --needed sddm qt6-declarative qt6-5compat zenity
```

In a Niri session with Noctalia running, clone the repository and run the installer:

```sh
git clone https://github.com/asd2003ru/noctail-sddm-wallpaper.git
cd noctail-sddm-wallpaper
./scripts/install.sh
```

The installer prompts for `sudo`, installs the bundled theme to `/usr/share/sddm/themes/sddm`, selects it in SDDM, installs and enables the plugin, and starts the first sync. If another theme already occupies that directory, the installer stops without replacing it. After installation, open Noctalia Launcher and enter `/sddm` to choose a monitor or a separate image. Theme colors sync with Noctalia at startup and when the palette changes; the plugin's `Color sync` button controls this independently of wallpaper sync.

## Русский

### Требования

- Niri с запущенной Noctalia v5.4.1 (plugin API 43 или новее).
- SDDM 0.21 с Qt 6. Нужная тема Noctalia SDDM включена в репозиторий и устанавливается скриптом; стандартные темы SDDM не поддерживаются. На Arch Linux нужны `qt6-declarative` и `qt6-5compat`.
- Python 3.11+, `zenity`, `sudo` и Git.
- Обои в формате JPEG (`.jpg` или `.jpeg`). PNG не поддерживается: плагин покажет уведомление при выборе такого файла.

### Установка

На Arch Linux установите SDDM, модули Qt 6 и `zenity` (диалог выбора файла обоев):

```sh
sudo pacman -S --needed sddm qt6-declarative qt6-5compat zenity
```

В сессии Niri с запущенной Noctalia установите плагин и тему одной командой:

```sh
git clone https://github.com/asd2003ru/noctail-sddm-wallpaper.git
cd noctail-sddm-wallpaper
./scripts/install.sh
```

Установщик запросит `sudo`, установит включённую в проект тему в `/usr/share/sddm/themes/sddm`, выберет её в SDDM, установит и включит плагин, затем запустит первую синхронизацию. Если каталог темы уже занят другой темой, установщик остановится без её замены. После установки откройте Noctalia Launcher и введите `/sddm` для выбора монитора или отдельного изображения. Цвета темы синхронизируются с Noctalia при запуске и смене палитры; кнопка `Color sync` в плагине отключает или включает это отдельно от обоев.

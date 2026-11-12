# Noctail SDDM Wallpaper

## Требования

- Niri с запущенной Noctalia v5 (plugin API 25 или новее).
- SDDM 0.21 с Qt 6. Нужная тема Noctalia SDDM включена в репозиторий и устанавливается скриптом; стандартные темы SDDM не поддерживаются. На Arch Linux нужны `qt6-declarative` и `qt6-5compat`.
- Python 3.11+, `zenity`, `sudo` и Git. Для команды клонирования ниже нужен доступ к GitHub по SSH.
- Обои в формате JPEG (`.jpg` или `.jpeg`). PNG не поддерживается: плагин покажет уведомление при выборе такого файла.

## Установка

На Arch Linux установите SDDM и модули Qt 6:

```sh
sudo pacman -S --needed sddm qt6-declarative qt6-5compat
```

В сессии Niri с запущенной Noctalia установите плагин и тему одной командой:

```sh
git clone git@github.com:asd2003ru/noctail-sddm-wallpaper.git
cd noctail-sddm-wallpaper
./scripts/install.sh
```

Установщик запросит `sudo`, установит включённую в проект тему в `/usr/share/sddm/themes/sddm`, выберет её в SDDM, установит и включит плагин, затем запустит первую синхронизацию. Если каталог темы уже занят другой темой, установщик остановится без её замены. Источник и лицензия включённой темы указаны в `theme/SOURCE.md` и `theme/LICENSE`. После установки откройте Noctalia Launcher и введите `/sddm` для выбора монитора или отдельного изображения.

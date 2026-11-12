# Noctail SDDM Wallpaper

## Требования

- Niri с запущенной Noctalia v5 (plugin API 25 или новее).
- SDDM 0.21 с установленной и выбранной темой `sddm` в `/usr/share/sddm/themes/sddm`. Тема должна использовать Qt 6; на Arch Linux нужны `qt6-declarative` и `qt6-5compat`.
- Python 3.11+, ImageMagick (`magick`), `zenity`, `sudo` и Git. Для команды клонирования ниже нужен доступ к GitHub по SSH.

## Установка

В сессии Niri с запущенной Noctalia выполните:

```sh
git clone git@github.com:asd2003ru/noctail-sddm-wallpaper.git
cd noctail-sddm-wallpaper
./scripts/install.sh
```

Установщик один раз запросит `sudo`, настроит текущую тему SDDM, установит и включит плагин, затем запустит первую синхронизацию. Дальше откройте Noctalia Launcher и введите `/sddm` для выбора монитора или отдельного изображения.

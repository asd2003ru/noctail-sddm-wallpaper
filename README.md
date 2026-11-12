# Noctail SDDM Wallpaper

## Требования

- Niri с запущенной Noctalia v5 (plugin API 25 или новее).
- SDDM 0.21 и сторонняя [тема Noctalia SDDM](https://github.com/mahaveergurjar/sddm/tree/noctalia) из ветки `noctalia`, установленная в `/usr/share/sddm/themes/sddm` и выбранная в SDDM. Плагин не работает со стандартными темами SDDM. Для темы нужны Qt 6, `qt6-declarative` и `qt6-5compat` на Arch Linux.
- Python 3.11+, `zenity`, `sudo` и Git. Для команды клонирования ниже нужен доступ к GitHub по SSH.
- Обои в формате JPEG (`.jpg` или `.jpeg`). PNG не поддерживается: плагин покажет уведомление при выборе такого файла.

## Установка

Сначала установите тему. На Arch Linux:

```sh
sudo pacman -S --needed sddm qt6-declarative qt6-5compat
git clone --branch noctalia --single-branch https://github.com/mahaveergurjar/sddm.git
if [ ! -e /usr/share/sddm/themes/sddm ]; then
    sudo cp -a sddm /usr/share/sddm/themes/
fi
sudoedit /etc/sddm.conf
```

В файле `/etc/sddm.conf` укажите:

```ini
[Theme]
Current=sddm
```

Если каталог `/usr/share/sddm/themes/sddm` уже существует, убедитесь, что это именно тема Noctalia (`Name=Noctalia` в `metadata.desktop`); команда выше не заменяет существующую тему. Тему можно проверить без выхода из сеанса:

```sh
sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/sddm
```

Затем в сессии Niri с запущенной Noctalia установите плагин:

```sh
git clone git@github.com:asd2003ru/noctail-sddm-wallpaper.git
cd noctail-sddm-wallpaper
./scripts/install.sh
```

Установщик один раз запросит `sudo`, настроит текущую тему SDDM, установит и включит плагин, затем запустит первую синхронизацию. Дальше откройте Noctalia Launcher и введите `/sddm` для выбора монитора или отдельного изображения.

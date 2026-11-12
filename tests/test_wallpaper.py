import importlib.util
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("wallpaper", Path(__file__).parents[1] / "plugin/wallpaper.py")
wallpaper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wallpaper)
SETUP_SPEC = importlib.util.spec_from_file_location("system_setup", Path(__file__).parents[1] / "scripts/system-setup.py")
system_setup = importlib.util.module_from_spec(SETUP_SPEC)
SETUP_SPEC.loader.exec_module(system_setup)


class WallpaperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.dest = root / "sddm/background.jpg"
        self.dest.parent.mkdir()
        self.dest.write_bytes(b"previous")
        self.state_dir = root / "state"
        self.patches = [
            patch.object(wallpaper, "DEST", self.dest),
            patch.object(wallpaper, "STATE_DIR", self.state_dir),
            patch.object(wallpaper, "STATE_FILE", self.state_dir / "state.json"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.source = root / "wallpaper.jpg"
        self.source.write_bytes(b"\xff\xd8\xffexample-jpeg-bytes\xff\xd9")

    def invoke(self, *args):
        with patch.object(wallpaper.sys, "argv", ["wallpaper.py", *args]):
            wallpaper.main()

    def test_manual_survives_sync_until_mode_changes(self):
        self.invoke("manual", str(self.source))
        manual = self.dest.read_bytes()
        self.assertEqual(manual, self.source.read_bytes())
        self.assertEqual(wallpaper.load_state()["mode"], "manual")
        with patch.object(wallpaper.sys, "argv", ["wallpaper.py", "seed-source"]), \
                patch("builtins.print") as output:
            wallpaper.main()
            output.assert_called_once_with(str(self.source.resolve()))
        self.invoke("sync-source", "DP-1", str(self.source))
        self.assertEqual(self.dest.read_bytes(), manual)
        self.invoke("mode", "sync", "DP-1", str(self.source))
        self.assertEqual(wallpaper.load_state()["mode"], "sync")
        self.assertEqual(wallpaper.load_state()["connector"], "DP-1")

    def test_png_is_rejected_without_changing_background(self):
        bad = Path(self.tmp.name) / "bad.png"
        bad.write_bytes(b"\x89PNG\r\n\x1a\n")
        with self.assertRaisesRegex(RuntimeError, "PNG is not supported"):
            self.invoke("manual", str(bad))
        self.assertEqual(self.dest.read_bytes(), b"previous")
        self.assertEqual(wallpaper.load_state()["mode"], "sync")

    def test_invalid_jpeg_is_rejected(self):
        bad = Path(self.tmp.name) / "bad.jpg"
        bad.write_text("not a jpeg")
        with self.assertRaisesRegex(RuntimeError, "not a valid JPEG"):
            self.invoke("manual", str(bad))
        self.assertEqual(self.dest.read_bytes(), b"previous")

    def test_sync_retries_changes_without_recopying_unchanged_image(self):
        with patch.object(wallpaper, "copy_image", wraps=wallpaper.copy_image) as convert:
            self.invoke("sync-source", "DP-1", str(self.source))
            self.invoke("sync-source", "DP-1", str(self.source))
            self.assertEqual(convert.call_count, 1)
            future = time.time_ns() + 2_000_000_000
            os.utime(self.source, ns=(future, future))
            self.invoke("sync-source", "DP-1", str(self.source))
            self.assertEqual(convert.call_count, 2)

    def test_sync_ignores_other_monitor(self):
        self.invoke("sync-source", "DP-1", str(self.source))
        first = self.dest.read_bytes()
        second = Path(self.tmp.name) / "other.jpg"
        second.write_bytes(b"\xff\xd8\xffother-jpeg-bytes\xff\xd9")
        self.invoke("sync-source", "HDMI-A-1", str(second))
        self.assertEqual(self.dest.read_bytes(), first)
        self.assertEqual(wallpaper.load_state()["connector"], "DP-1")


class SystemSetupTests(unittest.TestCase):
    def test_bundled_theme_installs_without_existing_theme(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            theme = root / "themes/sddm"
            theme.parent.mkdir()
            source = root / "wallpaper.jpg"
            source.write_bytes(b"\xff\xd8\xffseed-jpeg-bytes\xff\xd9")
            data = root / "data"
            sddm_config = root / "sddm.conf"
            import pwd
            user = pwd.getpwuid(os.getuid()).pw_name
            with patch.object(system_setup, "THEME", theme), \
                    patch.object(system_setup, "CONFIG", theme / "theme.conf"), \
                    patch.object(system_setup, "METADATA", theme / "metadata.desktop"), \
                    patch.object(system_setup, "BACKUP", theme / "theme.conf.noctail-backup"), \
                    patch.object(system_setup, "SDDM_CONFIG", sddm_config), \
                    patch.object(system_setup, "SDDM_CONFIG_BACKUP", root / "sddm.conf.noctail-backup"), \
                    patch.object(system_setup, "SDDM_CONFIG_ABSENT", root / "sddm.conf.noctail-absent"), \
                    patch.object(system_setup, "DATA_DIR", data), \
                    patch.object(system_setup, "DEST", data / "background.jpg"):
                system_setup.install(user, str(source), str(Path(__file__).parents[1] / "theme"))
                self.assertTrue((theme / "Main.qml").is_file())
                self.assertIn("Current=sddm", sddm_config.read_text())
                self.assertEqual((data / "background.jpg").read_bytes(), source.read_bytes())
                system_setup.uninstall()
                self.assertFalse(sddm_config.exists())

    def test_install_and_uninstall_restore_theme(self):
        with tempfile.TemporaryDirectory() as tmp:
            theme = Path(tmp) / "theme"
            assets = theme / "Assets"
            assets.mkdir(parents=True)
            (assets / "background.png").write_bytes(b"original image")
            source = Path(tmp) / "wallpaper.jpg"
            source.write_bytes(b"\xff\xd8\xffseed-jpeg-bytes\xff\xd9")
            config = theme / "theme.conf"
            metadata = theme / "metadata.desktop"
            metadata.write_text("[SddmGreeterTheme]\nName=Noctalia\nQtVersion=6\n")
            (theme / "Main.qml").write_text("import QtQuick 2.15\n")
            original = "[General]\nbackground=Assets/background.png\nblurRadius=0\n"
            config.write_text(original)
            data = Path(tmp) / "data"
            sddm_config = Path(tmp) / "sddm.conf"
            sddm_config.write_text("[Theme]\nCurrent=elarun\n")
            import pwd
            user = pwd.getpwuid(__import__("os").getuid()).pw_name
            with patch.object(system_setup, "THEME", theme), \
                    patch.object(system_setup, "CONFIG", config), \
                    patch.object(system_setup, "METADATA", metadata), \
                    patch.object(system_setup, "BACKUP", theme / "theme.conf.noctail-backup"), \
                    patch.object(system_setup, "SDDM_CONFIG", sddm_config), \
                    patch.object(system_setup, "SDDM_CONFIG_BACKUP", Path(tmp) / "sddm.conf.noctail-backup"), \
                    patch.object(system_setup, "SDDM_CONFIG_ABSENT", Path(tmp) / "sddm.conf.noctail-absent"), \
                    patch.object(system_setup, "DATA_DIR", data), \
                    patch.object(system_setup, "DEST", data / "background.jpg"):
                system_setup.install(user, str(source), str(theme))
                self.assertIn("background=file://" + str(data / "background.jpg"), config.read_text())
                self.assertEqual((data / "background.jpg").read_bytes(), source.read_bytes())
                self.assertIn("Current=sddm", sddm_config.read_text())
                system_setup.install(user, str(source), str(theme))
                system_setup.uninstall()
                self.assertEqual(config.read_text(), original)
                self.assertEqual(sddm_config.read_text(), "[Theme]\nCurrent=elarun\n")


if __name__ == "__main__":
    unittest.main()

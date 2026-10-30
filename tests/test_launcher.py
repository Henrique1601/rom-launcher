"""Testes unitários para o módulo de Scanner e Registry do Launcher."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rom_cli.launcher.scanner import LibraryScanner
from rom_cli.launcher.registry import EmulatorRegistry


class TestLauncher(unittest.TestCase):
    def test_scanner_detects_games(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            snes_dir = base / "SNES"
            snes_dir.mkdir()

            # Cria arquivos simulando ROMs
            (snes_dir / "Super Mario World.sfc").write_bytes(b"DATA" * 50)
            (snes_dir / "Chrono Trigger.zip").write_bytes(b"ZIP_DATA" * 50)
            (snes_dir / "Incomplete.part").write_bytes(b"PARTIAL")

            scanner = LibraryScanner(base)
            library = scanner.scan_all()

            self.assertIn("snes", library)
            games = library["snes"]
            titles = [g.title for g in games]
            self.assertIn("Super Mario World", titles)
            self.assertIn("Chrono Trigger", titles)
            self.assertNotIn("Incomplete", titles)

    def test_registry_custom_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "emulators.json"
            registry = EmulatorRegistry(config_file=config_file)

            fake_emu = Path(tmp_dir) / "fake_pcsx2.exe"
            fake_emu.write_text("dummy")

            registry.set_emulator_path("ps2", str(fake_emu))
            found = registry.find_emulator("ps2")

            self.assertIsNotNone(found)
            self.assertEqual(found, fake_emu)


if __name__ == "__main__":
    unittest.main()

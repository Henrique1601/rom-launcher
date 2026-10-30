"""Testes unitários para a Roleta Gamer."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rom_cli.core.roulette import pick_random_game


class TestRoulette(unittest.TestCase):
    def test_pick_random_game_empty(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            picked = pick_random_game(outdir=Path(tmp_dir))
            self.assertIsNone(picked)

    def test_pick_random_game_with_roms(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            snes_dir = base / "SNES"
            snes_dir.mkdir()
            (snes_dir / "Super Metroid.sfc").write_bytes(b"DATA" * 50)
            (snes_dir / "Chrono Trigger.sfc").write_bytes(b"DATA" * 50)

            picked = pick_random_game(platform_key="snes", outdir=base)
            self.assertIsNotNone(picked)
            self.assertIn(picked.title, ["Super Metroid", "Chrono Trigger"])


if __name__ == "__main__":
    unittest.main()

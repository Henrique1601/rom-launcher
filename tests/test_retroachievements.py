"""Testes unitários para o cliente RetroAchievements."""

import tempfile
import unittest
from pathlib import Path

from rom_cli.core.retroachievements import RetroAchievementsClient, RA_CONSOLE_IDS


class TestRetroAchievements(unittest.TestCase):
    def test_console_id_mapping(self):
        self.assertEqual(RA_CONSOLE_IDS.get("snes"), 3)
        self.assertEqual(RA_CONSOLE_IDS.get("ps1"), 12)
        self.assertEqual(RA_CONSOLE_IDS.get("ps2"), 21)
        self.assertEqual(RA_CONSOLE_IDS.get("genesis"), 1)

    def test_cache_storage(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            client = RetroAchievementsClient(cache_dir=Path(tmp_dir))
            # Teste de retorno seguro para console desconhecido
            res = client.get_game_info("Test Game", "unknown_console_xyz")
            self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()

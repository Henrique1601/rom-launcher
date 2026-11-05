"""Testes unitários para o Hub de Traduções PT-BR."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rom_cli.core.translations import (
    TRANSLATIONS_CATALOG,
    _normalize_title,
    apply_community_translation,
    find_translation_for_game,
    is_already_translated,
)


class TestTranslations(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normalize_title(self):
        self.assertEqual(_normalize_title("Super Mario World (USA) [!]"), "super mario world")
        self.assertEqual(_normalize_title("Chrono Trigger (E) [v1.1]"), "chrono trigger")
        self.assertEqual(_normalize_title("Resident Evil 2 (Disc 1)"), "resident evil 2")

    def test_is_already_translated(self):
        self.assertTrue(is_already_translated("Super Mario World [PT-BR]"))
        self.assertTrue(is_already_translated("Chrono Trigger (Traduzido)"))
        self.assertTrue(is_already_translated("Pokemon FireRed (BR)"))
        self.assertFalse(is_already_translated("Super Mario World (USA)"))

    def test_find_translation_for_game(self):
        # SNES
        item_smw = find_translation_for_game("Super Mario World (USA)", "snes")
        self.assertIsNotNone(item_smw)
        self.assertEqual(item_smw.id, "snes_smw_ptbr")
        self.assertEqual(item_smw.platform, "snes")

        item_ct = find_translation_for_game("Chrono Trigger [!]", "snes")
        self.assertIsNotNone(item_ct)
        self.assertEqual(item_ct.id, "snes_chrono_trigger_ptbr")

        # PS1
        item_re2 = find_translation_for_game("Resident Evil 2 (DualShock Edition)", "ps1")
        self.assertIsNotNone(item_re2)
        self.assertEqual(item_re2.id, "ps1_resident_evil_2_ptbr")

        # GBA
        item_pkmn = find_translation_for_game("Pokemon FireRed Version (USA)", "gba")
        self.assertIsNotNone(item_pkmn)
        self.assertEqual(item_pkmn.id, "gba_pokemon_fire_red_ptbr")

        # Se já traduzido, não sugere tradução redundante
        self.assertIsNone(find_translation_for_game("Super Mario World [PT-BR]", "snes"))

    @patch("rom_cli.core.translations.download_patch")
    def test_apply_community_translation(self, mock_download):
        # Cria uma ROM fake
        fake_rom = self.base_path / "Super Mario World (USA).sfc"
        fake_rom.write_bytes(b"\x00" * 512)

        item = find_translation_for_game("Super Mario World", "snes")
        self.assertIsNotNone(item)

        # Mock para criar patch IPS fake
        def fake_patch(item_entry, dest_path, on_progress=None):
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(b"PATCH\x00\x00\x00\x00\x01\x00EOF")
            return dest_path

        mock_download.side_effect = fake_patch

        with patch("rom_cli.core.translations.TRANSLATIONS_CACHE_DIR", self.base_path / "cache_trans"):
            success, msg, out_path = apply_community_translation(fake_rom, item)
            self.assertTrue(success)
            self.assertIsNotNone(out_path)
            self.assertTrue(out_path.is_file())
            self.assertIn("[PT-BR]", out_path.name)


if __name__ == "__main__":
    unittest.main()

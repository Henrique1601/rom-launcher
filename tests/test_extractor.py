"""Testes unitários para o módulo de extração automática."""

import tempfile
import unittest
import zipfile
from pathlib import Path

from rom_cli.core.extractor import extract_archive


class TestExtractor(unittest.TestCase):
    def test_extract_zip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            zip_file = tmp_path / "test_rom.zip"
            dest_dir = tmp_path / "extracted"

            # Cria um arquivo zip de teste
            with zipfile.ZipFile(zip_file, "w") as z:
                z.writestr("game.nes", b"NES_ROM_DATA_12345")

            result = extract_archive(zip_file, target_dir=dest_dir)
            self.assertIsNotNone(result)
            extracted_file = dest_dir / "game.nes"
            self.assertTrue(extracted_file.exists())
            self.assertEqual(extracted_file.read_bytes(), b"NES_ROM_DATA_12345")


if __name__ == "__main__":
    unittest.main()

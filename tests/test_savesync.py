"""Testes unitários para o gerenciador de Save-Sync e backups de saves."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import rom_cli.core.savesync as savesync


class TestSaveSync(unittest.TestCase):
    def test_emulator_paths_mapping(self):
        mapping = savesync.get_emulator_save_paths()
        self.assertIn("ps2", mapping)
        self.assertIn("ps1", mapping)
        self.assertIn("switch", mapping)
        self.assertIn("snes", mapping)

    def test_backup_and_restore_cycle(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Simula uma pasta de saves de PS2
            fake_memcard_dir = tmp_path / "PCSX2" / "memcards"
            fake_memcard_dir.mkdir(parents=True)
            memcard_file = fake_memcard_dir / "Mcd001.ps2"
            memcard_file.write_bytes(b"MEMORY_CARD_DATA_12345")

            # Redireciona caminhos e diretório de backup
            orig_backup_dir = savesync.SAVES_BACKUP_DIR
            savesync.SAVES_BACKUP_DIR = tmp_path / "backups"
            savesync.SAVES_BACKUP_DIR.mkdir()

            orig_func = savesync.get_emulator_save_paths
            try:
                # Monkeypatch temporário para a plataforma ps2
                def mock_save_paths():
                    return {"ps2": [fake_memcard_dir]}

                savesync.get_emulator_save_paths = mock_save_paths

                # 1. Cria backup
                zip_path = savesync.create_save_backup("ps2", game_title="God of War")
                self.assertIsNotNone(zip_path)
                self.assertTrue(zip_path.exists())

                # 2. Lista backups
                backups = savesync.list_save_backups("ps2")
                self.assertEqual(len(backups), 1)
                self.assertEqual(backups[0]["platform"], "ps2")

                # 3. Simula perda/corrupção de save
                memcard_file.write_bytes(b"CORRUPTED")

                # 4. Restaura backup
                success = savesync.restore_save_backup(zip_path)
                self.assertTrue(success)
                self.assertEqual(memcard_file.read_bytes(), b"MEMORY_CARD_DATA_12345")
            finally:
                savesync.SAVES_BACKUP_DIR = orig_backup_dir
                savesync.get_emulator_save_paths = orig_func

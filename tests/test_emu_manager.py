"""Testes unitários para o gerenciador e instalador automático de emuladores."""

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rom_cli.core.emu_manager import (
    EMULATOR_CATALOG,
    find_executable,
    get_emulator_info,
    install_emulator,
    resolve_release_url,
)
from rom_cli.launcher.registry import EmulatorRegistry


class TestEmuManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_catalog_entries(self):
        """Verifica se os principais emuladores estão cadastrados no catálogo."""
        self.assertIn("duckstation", EMULATOR_CATALOG)
        self.assertIn("pcsx2", EMULATOR_CATALOG)
        self.assertIn("dolphin", EMULATOR_CATALOG)
        self.assertIn("mgba", EMULATOR_CATALOG)
        self.assertIn("snes9x", EMULATOR_CATALOG)

        # Busca por id
        ds = get_emulator_info("duckstation")
        self.assertIsNotNone(ds)
        self.assertEqual(ds.name, "DuckStation")
        self.assertIn("ps1", ds.platform_keys)

        # Busca por platform_key
        ps2_emu = get_emulator_info("ps2")
        self.assertIsNotNone(ps2_emu)
        self.assertEqual(ps2_emu.id, "pcsx2")

    def test_resolve_release_url_fallback(self):
        """Testa o fallback para a URL direta caso o GitHub não responda."""
        entry = EMULATOR_CATALOG["snes9x"]
        with patch("urllib.request.build_opener", side_effect=Exception("Network down")):
            url, filename = resolve_release_url(entry)
            self.assertEqual(url, entry.fallback_url)
            self.assertTrue(filename.endswith(".zip"))

    def test_find_executable(self):
        """Testa a localização de executáveis em subpastas extraídas."""
        subfolder = self.base_path / "DuckStation"
        subfolder.mkdir(parents=True)
        exe_file = subfolder / "duckstation-qt-x64-ReleaseLTCG.exe"
        exe_file.write_text("dummy exe")

        # Busca com nome exato esperado
        found = find_executable(self.base_path, "duckstation-qt-x64-ReleaseLTCG.exe", "duckstation")
        self.assertIsNotNone(found)
        self.assertEqual(found, exe_file)

        # Busca com prefixo do binário
        found_prefix = find_executable(self.base_path, "outro_nome.exe", "duckstation")
        self.assertIsNotNone(found_prefix)
        self.assertEqual(found_prefix, exe_file)

    @patch("rom_cli.core.emu_manager.resolve_release_url", return_value=("https://example.com/snes9x.zip", "snes9x.zip"))
    @patch("rom_cli.core.emu_manager.download_file")
    def test_install_emulator_flow(self, mock_download, mock_resolve):
        """Testa o fluxo completo de instalação com descompactação e registro mockados."""
        entry = EMULATOR_CATALOG["snes9x"]
        install_dir = self.base_path / "emulators" / entry.id
        install_dir.mkdir(parents=True, exist_ok=True)

        # Faz com que o mock_download crie o zip no caminho esperado 'dest'
        def fake_download(url, dest, on_progress=None):
            with zipfile.ZipFile(dest, "w") as z:
                z.writestr("snes9x-x64.exe", "fake snes9x binary")
            return dest

        mock_download.side_effect = fake_download

        config_json = self.base_path / "emulators.json"
        mock_registry = EmulatorRegistry(config_file=config_json)

        progress_calls = []

        def track_progress(cur, total, msg):
            progress_calls.append(msg)

        with patch("rom_cli.core.emu_manager.EMULATORS_INSTALL_DIR", self.base_path / "emulators"):
            success, msg, exe_path = install_emulator("snes", on_progress=track_progress, registry=mock_registry)
            self.assertTrue(success, f"install_emulator failed: {msg}")
            self.assertIsNotNone(exe_path)
            self.assertTrue(Path(exe_path).is_file())
            self.assertEqual(Path(mock_registry.find_emulator("snes")), Path(exe_path))
            self.assertTrue(any("sucesso" in p.lower() for p in progress_calls))


if __name__ == "__main__":
    unittest.main()

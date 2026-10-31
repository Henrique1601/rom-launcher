"""Testes unitários para o assistente de instalação e componentes do Launcher Glass."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rom_cli.gui.main_window import PLATFORM_COLORS, QUICK_PLATFORMS, play_click
from rom_cli.installer.setup_wizard import SetupWizard


class TestInstallerAndGUI(unittest.TestCase):
    def test_gui_tokens_and_colors(self):
        """Verifica se as cores e plataformas rápidas do Launcher Glass estão configuradas."""
        self.assertIn("switch", PLATFORM_COLORS)
        self.assertIn("ps2", PLATFORM_COLORS)
        self.assertIn("xbox", PLATFORM_COLORS)
        self.assertIn("xbox360", PLATFORM_COLORS)

        # Garante que QUICK_PLATFORMS possui chave e label
        pill_keys = [pk for pk, _ in QUICK_PLATFORMS]
        self.assertIn("all", pill_keys)
        self.assertIn("switch", pill_keys)
        self.assertIn("ps2", pill_keys)

        # play_click não deve levantar exceções
        play_click()

    def test_uninstaller_script_creation(self):
        """Testa se o gerador de desinstalador cria o script Uninstall.bat corretamente."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # Cria instância sem invocar o loop principal
            wizard = SetupWizard.__new__(SetupWizard)
            wizard._create_uninstaller(tmp_path)

            uninstall_bat = tmp_path / "Uninstall.bat"
            self.assertTrue(uninstall_bat.exists())
            content = uninstall_bat.read_text(encoding="ascii")
            self.assertIn("EmuCraft", content)
            self.assertIn("rmdir /s /q", content)

    def test_shortcuts_vbs_generation(self):
        """Testa se a rotina de criação de atalhos gera o script VBS esperado."""
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            dummy_exe = tmp_path / "EmuCraft.exe"
            dummy_exe.write_bytes(b"MZ_DUMMY_EXE")

            wizard = SetupWizard.__new__(SetupWizard)
            class MockVar:
                def get(self): return True
            wizard.create_desktop_shortcut_var = MockVar()
            wizard.create_start_menu_var = MockVar()

            with patch("rom_cli.installer.setup_wizard.subprocess.run") as mock_run:
                wizard._create_shortcuts(tmp_path, dummy_exe)
                self.assertTrue(mock_run.called)
                args, kwargs = mock_run.call_args
                self.assertIn("cscript.exe", args[0])
                self.assertEqual(kwargs.get("timeout"), 5)


if __name__ == "__main__":
    unittest.main()

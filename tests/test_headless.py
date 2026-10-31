"""Testes para garantir resiliência em ambientes sem console (PyInstaller --noconsole / pythonw)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class TestHeadlessStreams(unittest.TestCase):
    def test_utils_with_none_stdout(self):
        """Simula ambiente sem console onde sys.stdout/stderr/stdin são None."""
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        orig_stdin = sys.stdin
        try:
            sys.stdout = None
            sys.stderr = None
            sys.stdin = None

            # Re-executa lógica de escrita sob ambiente None
            import rom_cli.core.utils as utils

            # A importação e funções não podem disparar AttributeError
            utils.write("Mensagem de teste em ambiente sem console")
            utils.status("Status de teste")
            utils.clear_status()
            self.assertFalse(utils.TTY)
        finally:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            sys.stdin = orig_stdin

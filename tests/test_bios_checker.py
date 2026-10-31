"""Testes unitários para o auditor de integridade de BIOS."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import rom_cli.core.bios_checker as bios_checker


class TestBiosChecker(unittest.TestCase):
    def test_rules_presence(self):
        rules = bios_checker.get_bios_rules()
        self.assertIn("ps2", rules)
        self.assertIn("ps1", rules)
        self.assertIn("switch", rules)
        self.assertIn("xbox", rules)

    def test_audit_missing_folder(self):
        result = bios_checker.audit_bios("ps2")
        self.assertIn("status", result)
        self.assertIn(result["status"], ["ok", "missing_bios", "missing_folder"])

    def test_audit_detected_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            bios_file = tmp_path / "scph39001.bin"
            bios_file.write_bytes(b"FAKE_PS2_BIOS")

            # Mocka regras para apontar para a pasta temporária
            orig_rules = bios_checker.get_bios_rules

            def mock_rules():
                r = orig_rules()
                r["ps2"]["folders"] = [tmp_path]
                return r

            bios_checker.get_bios_rules = mock_rules
            try:
                result = bios_checker.audit_bios("ps2")
                self.assertEqual(result["status"], "ok")
                self.assertIn("scph39001.bin", result["matched"])
            finally:
                bios_checker.get_bios_rules = orig_rules

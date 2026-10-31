"""Testes unitários para o motor de aplicação de patches (IPS e BPS)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rom_cli.core.patcher import apply_ips_patch, apply_patch, PatchError


class TestPatcher(unittest.TestCase):
    def test_apply_ips_standard_record(self):
        """Testa aplicação de registro padrão em patch IPS."""
        rom_data = b"ABCDEFGHIJ"
        # Patch: 'PATCH' + offset 2 (3 bytes) + size 3 (2 bytes) + 'XYZ' + 'EOF'
        patch_data = b"PATCH" + (2).to_bytes(3, "big") + (3).to_bytes(2, "big") + b"XYZ" + b"EOF"

        patched = apply_ips_patch(rom_data, patch_data)
        self.assertEqual(patched, b"ABXYZFGHIJ")

    def test_apply_ips_rle_record(self):
        """Testa aplicação de registro RLE (tamanho 0) em patch IPS."""
        rom_data = b"1234567890"
        # Patch: 'PATCH' + offset 1 + size 0 + rle_count 4 + val ord('Z') + 'EOF'
        patch_data = (
            b"PATCH"
            + (1).to_bytes(3, "big")
            + (0).to_bytes(2, "big")
            + (4).to_bytes(2, "big")
            + b"Z"
            + b"EOF"
        )

        patched = apply_ips_patch(rom_data, patch_data)
        self.assertEqual(patched, b"1ZZZZ67890")

    def test_apply_ips_invalid_header(self):
        """Testa rejeição de arquivo com cabeçalho inválido."""
        with self.assertRaises(PatchError):
            apply_ips_patch(b"DATA", b"INVALID_HEADER_DATA")

    def test_apply_patch_file_pipeline(self):
        """Testa a função de alto nível apply_patch gravando arquivo de saída."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            rom_file = tmp_path / "SuperMario.sfc"
            patch_file = tmp_path / "Traducao.ips"

            rom_file.write_bytes(b"HELLO_WORLD_ORIGINAL")
            patch_data = b"PATCH" + (0).to_bytes(3, "big") + (5).to_bytes(2, "big") + b"SALVE" + b"EOF"
            patch_file.write_bytes(patch_data)

            out_file = apply_patch(rom_file, patch_file)
            self.assertTrue(out_file.exists())
            self.assertIn("[PT-BR]", out_file.name)
            self.assertTrue(out_file.read_bytes().startswith(b"SALVE_WORLD"))

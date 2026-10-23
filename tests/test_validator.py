"""Testes unitários de validação e integridade de arquivos."""

import os
import tempfile
import unittest
from pathlib import Path
from rom_cli.core.validator import validate_file, fix_magic_extension


class TestValidator(unittest.TestCase):
    def test_validate_empty_or_nonexistent(self):
        self.assertFalse(validate_file("arquivo_inexistente_12345.zip"))
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(b"tiny")
            self.assertFalse(validate_file(path))
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_validate_zip(self):
        fd, path = tempfile.mkstemp(suffix=".zip")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(b"PK\x03\x04" + b"0" * 2000)
            self.assertTrue(validate_file(path))
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_fix_magic_extension(self):
        fd, path = tempfile.mkstemp(suffix=".bin")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(b"PK\x03\x04" + b"0" * 100)
            new_p = fix_magic_extension(path)
            self.assertEqual(Path(new_p).suffix, ".zip")
            self.assertTrue(os.path.exists(new_p))
        finally:
            if 'new_p' in locals() and os.path.exists(new_p):
                os.unlink(new_p)
            elif os.path.exists(path):
                os.unlink(path)


if __name__ == "__main__":
    unittest.main()

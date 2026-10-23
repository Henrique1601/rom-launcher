"""Testes unitários de utilitários e normalização."""

import unittest
from rom_cli.core.utils import norm, pretty_title, human_size, safe_name


class TestUtils(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(norm("Pokémon Emerald (USA, Europe)"), "pokemon emerald usa europe")
        self.assertEqual(norm("Super Mario 64!"), "super mario 64")

    def test_pretty_title(self):
        self.assertEqual(pretty_title("Super_Mario_World_[v1.1].sfc"), "Super Mario World")
        self.assertEqual(pretty_title("download Pokemon - FireRed Version (USA).gba"), "Pokemon - FireRed Version (USA)")

    def test_human_size(self):
        self.assertEqual(human_size(500), "500 B")
        self.assertEqual(human_size(1024 * 1024), "1.0 MB")
        self.assertEqual(human_size(int(1024 * 1024 * 1024 * 2.5)), "2.5 GB")

    def test_safe_name(self):
        cleaned = safe_name('Zelda: Breath / of * Wild?', 'fallback', '.nsp')
        self.assertNotIn(":", cleaned)
        self.assertNotIn("/", cleaned)
        self.assertNotIn("*", cleaned)
        self.assertNotIn("?", cleaned)
        self.assertTrue(cleaned.endswith('.nsp'))


if __name__ == "__main__":
    unittest.main()

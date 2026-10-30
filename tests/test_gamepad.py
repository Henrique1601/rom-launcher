"""Testes unitários para o módulo de Gamepad / XInput."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rom_cli.core.gamepad import GamepadController, DPAD_UP, BUTTON_A


class TestGamepad(unittest.TestCase):
    def test_constants_and_initialization(self):
        controller = GamepadController()
        self.assertEqual(DPAD_UP, 0x0001)
        self.assertEqual(BUTTON_A, 0x1000)
        self.assertFalse(controller._running)

    def test_callbacks_registration(self):
        controller = GamepadController()
        triggered = []

        controller.on_a = lambda: triggered.append("A")
        controller.on_y = lambda: triggered.append("Y")

        self.assertIsNotNone(controller.on_a)
        self.assertIsNotNone(controller.on_y)


if __name__ == "__main__":
    unittest.main()

"""Testes unitários para o cliente Discord Rich Presence."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rom_cli.core.discord_rpc import DiscordRPC


class TestDiscordRPC(unittest.TestCase):
    def test_rpc_initialization(self):
        rpc = DiscordRPC(client_id="123456789")
        self.assertEqual(rpc.client_id, "123456789")
        self.assertFalse(rpc._connected)

    def test_graceful_fallback_when_discord_offline(self):
        """Verifica que chamadas de Rich Presence não quebram mesmo sem Discord rodando."""
        rpc = DiscordRPC()
        # Força pipe inexistente
        rpc._get_pipe_path = lambda: None

        connected = rpc.connect()
        self.assertFalse(connected)

        # Não deve disparar exceção
        success = rpc.update_game_activity("Super Mario World", "SNES")
        self.assertFalse(success)

        rpc.clear_activity()
        rpc.close()

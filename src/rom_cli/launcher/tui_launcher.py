"""Interface TUI dedicada para o Launcher de Jogos Locais."""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from rom_cli.config import OUT_DIR, PLATFORM_LABELS
from rom_cli.core.utils import human_size
from rom_cli.launcher.scanner import LibraryScanner, InstalledGame
from rom_cli.launcher.registry import EmulatorRegistry


def launch_launcher_tui(outdir: Optional[Path] = None):
    from textual.app import App, ComposeResult
    from textual.widgets import Input, DataTable, Footer, Header, Static, OptionList
    from textual.widgets.option_list import Option
    from textual.containers import Horizontal, Vertical
    from rich.text import Text as RT

    scanner = LibraryScanner(outdir or OUT_DIR)
    registry = EmulatorRegistry()

    class RomLauncherApp(App):
        TITLE = "rom launcher"
        CSS = """
        #main-container { height: 1fr; }
        #left-pane { width: 28; height: 100%; border-right: vline $primary; padding: 0 1; }
        #right-pane { width: 1fr; height: 100%; padding: 0 1; }
        Input { dock: top; }
        #status { height: 3; background: $surface; padding: 0 1; dock: bottom; }
        DataTable { height: 1fr; }
        """
        BINDINGS = [
            ("q", "quit", "Sair"),
            ("enter", "play", "Jogar"),
            ("r", "refresh", "Recarregar"),
        ]

        def __init__(self):
            super().__init__()
            self.library: Dict[str, List[InstalledGame]] = {}
            self.current_platform = "all"
            self.current_games: List[InstalledGame] = []

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with Horizontal(id="main-container"):
                with Vertical(id="left-pane"):
                    yield Static("📁 Plataformas", id="left-title")
                    yield OptionList(id="platform-list")
                with Vertical(id="right-pane"):
                    yield Input(placeholder="Filtrar jogos instalados…")
                    yield DataTable(cursor_type="row")
            yield Footer()
            yield Static("Carregando biblioteca…", id="status")

        def on_mount(self):
            table = self.query_one(DataTable)
            table.add_columns("Título", "Plataforma", "Formato", "Tamanho")
            self._reload_library()

        def _reload_library(self):
            self.library = scanner.scan_all()
            total_games = sum(len(g) for g in self.library.values())

            # Atualiza lista de plataformas à esquerda
            plist = self.query_one(OptionList)
            plist.clear_options()
            plist.add_option(Option(f"Todas ({total_games})", id="all"))

            for pk, games in sorted(self.library.items()):
                label = PLATFORM_LABELS.get(pk, pk.upper())
                plist.add_option(Option(f"{label} ({len(games)})", id=pk))

            self._show_games()

        def _show_games(self, filter_text: str = ""):
            table = self.query_one(DataTable)
            table.clear()

            games = []
            if self.current_platform == "all":
                for g_list in self.library.values():
                    games.extend(g_list)
            else:
                games = self.library.get(self.current_platform, [])

            if filter_text:
                q = filter_text.lower()
                games = [g for g in games if q in g.title.lower()]

            self.current_games = games

            for i, g in enumerate(games):
                table.add_row(
                    g.title,
                    g.platform_label,
                    f".{g.extension}",
                    human_size(g.size),
                    key=str(i)
                )

            total = len(games)
            self.query_one(Static, id="status").update(
                f"{total} jogo(s) encontrado(s) · Enter para jogar · q para sair"
            )

        def on_option_list_option_selected(self, event):
            self.current_platform = event.option_id
            self._show_games(self.query_one(Input).value)

        def on_input_changed(self, event):
            self._show_games(event.value)

        def action_refresh(self):
            self._reload_library()

        def action_play(self):
            table = self.query_one(DataTable)
            if table.cursor_row is None or not self.current_games:
                return

            game = self.current_games[table.cursor_row]
            emu = registry.find_emulator(game.platform_key)
            status_box = self.query_one(Static, id="status")

            if not emu:
                status_box.update(f"✖ Nenhum emulador encontrado para {game.platform_label}")
                return

            status_box.update(f"🚀 Iniciando {game.title} com {emu.name}…")
            try:
                subprocess.Popen([str(emu), str(game.path)])
            except Exception as e:
                status_box.update(f"✖ Erro ao iniciar emulador: {e}")

    app = RomLauncherApp()
    app.run()

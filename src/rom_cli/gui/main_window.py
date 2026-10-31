"""Janela principal do ROM Launcher Desktop (GUI nativa em CustomTkinter)."""

import io
import os
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import filedialog
from typing import Dict, List, Optional
from PIL import Image

# Protege ambientes sem console no Windows (PyInstaller --noconsole / pythonw)
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()
if sys.stdin is None:
    sys.stdin = io.StringIO()

import customtkinter as ctk

from rom_cli.config import OUT_DIR, PLATFORM_LABELS
from rom_cli.core.downloader import get_unique_path, stream_download
from rom_cli.core.extractor import extract_archive
from rom_cli.core.gamepad import GAMEPAD
from rom_cli.core.launcher import launch_game
from rom_cli.core.ranking import rank, search_all
from rom_cli.core.retroachievements import RA_CLIENT
from rom_cli.core.roulette import pick_random_game
from rom_cli.core.scraper import fetch_boxart, get_cover_path
from rom_cli.core.tracker import TRACKER
from rom_cli.core.utils import human_size, safe_name
from rom_cli.core.validator import fix_magic_extension, validate_file
from rom_cli.launcher.registry import DEFAULT_EMULATORS, EmulatorRegistry
from rom_cli.launcher.scanner import InstalledGame, LibraryScanner
from rom_cli.models import RomItem
from rom_cli.providers import DLP, SOURCES

try:
    import winsound

    def play_click():
        try:
            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass
except Exception:
    def play_click():
        pass


PLATFORM_COLORS: Dict[str, str] = {
    "switch": "#e60012",
    "switchports": "#e60012",
    "ps1": "#003791",
    "ps2": "#003791",
    "ps3": "#003791",
    "ps4": "#003791",
    "ps5": "#003791",
    "psp": "#003791",
    "psv": "#003791",
    "xbox": "#107c10",
    "xbox360": "#107c10",
    "snes": "#7c3aed",
    "nes": "#dc2626",
    "gba": "#4f46e5",
    "gbc": "#7c3aed",
    "gb": "#64748b",
    "nds": "#0284c7",
    "n64": "#ea580c",
    "gc": "#4338ca",
    "wii": "#06b6d4",
    "genesis": "#1e40af",
    "dreamcast": "#f97316",
    "saturn": "#64748b",
    "arcade": "#b45309",
}

QUICK_PLATFORMS = [
    ("all", "Todos"),
    ("switch", "Switch"),
    ("ps2", "PS2"),
    ("xbox", "Xbox"),
    ("xbox360", "Xbox 360"),
    ("ps1", "PS1"),
    ("snes", "SNES"),
    ("gba", "GBA"),
    ("psp", "PSP"),
    ("nds", "NDS"),
]

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RomLauncherApp(ctk.CTk):
    def __init__(self, outdir: Optional[Path] = None):
        super().__init__()

        self.outdir = Path(outdir or OUT_DIR)
        self.scanner = LibraryScanner(self.outdir)
        self.registry = EmulatorRegistry()

        self.title("EmuCraft - Central de Emulação & Preservação")
        self.geometry("1100x700")
        self.minsize(950, 600)

        # Dados da biblioteca e busca
        self.library: Dict[str, List[InstalledGame]] = {}
        self.current_library_platform = "all"
        self.library_view_mode = "grid"  # 'grid' ou 'list'
        self.cover_cache: Dict[str, ctk.CTkImage] = {}
        self.search_results: List[RomItem] = []
        self.is_downloading = False

        self._setup_layout()
        self._select_tab("library")
        self.refresh_library()

        # Inicializa suporte a Gamepad (XInput / Modo Sofá)
        if GAMEPAD.is_available():
            GAMEPAD.on_y = lambda: self.after(0, self._spin_roulette)
            GAMEPAD.on_lb = lambda: self.after(0, self._gamepad_prev_platform)
            GAMEPAD.on_rb = lambda: self.after(0, self._gamepad_next_platform)
            GAMEPAD.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        GAMEPAD.stop()
        self.destroy()

    def _setup_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Barra Lateral (Sidebar Liquid Glass)
        self.sidebar = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0,
            fg_color=("#0f172a", "#0a0f1d"),
            border_width=1,
            border_color="#1e293b"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="🎮 EMUCRAFT",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#38bdf8"
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 25))

        self.btn_nav_library = ctk.CTkButton(
            self.sidebar,
            text="📚 Minha Biblioteca",
            height=38,
            corner_radius=8,
            anchor="w",
            command=lambda: self._select_tab("library")
        )
        self.btn_nav_library.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        self.btn_nav_store = ctk.CTkButton(
            self.sidebar,
            text="🔍 Baixar Jogos (Loja)",
            height=38,
            corner_radius=8,
            anchor="w",
            command=lambda: self._select_tab("store")
        )
        self.btn_nav_store.grid(row=2, column=0, padx=15, pady=5, sticky="ew")

        self.btn_nav_emulators = ctk.CTkButton(
            self.sidebar,
            text="⚙️ Emuladores & BIOS",
            height=38,
            corner_radius=8,
            anchor="w",
            command=lambda: self._select_tab("emulators")
        )
        self.btn_nav_emulators.grid(row=3, column=0, padx=15, pady=5, sticky="ew")

        self.btn_nav_saves = ctk.CTkButton(
            self.sidebar,
            text="💾 Saves & Backups",
            height=38,
            corner_radius=8,
            anchor="w",
            command=lambda: self._select_tab("saves")
        )
        self.btn_nav_saves.grid(row=4, column=0, padx=15, pady=5, sticky="ew")

        self.btn_open_folder = ctk.CTkButton(
            self.sidebar,
            text="📁 Abrir Pasta de ROMs",
            height=32,
            fg_color="transparent",
            border_width=1,
            border_color="#334155",
            corner_radius=8,
            text_color=("gray10", "#DCE4EE"),
            command=self._open_roms_folder
        )
        self.btn_open_folder.grid(row=6, column=0, padx=15, pady=(10, 8), sticky="ew")

        try:
            from rom_cli.core.discord_rpc import DISCORD_RPC
            discord_status = "🟢 Discord RPC Ativo" if DISCORD_RPC.connected else "⚪ Discord RPC Pronto"
        except Exception:
            discord_status = "⚪ Discord RPC Inativo"
        self.lbl_discord = ctk.CTkLabel(
            self.sidebar,
            text=discord_status,
            font=ctk.CTkFont(size=10),
            text_color="gray60"
        )
        self.lbl_discord.grid(row=7, column=0, padx=15, pady=(0, 15), sticky="w")

        # 2. Painel Central (Main Views)
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self._build_library_view()
        self._build_store_view()
        self._build_emulators_view()
        self._build_saves_view()

    def _select_tab(self, tab_name: str):
        play_click()
        self.view_library.grid_forget()
        self.view_store.grid_forget()
        self.view_emulators.grid_forget()
        self.view_saves.grid_forget()

        # Reseta estilos dos botões de navegação
        for btn, name in [
            (self.btn_nav_library, "library"),
            (self.btn_nav_store, "store"),
            (self.btn_nav_emulators, "emulators"),
            (self.btn_nav_saves, "saves"),
        ]:
            if name == tab_name:
                btn.configure(
                    fg_color="#0284c7",
                    hover_color="#0369a1",
                    text_color="#ffffff",
                    border_width=1,
                    border_color="#38bdf8"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray10", "#DCE4EE"),
                    border_width=0
                )

        if tab_name == "library":
            self.view_library.grid(row=0, column=0, sticky="nsew")
            self.refresh_library()
        elif tab_name == "store":
            self.view_store.grid(row=0, column=0, sticky="nsew")
        elif tab_name == "emulators":
            self.view_emulators.grid(row=0, column=0, sticky="nsew")
            self._refresh_emulators_list()
        elif tab_name == "saves":
            self.view_saves.grid(row=0, column=0, sticky="nsew")
            self._refresh_saves_list()

    # ==========================================
    # VIEW 1: BIBLIOTECA (INSTALLED GAMES) - LIQUID GLASS
    # ==========================================
    def _build_library_view(self):
        self.view_library = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_library.grid_rowconfigure(3, weight=1)
        self.view_library.grid_columnconfigure(0, weight=1)

        # 1. Barra de ferramentas superior
        top_bar = ctk.CTkFrame(self.view_library, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top_bar.grid_columnconfigure(0, weight=1)

        self.library_search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="🔍 Filtrar jogos da biblioteca...",
            height=36,
            corner_radius=8,
            border_color="#1e293b"
        )
        self.library_search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.library_search_entry.bind("<KeyRelease>", lambda e: self._render_library_cards())

        self.platform_filter_menu = ctk.CTkOptionMenu(
            top_bar,
            values=["Todas as Plataformas"],
            command=self._on_library_platform_changed,
            height=36,
            width=160,
            corner_radius=8
        )
        self.platform_filter_menu.grid(row=0, column=1, padx=(0, 8))

        self.sort_menu = ctk.CTkOptionMenu(
            top_bar,
            values=["Nome (A-Z)", "Mais Jogados", "Jogados Recentemente", "Maior Tamanho"],
            command=lambda c: self._render_library_cards(),
            height=36,
            width=150,
            corner_radius=8
        )
        self.sort_menu.grid(row=0, column=2, padx=(0, 8))

        self.view_mode_segmented = ctk.CTkSegmentedButton(
            top_bar,
            values=["⊞ Grade", "☰ Lista"],
            command=self._on_view_mode_changed,
            height=36,
            corner_radius=8
        )
        self.view_mode_segmented.set("⊞ Grade")
        self.view_mode_segmented.grid(row=0, column=3)

        self.btn_roulette = ctk.CTkButton(
            top_bar,
            text="🎲 Roleta",
            width=90,
            height=36,
            fg_color="#6366f1",
            hover_color="#4f46e5",
            corner_radius=8,
            command=self._spin_roulette
        )
        self.btn_roulette.grid(row=0, column=4, padx=(8, 0))

        # 2. Barra horizontal de filtros rápidos em cápsulas (Pills)
        self.pills_frame = ctk.CTkFrame(self.view_library, fg_color="transparent")
        self.pills_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.pill_buttons: Dict[str, ctk.CTkButton] = {}
        for pk, plabel in QUICK_PLATFORMS:
            btn = ctk.CTkButton(
                self.pills_frame,
                text=plabel,
                width=60 if pk == "all" else 72,
                height=26,
                corner_radius=13,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#0284c7" if pk == "all" else ("#1e293b", "#0f172a"),
                text_color="#ffffff" if pk == "all" else "gray80",
                border_width=1,
                border_color="#38bdf8" if pk == "all" else "#334155",
                hover_color="#0369a1",
                command=lambda p=pk: self._on_quick_pill_clicked(p)
            )
            btn.pack(side="left", padx=(0, 6))
            self.pill_buttons[pk] = btn

        # 3. Hero Spotlight Banner Container (Liquid Glass)
        self.hero_container = ctk.CTkFrame(
            self.view_library,
            corner_radius=12,
            fg_color=("#162032", "#0f1624"),
            border_width=1,
            border_color="#1f2e44"
        )
        self.hero_container.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # 4. Container rolável para os cards de jogos
        self.library_scroll = ctk.CTkScrollableFrame(self.view_library, fg_color="transparent")
        self.library_scroll.grid(row=3, column=0, sticky="nsew")
        self.library_scroll.grid_columnconfigure(0, weight=1)

        # 5. Barra de status da biblioteca
        self.library_status = ctk.CTkLabel(
            self.view_library,
            text="Carregando biblioteca...",
            anchor="w",
            text_color="gray70"
        )
        self.library_status.grid(row=4, column=0, sticky="ew", pady=(6, 0))

    def _on_quick_pill_clicked(self, platform_key: str):
        play_click()
        self.current_library_platform = platform_key
        if platform_key == "all":
            self.platform_filter_menu.set("Todas as Plataformas")
        else:
            label = PLATFORM_LABELS.get(platform_key, platform_key)
            for v in self.platform_filter_menu.cget("values"):
                if v.startswith(label):
                    self.platform_filter_menu.set(v)
                    break
        self._update_pill_styles()
        self._render_library_cards()

    def _update_pill_styles(self):
        for pk, btn in self.pill_buttons.items():
            if pk == self.current_library_platform:
                btn.configure(
                    fg_color="#0284c7",
                    border_color="#38bdf8",
                    text_color="#ffffff"
                )
            else:
                btn.configure(
                    fg_color=("#1e293b", "#0f172a"),
                    border_color="#334155",
                    text_color="gray80"
                )

    def _on_view_mode_changed(self, mode: str):
        self.library_view_mode = "grid" if "Grade" in mode else "list"
        self._render_library_cards()

    def refresh_library(self):
        self.library = self.scanner.scan_all()
        total = sum(len(g) for g in self.library.values())

        # Atualiza o dropdown de plataformas
        platforms = ["Todas as Plataformas"]
        for pk in sorted(self.library.keys()):
            label = PLATFORM_LABELS.get(pk, pk.upper())
            platforms.append(f"{label} ({len(self.library[pk])})")

        self.platform_filter_menu.configure(values=platforms)
        self._render_library_cards()
        self.library_status.configure(text=f"Total: {total} jogo(s) instalado(s) na pasta: {self.outdir}")

    def _on_library_platform_changed(self, choice: str):
        if choice == "Todas as Plataformas":
            self.current_library_platform = "all"
        else:
            label = choice.split(" (")[0]
            for k, v in PLATFORM_LABELS.items():
                if v == label:
                    self.current_library_platform = k
                    break
        self._update_pill_styles()
        self._render_library_cards()

    def _render_hero_banner(self, featured_game: Optional[InstalledGame]):
        for w in self.hero_container.winfo_children():
            w.destroy()

        if not featured_game:
            welcome_lbl = ctk.CTkLabel(
                self.hero_container,
                text="✨ Bem-vindo ao EmuCraft! Nenhum jogo encontrado nesta categoria.\nAcesse a aba 'Baixar Jogos (Loja)' para adicionar títulos com posters e metadados automáticos.",
                font=ctk.CTkFont(size=13),
                text_color="gray75"
            )
            welcome_lbl.pack(pady=18, padx=20)
            return

        self.hero_container.grid_columnconfigure(1, weight=1)

        # Poster da esquerda
        poster_box = ctk.CTkFrame(
            self.hero_container,
            width=96,
            height=130,
            corner_radius=8,
            fg_color=("#0f172a", "#090d16"),
            border_width=1,
            border_color="#24344d"
        )
        poster_box.grid(row=0, column=0, rowspan=3, padx=14, pady=12, sticky="nw")
        poster_box.pack_propagate(False)

        hero_img = ctk.CTkLabel(poster_box, text="🎮", font=ctk.CTkFont(size=36))
        hero_img.pack(expand=True, fill="both")
        self._load_hero_cover(featured_game, hero_img)

        # Informações centrais
        info_frame = ctk.CTkFrame(self.hero_container, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=(4, 14), pady=(12, 6), sticky="nsew")

        # Linha de badges (Tag "EM DESTAQUE" + Plataforma)
        badges_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        badges_row.pack(anchor="w", pady=(0, 4))

        stats = TRACKER.get_stats(featured_game.path.stem)
        tag_text = "🔥 ÚLTIMO JOGO INICIADO" if stats.get("last_played", 0) > 0 else "⭐ DESTAQUE DA BIBLIOTECA"
        tag_badge = ctk.CTkLabel(
            badges_row,
            text=f"  {tag_text}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#0284c7",
            text_color="#ffffff",
            corner_radius=6
        )
        tag_badge.pack(side="left", padx=(0, 8))

        plat_color = PLATFORM_COLORS.get(featured_game.platform_key, "#334155")
        plat_badge = ctk.CTkLabel(
            badges_row,
            text=f"  {featured_game.platform_label}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=plat_color,
            text_color="#ffffff",
            corner_radius=6
        )
        plat_badge.pack(side="left")

        # Título Grande do Jogo
        hero_title = ctk.CTkLabel(
            info_frame,
            text=featured_game.title,
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w"
        )
        hero_title.pack(anchor="w", pady=(2, 4))

        # Metadados
        playtime = TRACKER.format_playtime(featured_game.path.stem)
        last_played = TRACKER.format_last_played(featured_game.path.stem)
        meta_str = f"⏱️ Tempo Jogado: {playtime}   •   📅 Última vez: {last_played}   •   💾 Formato: .{featured_game.extension} ({human_size(featured_game.size)})"
        hero_meta = ctk.CTkLabel(
            info_frame,
            text=meta_str,
            font=ctk.CTkFont(size=11),
            text_color="gray75",
            anchor="w"
        )
        hero_meta.pack(anchor="w", pady=(0, 4))

        # Linha de Ações (Botões)
        actions_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        actions_row.pack(anchor="w", pady=(6, 2))

        btn_hero_play = ctk.CTkButton(
            actions_row,
            text="▶  JOGAR AGORA",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=34,
            width=140,
            fg_color="#10b981",
            hover_color="#059669",
            corner_radius=8,
            command=lambda g=featured_game: (play_click(), self._launch_game_action(g))
        )
        btn_hero_play.pack(side="left", padx=(0, 10))

        btn_hero_patch = ctk.CTkButton(
            actions_row,
            text="🔧 Traduzir (Patch)",
            font=ctk.CTkFont(size=12),
            height=34,
            width=130,
            fg_color=("#334155", "#1e293b"),
            hover_color="#475569",
            corner_radius=8,
            command=lambda g=featured_game: self._apply_patch_action(g)
        )
        btn_hero_patch.pack(side="left", padx=(0, 10))

        btn_hero_spin = ctk.CTkButton(
            actions_row,
            text="🎲 Outro Aleatório",
            font=ctk.CTkFont(size=12),
            height=34,
            width=130,
            fg_color="#6366f1",
            hover_color="#4f46e5",
            corner_radius=8,
            command=self._spin_roulette
        )
        btn_hero_spin.pack(side="left")

    def _load_hero_cover(self, game: InstalledGame, label: ctk.CTkLabel):
        cache_key = f"hero_{game.platform_key}_{game.path.stem}"
        if cache_key in self.cover_cache:
            label.configure(image=self.cover_cache[cache_key], text="")
            return

        disk_path = get_cover_path(game.title, game.platform_key)
        if disk_path.exists():
            try:
                with Image.open(disk_path) as img:
                    img_res = img.resize((96, 130), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img_res, dark_image=img_res, size=(96, 130))
                    self.cover_cache[cache_key] = ctk_img
                    label.configure(image=ctk_img, text="")
                    return
            except Exception:
                pass

        def worker():
            path = fetch_boxart(game.title, game.platform_key)
            if path and path.exists():
                try:
                    with Image.open(path) as img:
                        img_res = img.resize((96, 130), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(light_image=img_res, dark_image=img_res, size=(96, 130))
                        self.cover_cache[cache_key] = ctk_img
                        self.after(0, lambda: label.configure(image=ctk_img, text=""))
                except Exception:
                    pass
        threading.Thread(target=worker, daemon=True).start()

    def _render_library_cards(self):
        for widget in self.library_scroll.winfo_children():
            widget.destroy()

        filter_q = self.library_search_entry.get().strip().lower()

        games: List[InstalledGame] = []
        if self.current_library_platform == "all":
            for g_list in self.library.values():
                games.extend(g_list)
        else:
            games = self.library.get(self.current_library_platform, [])

        if filter_q:
            games = [g for g in games if filter_q in g.title.lower()]

        # Seleciona o jogo em destaque para o Hero Banner
        featured_game = None
        if games:
            recent_games = sorted(
                games,
                key=lambda g: TRACKER.get_stats(g.path.stem).get("last_played", 0),
                reverse=True
            )
            if TRACKER.get_stats(recent_games[0].path.stem).get("last_played", 0) > 0:
                featured_game = recent_games[0]
            else:
                featured_game = games[0]

        self._render_hero_banner(featured_game)

        if not games:
            empty_lbl = ctk.CTkLabel(
                self.library_scroll,
                text="Nenhum jogo encontrado nesta visualização.\nClique em 'Baixar Jogos' para buscar e adicionar novos títulos!",
                font=ctk.CTkFont(size=14),
                text_color="gray60"
            )
            empty_lbl.pack(pady=40)
            return

        # Ordenação
        sort_by = self.sort_menu.get()
        if sort_by == "Nome (A-Z)":
            games.sort(key=lambda g: g.title.lower())
        elif sort_by == "Mais Jogados":
            games.sort(key=lambda g: TRACKER.get_stats(g.path.stem).get("total_seconds", 0), reverse=True)
        elif sort_by == "Jogados Recentemente":
            games.sort(key=lambda g: TRACKER.get_stats(g.path.stem).get("last_played", 0), reverse=True)
        elif sort_by == "Maior Tamanho":
            games.sort(key=lambda g: g.size, reverse=True)

        if self.library_view_mode == "grid":
            self._render_grid_view(games)
        else:
            self._render_list_view(games)

    def _render_list_view(self, games: List[InstalledGame]):
        for game in games:
            card = ctk.CTkFrame(
                self.library_scroll,
                corner_radius=10,
                fg_color=("#1a2333", "#111827"),
                border_width=1,
                border_color="#1e293b"
            )
            card.pack(fill="x", pady=5, padx=2)
            card.grid_columnconfigure(0, weight=1)

            # Efeito Motion Hover
            def on_enter(e, f=card):
                f.configure(border_color="#38bdf8", fg_color=("#222f44", "#162032"))
            def on_leave(e, f=card):
                f.configure(border_color="#1e293b", fg_color=("#1a2333", "#111827"))
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

            playtime = TRACKER.format_playtime(game.path.stem)
            last_played = TRACKER.format_last_played(game.path.stem)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="w", padx=15, pady=10)

            title_row = ctk.CTkFrame(info_frame, fg_color="transparent")
            title_row.pack(anchor="w")

            plat_color = PLATFORM_COLORS.get(game.platform_key, "#0284c7")
            ctk.CTkLabel(
                title_row,
                text=f"  {game.platform_label}  ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=plat_color,
                text_color="#ffffff",
                corner_radius=6
            ).pack(side="left", padx=(0, 8))

            title_lbl = ctk.CTkLabel(
                title_row,
                text=game.title,
                font=ctk.CTkFont(size=15, weight="bold"),
                anchor="w"
            )
            title_lbl.pack(side="left")

            sub_lbl = ctk.CTkLabel(
                info_frame,
                text=f"Formato: .{game.extension}  •  Tam: {human_size(game.size)}  •  ⏱️ {playtime}  •  Última vez: {last_played}",
                font=ctk.CTkFont(size=12),
                text_color="gray70",
                anchor="w"
            )
            sub_lbl.pack(anchor="w", pady=(3, 0))
            self._load_card_achievements(game, sub_lbl)

            actions_frame = ctk.CTkFrame(card, fg_color="transparent")
            actions_frame.grid(row=0, column=1, padx=15, pady=10, sticky="e")

            btn_patch = ctk.CTkButton(
                actions_frame,
                text="🔧 Traduzir",
                width=85,
                height=34,
                font=ctk.CTkFont(size=12),
                fg_color=("#334155", "#1e293b"),
                hover_color="#475569",
                corner_radius=8,
                command=lambda g=game: self._apply_patch_action(g)
            )
            btn_patch.pack(side="left", padx=(0, 8))

            btn_play = ctk.CTkButton(
                actions_frame,
                text="▶ JOGAR",
                width=100,
                height=34,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#10b981",
                hover_color="#059669",
                corner_radius=8,
                command=lambda g=game: (play_click(), self._launch_game_action(g))
            )
            btn_play.pack(side="left")

    def _render_grid_view(self, games: List[InstalledGame]):
        cols = 4
        for c in range(cols):
            self.library_scroll.grid_columnconfigure(c, weight=1)

        for i, game in enumerate(games):
            r = i // cols
            c = i % cols

            card = ctk.CTkFrame(
                self.library_scroll,
                corner_radius=12,
                fg_color=("#1a2333", "#111827"),
                border_width=1,
                border_color="#1e293b"
            )
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")

            # Efeito Motion Hover
            def on_enter(e, f=card):
                f.configure(border_color="#38bdf8", fg_color=("#222f44", "#162032"))
            def on_leave(e, f=card):
                f.configure(border_color="#1e293b", fg_color=("#1a2333", "#111827"))
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

            # Box Art (Poster)
            cover_frame = ctk.CTkFrame(
                card,
                width=130,
                height=180,
                corner_radius=8,
                fg_color=("#0f172a", "#090d16"),
                border_width=1,
                border_color="#1e293b"
            )
            cover_frame.pack(padx=10, pady=(10, 6))
            cover_frame.pack_propagate(False)

            img_label = ctk.CTkLabel(cover_frame, text="🎮", font=ctk.CTkFont(size=32))
            img_label.pack(expand=True, fill="both")
            self._load_card_cover(game, img_label)

            # Platform capsule badge
            plat_color = PLATFORM_COLORS.get(game.platform_key, "#0284c7")
            badge = ctk.CTkLabel(
                card,
                text=f" {game.platform_label} ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=plat_color,
                text_color="#ffffff",
                corner_radius=6,
                height=18
            )
            badge.pack(padx=8, pady=(0, 4))

            # Título resumido
            display_title = game.title if len(game.title) <= 24 else game.title[:22] + "…"
            title_lbl = ctk.CTkLabel(card, text=display_title, font=ctk.CTkFont(size=13, weight="bold"))
            title_lbl.pack(padx=8, pady=(0, 2))

            # Detalhes (Tempo jogado)
            playtime = TRACKER.format_playtime(game.path.stem)
            meta_lbl = ctk.CTkLabel(
                card,
                text=f"⏱️ {playtime}",
                font=ctk.CTkFont(size=11),
                text_color="gray70"
            )
            meta_lbl.pack(padx=8, pady=(0, 6))
            self._load_grid_achievements(game, meta_lbl)

            btn_play = ctk.CTkButton(
                card,
                text="▶ JOGAR",
                height=32,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#10b981",
                hover_color="#059669",
                corner_radius=8,
                command=lambda g=game: (play_click(), self._launch_game_action(g))
            )
            btn_play.pack(fill="x", padx=12, pady=(0, 10))

    def _load_card_achievements(self, game: InstalledGame, label: ctk.CTkLabel):
        def worker():
            info = RA_CLIENT.get_game_info(game.title, game.platform_key)
            if info and info.get("achievements_count"):
                txt = f"  •  🏆 {info['achievements_count']} Conquistas ({info['points']} pts)"
                self.after(0, lambda: label.configure(text=label.cget("text") + txt))
        threading.Thread(target=worker, daemon=True).start()

    def _load_grid_achievements(self, game: InstalledGame, label: ctk.CTkLabel):
        def worker():
            info = RA_CLIENT.get_game_info(game.title, game.platform_key)
            if info and info.get("achievements_count"):
                cur_text = label.cget("text")
                parts = cur_text.split("\n", 1)
                new_text = f"{parts[0]} • 🏆 {info['achievements_count']}\n{parts[1]}" if len(parts) > 1 else f"{cur_text} • 🏆 {info['achievements_count']}"
                self.after(0, lambda: label.configure(text=new_text))
        threading.Thread(target=worker, daemon=True).start()

    def _spin_roulette(self):
        pk = None if self.current_library_platform == "all" else self.current_library_platform
        lucky = pick_random_game(platform_key=pk, outdir=self.outdir)
        if not lucky:
            self.library_status.configure(text="✖ Nenhum jogo encontrado na biblioteca para sortear.")
            return

        self.library_status.configure(text=f"🎲 Roleta sorteou: {lucky.title} ({lucky.platform_label})! Iniciando...")
        self._launch_game_action(lucky)

    def _gamepad_prev_platform(self):
        platforms = self.platform_filter_menu.cget("values")
        cur = self.platform_filter_menu.get()
        if cur in platforms:
            idx = (platforms.index(cur) - 1) % len(platforms)
            self.platform_filter_menu.set(platforms[idx])
            self._on_library_platform_changed(platforms[idx])

    def _gamepad_next_platform(self):
        platforms = self.platform_filter_menu.cget("values")
        cur = self.platform_filter_menu.get()
        if cur in platforms:
            idx = (platforms.index(cur) + 1) % len(platforms)
            self.platform_filter_menu.set(platforms[idx])
            self._on_library_platform_changed(platforms[idx])

    def _load_card_cover(self, game: InstalledGame, label: ctk.CTkLabel):
        cache_key = f"{game.platform_key}_{game.path.stem}"
        if cache_key in self.cover_cache:
            label.configure(image=self.cover_cache[cache_key], text="")
            return

        disk_path = get_cover_path(game.title, game.platform_key)
        if disk_path.exists():
            try:
                with Image.open(disk_path) as img:
                    img_res = img.resize((125, 175), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img_res, dark_image=img_res, size=(125, 175))
                    self.cover_cache[cache_key] = ctk_img
                    label.configure(image=ctk_img, text="")
                    return
            except Exception:
                pass

        # Dispara busca assíncrona na nuvem (Libretro Thumbnails)
        threading.Thread(target=self._async_fetch_cover, args=(game, label, cache_key), daemon=True).start()

    def _async_fetch_cover(self, game: InstalledGame, label: ctk.CTkLabel, cache_key: str):
        path = fetch_boxart(game.title, game.platform_key)
        if path and path.exists():
            try:
                with Image.open(path) as img:
                    img_res = img.resize((125, 175), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img_res, dark_image=img_res, size=(125, 175))
                    self.cover_cache[cache_key] = ctk_img
                    self.after(0, lambda: label.configure(image=ctk_img, text=""))
            except Exception:
                pass

    def _launch_game_action(self, game: InstalledGame):
        emu = self.registry.find_emulator(game.platform_key)
        if not emu:
            self.library_status.configure(
                text=f"✖ Nenhum emulador configurado para {game.platform_label}. Configure na aba 'Emuladores'."
            )
            return

        self.library_status.configure(text=f"🚀 Iniciando {game.title} via {emu.name}...")

        def on_end(duration_sec):
            self.after(0, self.refresh_library)

        success = launch_game(game.path, game.platform_key, on_session_end=on_end)
        if success:
            self.library_status.configure(text=f"✔ {game.title} em execução! Monitorando sessão...")
        else:
            self.library_status.configure(text=f"✖ Falha ao abrir emulador {emu}")

    def _apply_patch_action(self, game: InstalledGame):
        patch_file = filedialog.askopenfilename(
            title=f"Selecione o patch de tradução para {game.title}",
            filetypes=[("Patches de Tradução (*.ips;*.bps)", "*.ips;*.bps"), ("Todos os arquivos", "*.*")]
        )
        if not patch_file:
            return
        try:
            from rom_cli.core.patcher import apply_patch
            out_rom = apply_patch(game.path, patch_file)
            self.library_status.configure(text=f"✔ Tradução aplicada com sucesso! Gerado: {out_rom.name}")
            self.refresh_library()
        except Exception as e:
            self.library_status.configure(text=f"✖ Erro ao aplicar patch: {e}")

    # ==========================================
    # VIEW 2: LOJA / DOWNLOAD CENTER (ONLINE)
    # ==========================================
    def _build_store_view(self):
        self.view_store = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_store.grid_rowconfigure(1, weight=1)
        self.view_store.grid_columnconfigure(0, weight=1)

        # Barra de busca online
        search_bar = ctk.CTkFrame(self.view_store, fg_color="transparent")
        search_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_bar.grid_columnconfigure(0, weight=1)

        self.store_search_entry = ctk.CTkEntry(
            search_bar,
            placeholder_text="Digite o nome do jogo (ex.: Zelda, God of War, Halo)...",
            height=35
        )
        self.store_search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.store_search_entry.bind("<Return>", lambda e: self._start_online_search())

        # Plataformas suportadas para busca
        store_plat_choices = ["Todas as Plataformas"] + [PLATFORM_LABELS[k] for k in sorted(PLATFORM_LABELS.keys())]
        self.store_plat_menu = ctk.CTkOptionMenu(
            search_bar,
            values=store_plat_choices,
            height=35
        )
        self.store_plat_menu.grid(row=0, column=1, padx=(0, 10))

        self.btn_search = ctk.CTkButton(
            search_bar,
            text="Buscar ROMs",
            height=35,
            command=self._start_online_search
        )
        self.btn_search.grid(row=0, column=2)

        # Container rolável de resultados
        self.store_scroll = ctk.CTkScrollableFrame(self.view_store, fg_color="transparent")
        self.store_scroll.grid(row=1, column=0, sticky="nsew")
        self.store_scroll.grid_columnconfigure(0, weight=1)

        # Painel inferior de status e progresso de download
        self.download_panel = ctk.CTkFrame(self.view_store, corner_radius=8)
        self.download_panel.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.download_panel.grid_columnconfigure(0, weight=1)

        self.download_lbl = ctk.CTkLabel(
            self.download_panel,
            text="Pronto para buscar jogos em provedores preservados (Myrient, Sony CDN, Archive.org, dlarchive).",
            anchor="w",
            text_color="gray70"
        )
        self.download_lbl.grid(row=0, column=0, sticky="w", padx=15, pady=(8, 4))

        self.download_progress = ctk.CTkProgressBar(self.download_panel)
        self.download_progress.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        self.download_progress.set(0)

    def _start_online_search(self):
        query = self.store_search_entry.get().strip()
        if not query:
            return

        choice = self.store_plat_menu.get()
        platform_key = None
        if choice != "Todas as Plataformas":
            for k, v in PLATFORM_LABELS.items():
                if v == choice:
                    platform_key = k
                    break

        self.download_lbl.configure(text=f"🔍 Buscando '{query}' online nos provedores...")
        self.btn_search.configure(state="disabled")

        for widget in self.store_scroll.winfo_children():
            widget.destroy()

        loading_lbl = ctk.CTkLabel(self.store_scroll, text="Buscando catálogos... Aguarde.", font=ctk.CTkFont(size=14))
        loading_lbl.pack(pady=40)

        threading.Thread(target=self._search_worker, args=(query, platform_key), daemon=True).start()

    def _search_worker(self, query: str, platform_key: Optional[str]):
        try:
            results = search_all(query, platform_key=platform_key)
            ranked = rank(results, query)
            self.after(0, lambda: self._render_store_results(ranked))
        except Exception as e:
            self.after(0, lambda: self.download_lbl.configure(text=f"✖ Erro na busca: {e}"))
            self.after(0, lambda: self.btn_search.configure(state="normal"))

    def _render_store_results(self, results: List[RomItem]):
        self.btn_search.configure(state="normal")
        for widget in self.store_scroll.winfo_children():
            widget.destroy()

        if not results:
            ctk.CTkLabel(
                self.store_scroll,
                text="Nenhum resultado encontrado online. Tente simplificar o nome do jogo.",
                font=ctk.CTkFont(size=14),
                text_color="gray60"
            ).pack(pady=40)
            self.download_lbl.configure(text="Nenhum resultado.")
            return

        self.download_lbl.configure(text=f"{len(results)} resultados encontrados.")

        for item in results[:50]:
            card = ctk.CTkFrame(self.store_scroll, corner_radius=8, fg_color=("gray85", "gray20"))
            card.pack(fill="x", pady=4, padx=2)
            card.grid_columnconfigure(0, weight=1)

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.grid(row=0, column=0, sticky="w", padx=15, pady=8)

            star = "★ " if item.is_star else ""
            ctk.CTkLabel(
                info,
                text=f"{star}{item.title}",
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            ).pack(anchor="w")

            meta = f"Plataforma: {item.platform_label}  •  Tamanho: {human_size(item.size)}  •  Fonte: {item.source}"
            if item.kind:
                meta += f"  •  Tipo: {item.kind}"
            ctk.CTkLabel(info, text=meta, font=ctk.CTkFont(size=11), text_color="gray70", anchor="w").pack(anchor="w")

            btn_dl = ctk.CTkButton(
                card,
                text="⬇ Baixar",
                width=100,
                height=30,
                command=lambda it=item: self._download_online_item(it)
            )
            btn_dl.grid(row=0, column=1, padx=15, pady=8, sticky="e")

    def _download_online_item(self, item: RomItem):
        if self.is_downloading:
            self.download_lbl.configure(text="Aguarde o download atual terminar antes de iniciar outro.")
            return

        self.is_downloading = True
        self.download_progress.set(0)
        self.download_lbl.configure(text=f"Iniciando download de {item.title}...")

        threading.Thread(target=self._download_worker, args=(item,), daemon=True).start()

    def _download_worker(self, item: RomItem):
        try:
            folder = self.outdir / (item.platform_label or "outros")
            folder.mkdir(parents=True, exist_ok=True)

            if item.extra and item.extra.get("search_title"):
                found = DLP.search(item.extra["search_title"], item.extra.get("pk"))
                if found:
                    item = found[0]

            src = SOURCES[item.source]
            url, name = src.resolve(item)

            ext = (item.extra.get("ext") if item.extra else None) or "zip"
            if not ext.startswith("."):
                ext = f".{ext}"

            dest_path = get_unique_path(folder / safe_name(name or item.title, "rom", ext))

            def on_prog(read, total):
                if total > 0:
                    pct = read / total
                    self.after(0, lambda: self.download_progress.set(pct))
                    self.after(0, lambda: self.download_lbl.configure(
                        text=f"Baixando: {item.title[:45]} ({pct*100:.1f}%) - {human_size(read)}/{human_size(total)}"
                    ))

            referer = item.url if item.source not in ("dlarchive", "nps") else None
            stream_download(url, dest_path, referer=referer, on_progress=on_prog)
            dest_path = fix_magic_extension(dest_path)

            if not validate_file(dest_path):
                try:
                    dest_path.unlink()
                except OSError:
                    pass
                raise RuntimeError("Arquivo baixado parece incompleto ou corrompido.")

            # Se for ZIP, extrai automaticamente
            if dest_path.suffix.lower() == ".zip":
                self.after(0, lambda: self.download_lbl.configure(text=f"Extraindo {dest_path.name}..."))
                extract_archive(dest_path, remove_archive=False)

            self.after(0, lambda: self.download_progress.set(1.0))
            self.after(0, lambda: self.download_lbl.configure(
                text=f"✔ Download concluído com sucesso: {dest_path.name}"
            ))
            # Atualiza biblioteca
            self.after(0, self.refresh_library)
        except Exception as e:
            self.after(0, lambda: self.download_lbl.configure(text=f"✖ Falha no download: {e}"))
        finally:
            self.is_downloading = False

    # ==========================================
    # VIEW 3: CONFIGURAÇÃO DE EMULADORES
    # ==========================================
    def _build_emulators_view(self):
        self.view_emulators = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_emulators.grid_rowconfigure(1, weight=1)
        self.view_emulators.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            self.view_emulators,
            text="Configuração de Emuladores Instalados",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.grid(row=0, column=0, sticky="w", pady=(0, 15))

        self.emulators_scroll = ctk.CTkScrollableFrame(self.view_emulators, fg_color="transparent")
        self.emulators_scroll.grid(row=1, column=0, sticky="nsew")
        self.emulators_scroll.grid_columnconfigure(0, weight=1)

    def _refresh_emulators_list(self):
        for widget in self.emulators_scroll.winfo_children():
            widget.destroy()

        for pk, info in DEFAULT_EMULATORS.items():
            card = ctk.CTkFrame(self.emulators_scroll, corner_radius=8, fg_color=("gray85", "gray20"))
            card.pack(fill="x", pady=6, padx=2)
            card.grid_columnconfigure(0, weight=1)

            current_path = self.registry.find_emulator(pk)
            status_text = f"Caminho: {current_path}" if current_path else "Não detectado automaticamente"
            status_color = "#28a745" if current_path else "gray60"

            txt_frame = ctk.CTkFrame(card, fg_color="transparent")
            txt_frame.grid(row=0, column=0, sticky="w", padx=15, pady=10)

            plat_label = PLATFORM_LABELS.get(pk, pk.upper())
            title_text = f"{plat_label}  ({info['name']})"
            ctk.CTkLabel(txt_frame, text=title_text, font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(txt_frame, text=status_text, font=ctk.CTkFont(size=11), text_color=status_color, anchor="w").pack(anchor="w")

            from rom_cli.core.bios_checker import audit_bios
            bios_info = audit_bios(pk)
            if bios_info.get("status") == "ok":
                bios_txt = "🟢 BIOS detectada e pronta"
                bios_clr = "#28a745"
            elif bios_info.get("status") in ("missing_bios", "missing_folder"):
                bios_txt = f"🔴 {bios_info['message']}"
                bios_clr = "#e06c75"
            else:
                bios_txt = ""
                bios_clr = "gray50"

            if bios_txt:
                ctk.CTkLabel(txt_frame, text=bios_txt, font=ctk.CTkFont(size=11), text_color=bios_clr, anchor="w").pack(anchor="w")

            btn_browse = ctk.CTkButton(
                card,
                text="Selecionar .exe",
                width=110,
                height=30,
                command=lambda p=pk: self._browse_emulator_exe(p)
            )
            btn_browse.grid(row=0, column=1, padx=15, pady=10, sticky="e")

    def _browse_emulator_exe(self, platform_key: str):
        path = filedialog.askopenfilename(
            title=f"Selecione o executável para {PLATFORM_LABELS.get(platform_key, platform_key)}",
            filetypes=[("Executáveis (*.exe)", "*.exe"), ("Todos os arquivos", "*.*")]
        )
        if path:
            self.registry.set_emulator_path(platform_key, path)
            self._refresh_emulators_list()

    # ==========================================
    # VIEW 4: GERENCIADOR DE SAVES & BACKUPS
    # ==========================================
    def _build_saves_view(self):
        self.view_saves = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_saves.grid_rowconfigure(1, weight=1)
        self.view_saves.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self.view_saves, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        top_bar.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            top_bar,
            text="💾 Backups de Saves e Memory Cards",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.grid(row=0, column=0, sticky="w")

        btn_refresh = ctk.CTkButton(
            top_bar,
            text="🔄 Atualizar",
            width=100,
            command=self._refresh_saves_list
        )
        btn_refresh.grid(row=0, column=1, padx=(0, 8))

        btn_open_saves = ctk.CTkButton(
            top_bar,
            text="📁 Abrir Pasta de Backups",
            width=160,
            command=self._open_saves_folder
        )
        btn_open_saves.grid(row=0, column=2)

        self.saves_scroll = ctk.CTkScrollableFrame(self.view_saves, fg_color="transparent")
        self.saves_scroll.grid(row=1, column=0, sticky="nsew")
        self.saves_scroll.grid_columnconfigure(0, weight=1)

    def _open_saves_folder(self):
        from rom_cli.core.savesync import SAVES_BACKUP_DIR
        SAVES_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(SAVES_BACKUP_DIR))
        else:
            subprocess.run(["xdg-open", str(SAVES_BACKUP_DIR)])

    def _refresh_saves_list(self):
        for widget in self.saves_scroll.winfo_children():
            widget.destroy()

        from rom_cli.core.savesync import list_save_backups
        backups = list_save_backups()

        if not backups:
            empty_lbl = ctk.CTkLabel(
                self.saves_scroll,
                text="Nenhum snapshot de save encontrado.\nAo jogar e encerrar uma sessão de emulador, um backup automático será criado aqui!",
                font=ctk.CTkFont(size=13),
                text_color="gray60"
            )
            empty_lbl.pack(pady=40)
            return

        for b in backups:
            card = ctk.CTkFrame(self.saves_scroll, corner_radius=8, fg_color=("gray85", "gray20"))
            card.pack(fill="x", pady=5, padx=2)
            card.grid_columnconfigure(0, weight=1)

            txt_frame = ctk.CTkFrame(card, fg_color="transparent")
            txt_frame.grid(row=0, column=0, sticky="w", padx=15, pady=8)

            plat_label = PLATFORM_LABELS.get(b["platform"], b["platform"].upper())
            ctk.CTkLabel(
                txt_frame,
                text=f"{plat_label}  •  {b['filename']}",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            ).pack(anchor="w")

            ctk.CTkLabel(
                txt_frame,
                text=f"Tamanho: {human_size(b['size_bytes'])}  •  Data: {b['created_at']}",
                font=ctk.CTkFont(size=11),
                text_color="gray70",
                anchor="w"
            ).pack(anchor="w")

            btn_restore = ctk.CTkButton(
                card,
                text="↺ Restaurar",
                width=100,
                height=30,
                fg_color="#17a2b8",
                hover_color="#138496",
                command=lambda p=b["path"]: self._restore_save_action(p)
            )
            btn_restore.grid(row=0, column=1, padx=15, pady=8, sticky="e")

    def _restore_save_action(self, zip_path: str):
        from rom_cli.core.savesync import restore_save_backup
        if restore_save_backup(zip_path):
            self.library_status.configure(text=f"✔ Save restaurado com sucesso a partir de {Path(zip_path).name}!")
        else:
            self.library_status.configure(text=f"✖ Falha ao restaurar save.")

    def _open_roms_folder(self):
        self.outdir.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(self.outdir))
        else:
            subprocess.run(["xdg-open", str(self.outdir)])


def main():
    app = RomLauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()

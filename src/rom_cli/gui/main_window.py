"""Janela principal do ROM Launcher Desktop (GUI nativa em CustomTkinter)."""

import os
import subprocess
import threading
from pathlib import Path
from tkinter import filedialog
from typing import Dict, List, Optional

import customtkinter as ctk

from rom_cli.config import OUT_DIR, PLATFORM_LABELS
from rom_cli.core.downloader import get_unique_path, stream_download
from rom_cli.core.extractor import extract_archive
from rom_cli.core.launcher import launch_game
from rom_cli.core.ranking import rank, search_all
from rom_cli.core.utils import human_size, safe_name
from rom_cli.core.validator import fix_magic_extension, validate_file
from rom_cli.launcher.registry import DEFAULT_EMULATORS, EmulatorRegistry
from rom_cli.launcher.scanner import InstalledGame, LibraryScanner
from rom_cli.models import RomItem
from rom_cli.providers import DLP, SOURCES

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RomLauncherApp(ctk.CTk):
    def __init__(self, outdir: Optional[Path] = None):
        super().__init__()

        self.outdir = Path(outdir or OUT_DIR)
        self.scanner = LibraryScanner(self.outdir)
        self.registry = EmulatorRegistry()

        self.title("ROM Launcher - Central de Emulação & Preservação")
        self.geometry("1100x700")
        self.minsize(950, 600)

        # Dados da biblioteca e busca
        self.library: Dict[str, List[InstalledGame]] = {}
        self.current_library_platform = "all"
        self.search_results: List[RomItem] = []
        self.is_downloading = False

        self._setup_layout()
        self._select_tab("library")
        self.refresh_library()

    def _setup_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Barra Lateral (Sidebar)
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="🎮 ROM LAUNCHER",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 25))

        self.btn_nav_library = ctk.CTkButton(
            self.sidebar,
            text="📚 Minha Biblioteca",
            height=36,
            anchor="w",
            command=lambda: self._select_tab("library")
        )
        self.btn_nav_library.grid(row=1, column=0, padx=15, pady=6, sticky="ew")

        self.btn_nav_store = ctk.CTkButton(
            self.sidebar,
            text="🔍 Baixar Jogos (Loja)",
            height=36,
            anchor="w",
            command=lambda: self._select_tab("store")
        )
        self.btn_nav_store.grid(row=2, column=0, padx=15, pady=6, sticky="ew")

        self.btn_nav_emulators = ctk.CTkButton(
            self.sidebar,
            text="⚙️ Emuladores",
            height=36,
            anchor="w",
            command=lambda: self._select_tab("emulators")
        )
        self.btn_nav_emulators.grid(row=3, column=0, padx=15, pady=6, sticky="ew")

        self.btn_open_folder = ctk.CTkButton(
            self.sidebar,
            text="📁 Abrir Pasta de ROMs",
            height=32,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "#DCE4EE"),
            command=self._open_roms_folder
        )
        self.btn_open_folder.grid(row=6, column=0, padx=15, pady=(10, 20), sticky="ew")

        # 2. Painel Central (Main Views)
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self._build_library_view()
        self._build_store_view()
        self._build_emulators_view()

    def _select_tab(self, tab_name: str):
        self.view_library.grid_forget()
        self.view_store.grid_forget()
        self.view_emulators.grid_forget()

        # Reseta estilos dos botões de navegação
        for btn, name in [
            (self.btn_nav_library, "library"),
            (self.btn_nav_store, "store"),
            (self.btn_nav_emulators, "emulators")
        ]:
            if name == tab_name:
                btn.configure(fg_color=["#3a7ebf", "#1f538d"], text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "#DCE4EE"))

        if tab_name == "library":
            self.view_library.grid(row=0, column=0, sticky="nsew")
            self.refresh_library()
        elif tab_name == "store":
            self.view_store.grid(row=0, column=0, sticky="nsew")
        elif tab_name == "emulators":
            self.view_emulators.grid(row=0, column=0, sticky="nsew")
            self._refresh_emulators_list()

    # ==========================================
    # VIEW 1: BIBLIOTECA (INSTALLED GAMES)
    # ==========================================
    def _build_library_view(self):
        self.view_library = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.view_library.grid_rowconfigure(1, weight=1)
        self.view_library.grid_columnconfigure(0, weight=1)

        # Barra de ferramentas superior
        top_bar = ctk.CTkFrame(self.view_library, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top_bar.grid_columnconfigure(0, weight=1)

        self.library_search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="🔍 Filtrar jogos da biblioteca...",
            height=35
        )
        self.library_search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.library_search_entry.bind("<KeyRelease>", lambda e: self._render_library_cards())

        self.platform_filter_menu = ctk.CTkOptionMenu(
            top_bar,
            values=["Todas as Plataformas"],
            command=self._on_library_platform_changed,
            height=35
        )
        self.platform_filter_menu.grid(row=0, column=1, sticky="e")

        # Container rolável para os cards de jogos
        self.library_scroll = ctk.CTkScrollableFrame(self.view_library, fg_color="transparent")
        self.library_scroll.grid(row=1, column=0, sticky="nsew")
        self.library_scroll.grid_columnconfigure(0, weight=1)

        # Barra de status da biblioteca
        self.library_status = ctk.CTkLabel(
            self.view_library,
            text="Carregando biblioteca...",
            anchor="w",
            text_color="gray70"
        )
        self.library_status.grid(row=2, column=0, sticky="ew", pady=(8, 0))

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
            # Extrai o label
            label = choice.split(" (")[0]
            # Mapeia de volta para pk
            for k, v in PLATFORM_LABELS.items():
                if v == label:
                    self.current_library_platform = k
                    break
        self._render_library_cards()

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

        if not games:
            empty_lbl = ctk.CTkLabel(
                self.library_scroll,
                text="Nenhum jogo encontrado nesta visualização.\nClique em 'Baixar Jogos' para buscar e adicionar novos títulos!",
                font=ctk.CTkFont(size=14),
                text_color="gray60"
            )
            empty_lbl.pack(pady=40)
            return

        for game in games:
            card = ctk.CTkFrame(self.library_scroll, corner_radius=8, fg_color=("gray85", "gray20"))
            card.pack(fill="x", pady=5, padx=2)
            card.grid_columnconfigure(0, weight=1)

            # Informações do jogo
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="w", padx=15, pady=10)

            title_lbl = ctk.CTkLabel(
                info_frame,
                text=game.title,
                font=ctk.CTkFont(size=15, weight="bold"),
                anchor="w"
            )
            title_lbl.pack(anchor="w")

            sub_lbl = ctk.CTkLabel(
                info_frame,
                text=f"{game.platform_label}  •  Formato: .{game.extension}  •  Tamanho: {human_size(game.size)}",
                font=ctk.CTkFont(size=12),
                text_color="gray70",
                anchor="w"
            )
            sub_lbl.pack(anchor="w")

            # Botão Jogar
            btn_play = ctk.CTkButton(
                card,
                text="▶ JOGAR",
                width=110,
                height=34,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#28a745",
                hover_color="#218838",
                command=lambda g=game: self._launch_game_action(g)
            )
            btn_play.grid(row=0, column=1, padx=15, pady=10, sticky="e")

    def _launch_game_action(self, game: InstalledGame):
        emu = self.registry.find_emulator(game.platform_key)
        if not emu:
            self.library_status.configure(
                text=f"✖ Nenhum emulador configurado para {game.platform_label}. Configure na aba 'Emuladores'."
            )
            return

        self.library_status.configure(text=f"🚀 Iniciando {game.title} via {emu.name}...")
        success = launch_game(game.path, game.platform_key)
        if success:
            self.library_status.configure(text=f"✔ {game.title} em execução!")
        else:
            self.library_status.configure(text=f"✖ Falha ao abrir emulador {emu}")

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

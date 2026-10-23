"""Interface TUI com Textual para navegação e download de ROMs."""

from typing import Optional, List
from pathlib import Path

from rom_cli.config import OUT_DIR, PLATFORM_LABELS
from rom_cli.core.utils import human_size, safe_name
from rom_cli.core.ranking import search_all, rank, browse_items
from rom_cli.core.downloader import stream_download, get_unique_path
from rom_cli.core.validator import validate_file, fix_magic_extension
from rom_cli.providers import SOURCES, DLP
from rom_cli.models import RomItem


def download_item(item: RomItem, outdir: Path, on_progress=None) -> Path:
    if on_progress:
        on_progress(0, 0, f"procurando: {item.title[:45]}…")
    if item.extra and item.extra.get("search_title"):
        found = DLP.search(item.extra["search_title"], item.extra.get("pk"))
        if not found:
            raise RuntimeError(f"não achei '{item.title}' no dlpsgame")
        item = found[0]

    src = SOURCES[item.source]
    if on_progress:
        on_progress(0, 0, f"pegando link: {item.title[:45]}…")
    url, name = src.resolve(item)

    # Obter extensão
    ext = (item.extra.get("ext") if item.extra else None) or "zip"
    if not ext.startswith("."):
        ext = f".{ext}"

    folder = outdir / (item.platform_label or "outros")
    folder.mkdir(parents=True, exist_ok=True)
    dest_path = get_unique_path(folder / safe_name(name or item.title, "rom", ext))

    import time
    start = time.time()

    def cb(read, total):
        if not on_progress:
            return
        pct = read * 100 / total if total else 0
        bps = read / max(time.time() - start, 0.1)
        on_progress(read, total, f"{pct:5.1f}%  {human_size(read)}/{human_size(total)}  {bps / 1048576:.1f} MB/s")

    referer = item.url if item.source not in ("dlarchive", "nps") else None
    stream_download(url, dest_path, referer=referer, on_progress=cb)
    dest_path = fix_magic_extension(dest_path)
    if not validate_file(dest_path):
        try:
            dest_path.unlink()
        except OSError:
            pass
        raise RuntimeError("arquivo inválido (link expirado?)")
    return dest_path


def launch_tui(platform_key: str = "", query: str = "", outdir: Optional[Path] = None, force: bool = False):
    import threading
    from textual.app import App, ComposeResult
    from textual.widgets import Input, DataTable, Footer, Header, Static
    from textual.widgets.option_list import Option, OptionList
    from textual.screen import ModalScreen
    from textual.containers import Vertical
    from textual.binding import Binding
    from rich.text import Text as RT

    class OptionsScreen(ModalScreen):
        CSS = """
        OptionsScreen { align: center middle; background: $background 60%; }
        #opts { width: 64; height: auto; max-height: 80%; background: $surface;
                border: round $primary; padding: 1 2; }
        #opts-title { text-style: bold; margin-bottom: 1; }
        #opts-list { height: auto; }
        #opts-hint { text-style: dim italic; margin-top: 1; }
        """
        BINDINGS = [
            Binding("escape", "cancel", "Fechar"),
            Binding("ctrl+b", "cancel", "Fechar", show=False),
            Binding("q", "cancel", "Fechar", show=False),
        ]

        def __init__(self, options):
            super().__init__()
            self.options = options

        def compose(self) -> ComposeResult:
            with Vertical(id="opts"):
                yield Static("Opções", id="opts-title")
                yield OptionList(*[Option(o[0], id=o[1]) for o in self.options], id="opts-list")
                yield Static("↑↓ navega · Enter seleciona · esc fecha", id="opts-hint")

        def on_option_list_option_selected(self, event):
            self.dismiss(event.option_id)

        def action_cancel(self):
            self.dismiss(None)

    class PlataformasScreen(OptionsScreen):
        def compose(self) -> ComposeResult:
            with Vertical(id="opts"):
                yield Static("Plataforma", id="opts-title")
                opts = [("todas", "all")] + [(PLATFORM_LABELS[k], k) for k in sorted(PLATFORM_LABELS)]
                yield OptionList(*[Option(t, id=i) for t, i in opts], id="opts-list")
                yield Static("↑↓ navega · Enter escolhe · esc fecha", id="opts-hint")

    class RomApp(App):
        TITLE = "rom"
        CSS = """
        Input { dock: top; }
        #status { height: 3; background: $surface; padding: 0 1; dock: bottom; }
        Footer { dock: bottom; }
        DataTable { height: 1fr; }
        """
        BINDINGS = [
            ("q", "quit", "Sair"),
            ("d", "download", "Baixar"),
            ("space", "toggle", "Selecionar"),
            ("p", "platform", "Plataforma"),
            ("n", "next_page", "Página+"),
            ("b", "prev_page", "Página-"),
            ("ctrl+b", "palette", "Opções"),
            ("ctrl+a", "select_all", "Marcar todos"),
            ("ctrl+n", "select_none", "Limpar"),
        ]

        def __init__(self, platform_key: str = "", query: str = "", outdir: Optional[Path] = None, force: bool = False):
            super().__init__()
            self.results: List[RomItem] = []
            self.selected = set()
            self.last_query = ""
            self.pk = platform_key or ""
            self.initial_query = query or ""
            self.outdir = outdir or OUT_DIR
            self.force = force
            self.browse_items_list = None
            self.page = 0
            self.col_keys = []
            self._busy = None
            self._frame = 0

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Input(placeholder="Digite o nome do jogo e Enter…  (p troca plataforma)")
            yield DataTable(cursor_type="row")
            yield Footer()
            yield Static("", id="status")

        def on_mount(self):
            table = self.query_one(DataTable)
            table.add_columns(" ", "Título", "Plataforma", "Tipo", "Tam", "Fonte")
            self.col_keys = list(table.columns.keys())
            self.set_interval(0.1, self._tick)
            self._set_status(self._hint())
            self.query_one(Input).focus()
            if self.initial_query:
                self.query_one(Input).value = self.initial_query
                self._start_search(self.initial_query)
            elif self.pk:
                self._start_browse(self.pk)
            else:
                self.call_after_refresh(self._open_platforms)

        def _tick(self):
            if not self._busy:
                return
            frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            self._frame += 1
            self.query_one(Static).update(f"{frames[self._frame % len(frames)]} {self._busy}")

        def _hint(self):
            plat = PLATFORM_LABELS.get(self.pk, "todas") if self.pk else "todas"
            return (f"plataforma: {plat} · espaço marca · d baixa · p navega/troca · "
                    f"n/b página · ctrl+b opções · q sai")

        def _set_status(self, msg):
            self._busy = None
            self.query_one(Static).update(msg)

        def _busy_msg(self, msg):
            self._busy = msg

        def on_input_submitted(self, event):
            q = event.value.strip()
            if q:
                self._start_search(q)

        def _start_search(self, q):
            self.last_query = q
            self.selected.clear()
            self._busy = f"buscando '{q}'…"
            self.query_one(Static).update(f"⠋ buscando '{q}'…")
            threading.Thread(target=self._search_bg, args=(q,), daemon=True).start()

        def _search_bg(self, q):
            try:
                results = search_all(
                    q, self.pk or None,
                    on_progress=lambda d, t: self._busy_msg(f"montando índice do catálogo… {d}/{t}"),
                    force=self.force
                )
                self.force = False
                self.call_from_thread(self._show, rank(results, q))
            except Exception as e:
                self.call_from_thread(self._set_status, f"✖ erro na busca: {e}")

        def _show(self, results):
            self.browse_items_list = None
            table = self.query_one(DataTable)
            table.clear()
            self.results = results
            for i, r in enumerate(results[:200]):
                table.add_row(*self._cells(i, r), key=str(i))
            table.focus()
            msg = f"{len(results)} resultados" if results else "nada encontrado"
            self._set_status(f"{msg} — {self._hint()}")

        def _start_browse(self, pk):
            self.last_query = ""
            self.selected.clear()
            self._busy = f"abrindo {PLATFORM_LABELS.get(pk, pk)}…"
            self.query_one(Static).update(f"⠋ {self._busy}")
            threading.Thread(target=self._browse_bg, args=(pk,), daemon=True).start()

        def _browse_bg(self, pk):
            try:
                self.call_from_thread(self._set_browse, browse_items(pk))
            except Exception as e:
                self.call_from_thread(self._set_status, f"✖ {e}")

        def _set_browse(self, items):
            self.browse_items_list = items
            self.page = 0
            self._render_page()

        def _render_page(self):
            items = self.browse_items_list or []
            size = 300
            pages = max(1, (len(items) + size - 1) // size)
            self.page = max(0, min(self.page, pages - 1))
            chunk = items[self.page * size:(self.page + 1) * size]
            self.results = chunk
            self.selected.clear()
            table = self.query_one(DataTable)
            table.clear()
            for i, r in enumerate(chunk):
                table.add_row(*self._cells(i, r), key=str(i))
            table.focus()
            plat = PLATFORM_LABELS.get(self.pk, self.pk or "todas")
            self._set_status(f"{plat} · {len(items)} itens · página {self.page + 1}/{pages}"
                             " — n/b página · espaço marca · d baixa · q sai")

        def action_next_page(self):
            if self.browse_items_list is None:
                return
            self.page += 1
            self._render_page()

        def action_prev_page(self):
            if self.browse_items_list is None:
                return
            self.page = max(0, self.page - 1)
            self._render_page()

        def _cells(self, i: int, r: RomItem):
            sel = i in self.selected
            mark = RT("  ✔  ", style="black on green") if sel else ""
            style = "black on dark_green" if sel else None
            star = "★ " if r.is_star else ""
            vals = [
                mark,
                star + r.title[:60],
                r.platform_label,
                r.kind or "-",
                human_size(r.size) if r.size else "?",
                r.source
            ]
            out = [mark]
            for v in vals[1:]:
                out.append(RT(str(v), style=style) if style else str(v))
            return out

        def _redraw(self):
            table = self.query_one(DataTable)
            for i, r in enumerate(self.results[:200]):
                for ck, val in zip(self.col_keys, self._cells(i, r)):
                    table.update_cell(str(i), ck, val)

        def _status_sel(self):
            n = len(self.selected)
            msg = f"{len(self.results)} resultados"
            if n:
                msg += f" · ✔ {n} selecionado(s)"
            self._set_status(msg + " — " + self._hint())

        def action_toggle(self):
            table = self.query_one(DataTable)
            if table.cursor_row is None or not self.results:
                return
            i = table.cursor_row
            self.selected.symmetric_difference_update({i})
            self._redraw()
            self._status_sel()

        def action_select_all(self):
            self.selected = set(range(len(self.results[:200])))
            self._redraw()
            self._status_sel()

        def action_select_none(self):
            self.selected.clear()
            self._redraw()
            self._status_sel()

        def action_platform(self):
            self._open_platforms()

        def _open_platforms(self):
            def chosen(val):
                if val is None:
                    return
                self.pk = "" if val == "all" else val
                if self.last_query:
                    self._start_search(self.last_query)
                elif self.pk:
                    self._start_browse(self.pk)
                else:
                    self._set_status("plataforma: todas — digite um nome e Enter")
            self.push_screen(PlataformasScreen([]), callback=chosen)

        def action_palette(self):
            self.push_screen(
                OptionsScreen([
                    ("Baixar selecionados", "sel"),
                    ("Baixar o atual", "cur"),
                    ("Navegar nesta plataforma", "browse"),
                    ("Trocar plataforma", "plat"),
                    ("Marcar todos", "all"),
                    ("Limpar seleção", "none"),
                ]),
                callback=self._palette,
            )

        def _palette(self, choice):
            if choice is None:
                return
            if choice == "sel":
                self._batch([self.results[i] for i in sorted(self.selected)])
            elif choice == "cur":
                self.action_download()
            elif choice == "browse":
                if self.pk:
                    self._start_browse(self.pk)
                else:
                    self.action_platform()
            elif choice == "all":
                self.action_select_all()
            elif choice == "none":
                self.action_select_none()
            elif choice == "plat":
                self.action_platform()

        def on_data_table_row_selected(self, event):
            table = self.query_one(DataTable)
            if table.cursor_row is not None and self.results:
                self.selected.add(table.cursor_row)
                self._redraw()
                self.action_palette()

        def action_download(self):
            table = self.query_one(DataTable)
            if table.cursor_row is None or not self.results:
                return
            self._batch([self.results[table.cursor_row]])

        def _batch(self, rows: List[RomItem]):
            if not rows:
                self._set_status("nada selecionado")
                return
            self._set_status(f"baixando 0/{len(rows)}…")
            threading.Thread(target=self._batch_bg, args=(rows,), daemon=True).start()

        def _batch_bg(self, rows: List[RomItem]):
            ok, fail, total = 0, 0, len(rows)
            for n, r in enumerate(rows, 1):
                label = f"{n}/{total} {r.title[:38]}"

                def prog(read, tot, msg, label=label):
                    self.call_from_thread(self._set_status, f"baixando {label} · {msg}")
                try:
                    dest = download_item(r, self.outdir, on_progress=prog)
                    ok += 1
                    self.call_from_thread(self._set_status, f"✔ {dest}")
                except Exception as e:
                    fail += 1
                    self.call_from_thread(self._set_status, f"✖ {r.title[:40]}: {e}")
            self.call_from_thread(
                self._set_status,
                f"✔ {ok}/{total} baixados em {self.outdir}" + (f" · {fail} falharam" if fail else "")
            )

    app = RomApp(platform_key=platform_key, query=query, outdir=outdir, force=force)
    app.run()


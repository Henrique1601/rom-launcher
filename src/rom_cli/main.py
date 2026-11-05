"""Ponto de entrada do CLI (Command Line Interface)."""

import argparse
import io
import os
import sys
from pathlib import Path
from typing import List

if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()
if sys.stdin is None:
    sys.stdin = io.StringIO()

from rom_cli.config import (
    OUT_DIR, PLATFORMS, PLATFORM_LABELS, INDEX_FILE
)
from rom_cli.core.utils import write, status, clear_status, human_size
from rom_cli.core.ranking import (
    search_all, rank, browse_items, load_popular
)
from rom_cli.core.extractor import extract_archive
from rom_cli.core.launcher import launch_game, find_emulator
from rom_cli.launcher import LibraryScanner, EmulatorRegistry, launch_launcher_tui
from rom_cli.tui.app import launch_tui, download_item
from rom_cli.providers import DLA, DLP, SOURCES
from rom_cli.models import RomItem


def fmt_row(r: RomItem, i: int) -> str:
    size = f"{human_size(r.size):>9}" if r.size else " " * 9
    kind = f"{r.kind:<6}" if r.kind else " " * 6
    star = "★ " if r.is_star else ""
    return f"{i:>2}  {r.platform_label[:11]:<11} {kind} {size}  {star}{r.title[:52]}"


def show_results(results: List[RomItem], limit: int = 15) -> None:
    write()
    write(f"  {'#':>2}  {'plataforma':<11} {'tipo':<6} {'tamanho':>9}  título")
    write("  " + "-" * 80)
    for i, r in enumerate(results[:limit], 1):
        write("  " + fmt_row(r, i))
    write()


def run_cli_download(picked: List[RomItem], outdir: Path, auto_extract: bool = False, play: bool = False) -> int:
    ok = 0
    for i, r in enumerate(picked, 1):
        write()
        write(f"  [{i}/{len(picked)}] {r.title} ({r.platform_label})")
        try:
            path = download_item(r, outdir, on_progress=lambda a, b, m: status(f"   {m}"))
            clear_status()
            size_str = human_size(path.stat().st_size) if path.exists() else "?"
            write(f"  ✔ pronto: {path}  ({size_str})")

            if auto_extract and path.suffix.lower() in (".zip", ".7z", ".rar"):
                write(f"  📦 extraindo {path.name}...")
                extract_archive(path, remove_archive=False, on_progress=lambda m: write(f"     {m}"))
                write("  ✔ extração concluída")

            if play:
                write(f"  🎮 iniciando jogo no emulador...")
                if launch_game(path, r.platform):
                    write("  ✔ jogo iniciado com sucesso!")
                else:
                    write(f"  ✖ nenhum emulador configurado/encontrado para {r.platform_label}")

            ok += 1
        except Exception as e:
            clear_status()
            write(f"  ✖ falhou: {e}")
    write()
    write(f"  {ok}/{len(picked)} baixado(s) em {outdir}")
    return 0 if ok else 1


def _has_textual() -> bool:
    try:
        import textual  # noqa: F401
        return True
    except ImportError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Busca e baixa ROMs/ISOs/jogos de Switch pelo terminal.")
    ap.add_argument("query", nargs="*")
    ap.add_argument("-p", "--platform", help="switch, snes, gba, ps2, nds, wii… (use -l)")
    ap.add_argument("-l", "--platforms", action="store_true", help="lista plataformas")
    ap.add_argument("-y", "--yes", action="store_true", help="baixa o melhor sem perguntar")
    ap.add_argument("-x", "--extract", action="store_true", help="extrai automaticamente arquivos compactados (zip/7z)")
    ap.add_argument("--play", action="store_true", help="abre o jogo automaticamente no emulador após baixar")
    ap.add_argument("--launch", action="store_true", help="abre o launcher de jogos instalados na biblioteca")
    ap.add_argument("--gui", action="store_true", help="abre o aplicativo Desktop completo com janela gráfica")
    ap.add_argument("--random", "--roulette", dest="roulette", action="store_true", help="sorteia e abre um jogo aleatório da sua biblioteca")
    ap.add_argument("--check-bios", action="store_true", help="audita e verifica se as pastas de BIOS dos emuladores estão completas")
    ap.add_argument("--patch", nargs=2, metavar=("ROM", "PATCH"), help="aplica patch de tradução (IPS ou BPS) diretamente na ROM")
    ap.add_argument("--backups", action="store_true", help="lista snapshots de backup de saves e memory cards")
    ap.add_argument("--installed", action="store_true", help="lista jogos já baixados na máquina")
    ap.add_argument("--set-emulator", nargs=2, metavar=("PLATFORM", "PATH"), help="define caminho customizado de um emulador")
    ap.add_argument("--install-emu", metavar="PLATFORM_OR_EMU", help="baixa e configura emulador portátil oficial automaticamente (1-Clique)")
    ap.add_argument("--auto-translate", metavar="ROM_FILE", help="detecta, baixa e aplica tradução PT-BR da comunidade automaticamente na ROM")
    ap.add_argument("--list", action="store_true", help="só lista resultados")
    ap.add_argument("--print-url", action="store_true", help="mostra o link direto e sai")
    ap.add_argument("--refresh", action="store_true", help="reconstrói o índice do catálogo")
    ap.add_argument("--index", action="store_true", help="baixa/mostra o índice e sai")
    ap.add_argument("-n", "--number", type=int, default=15, help="quantos resultados mostrar")
    ap.add_argument("-o", "--out", default=str(OUT_DIR), help="pasta de destino")
    args = ap.parse_args()

    if args.platforms:
        write("  plataformas: " + ", ".join(sorted(PLATFORMS)))
        return 0

    if args.set_emulator:
        plat, emu_path = args.set_emulator
        reg = EmulatorRegistry()
        reg.set_emulator_path(plat.lower(), emu_path)
        write(f"  ✔ Emulador para '{plat}' configurado: {emu_path}")
        return 0

    if args.install_emu:
        from rom_cli.core.emu_manager import install_emulator
        write(f"\n  ⬇ Iniciando download e instalação automática para '{args.install_emu}'...")

        def on_prog(cur, total, msg):
            status(f"  {msg}")

        success, msg, exe = install_emulator(args.install_emu, on_progress=on_prog)
        clear_status()
        if success:
            write(f"  {msg}\n")
            return 0
        else:
            write(f"  ✖ {msg}\n")
            return 1

    if args.auto_translate:
        rom_p = Path(args.auto_translate)
        if not rom_p.is_file():
            write(f"  ✖ Arquivo não encontrado: {rom_p}")
            return 1
        from rom_cli.core.translations import find_translation_for_game, apply_community_translation
        from rom_cli.core.utils import platform_of
        pk, _ = platform_of(rom_p.name, None)
        trans = find_translation_for_game(rom_p.stem, pk)
        if not trans:
            write(f"  ✖ Nenhuma tradução PT-BR automática cadastrada para '{rom_p.stem}' [{pk.upper()}].")
            return 1
        write(f"\n  🇧🇷 Tradução encontrada: {trans.game_title} por {trans.author} ({trans.group}) {trans.version}")

        def on_prog(cur, total, msg):
            status(f"  {msg}")

        success, msg, out = apply_community_translation(rom_p, trans, on_progress=on_prog)
        clear_status()
        if success:
            write(f"  {msg}\n")
            return 0
        else:
            write(f"  ✖ {msg}\n")
            return 1

    if args.check_bios:
        from rom_cli.core.bios_checker import audit_all_bios
        write("\n  🔍 Auditoria de BIOS e Firmwares de Emuladores:\n")
        audits = audit_all_bios()
        for a in audits:
            mark = "[OK]" if a["status"] == "ok" else "[X]"
            write(f"  {mark} {a['name']}")
            write(f"     Status: {a['message']}")
            write(f"     Diretório: {a.get('bios_dir', 'N/A')}")
            matched = a.get("matched", [])
            if matched:
                write(f"     Arquivos identificados: {', '.join(matched)}")
            write()
        return 0

    if args.patch:
        rom_file, patch_file = args.patch
        from rom_cli.core.patcher import apply_patch
        try:
            write(f"  🔧 Aplicando patch {patch_file} em {rom_file}...")
            out = apply_patch(rom_file, patch_file)
            write(f"  ✔ Patch aplicado com sucesso! Nova ROM gerada em: {out}")
            return 0
        except Exception as e:
            write(f"  ✖ Falha ao aplicar patch: {e}")
            return 1

    if args.backups:
        from rom_cli.core.savesync import list_save_backups
        backups = list_save_backups()
        write(f"\n  💾 Backups de Saves e Memory Cards ({len(backups)} snapshots):\n")
        if not backups:
            write("  Nenhum backup encontrado ainda.")
            return 0
        for b in backups:
            write(f"  [{b['platform'].upper()}] {b['filename']} ({human_size(b['size_bytes'])}) - {b['created_at']}")
        write()
        return 0

    outdir = Path(os.path.expanduser(args.out)).resolve()

    if args.installed:
        scanner = LibraryScanner(outdir)
        library = scanner.scan_all()
        total = sum(len(games) for games in library.values())
        write(f"\n  🎮 Biblioteca Local ({total} jogos encontrados em {outdir}):\n")
        if not library:
            write("  Nenhum jogo encontrado na pasta.")
            return 0
        for pk, games in sorted(library.items()):
            label = PLATFORM_LABELS.get(pk, pk.upper())
            write(f"  [{label}] ({len(games)} jogos):")
            for g in games:
                write(f"    - {g.title} (.{g.extension}) [{human_size(g.size)}]")
            write()
        return 0

    if args.gui:
        try:
            from rom_cli.gui.main_window import main as gui_main
            gui_main()
            return 0
        except ImportError as e:
            write(f"  ✖ Dependências gráficas ausentes: {e}\n  Execute: pip install customtkinter pillow")
            return 1

    if args.roulette:
        from rom_cli.core.roulette import pick_random_game
        game = pick_random_game(platform_key=key or None, outdir=outdir)
        if not game:
            write("  ✖ Nenhum jogo encontrado na biblioteca para sortear.")
            return 1
        write(f"\n  🎲 Roleta Gamer sorteou: {game.title} [{game.platform_label}]!")
        write(f"  🚀 Abrindo no emulador...")
        if launch_game(game.path, game.platform_key):
            write("  ✔ Jogo iniciado com sucesso!\n")
            return 0
        else:
            write(f"  ✖ Nenhum emulador configurado para {game.platform_label}\n")
            return 1

    if args.launch:
        if not _has_textual():
            write("  ✖ Instale o textual para usar o launcher visual: pip install textual")
            return 1
        launch_launcher_tui(outdir)
        return 0

    key = (args.platform or "").lower().strip()
    if key and key not in PLATFORMS:
        ap.error(f"plataforma desconhecida: {key}\n  use: {', '.join(sorted(PLATFORMS))}")

    if args.index:
        write("  montando índice…")
        idx = DLA.load_index(
            force=args.refresh,
            on_progress=lambda d, t: status(f"   {d}/{t} páginas")
        )
        clear_status()
        with_rom = sum(1 for e in idx if e.get("ext") in ("nsp", "xci", "nsz"))
        write(f"  {len(idx)} arquivos no índice ({with_rom} de Switch)")
        write(f"  cache: {INDEX_FILE}")
        pop = load_popular(force=args.refresh)
        top = ", ".join(f"{k}({len(v)})" for k, v in sorted(pop.items()) if v)
        write(f"  melhores (Wikipedia): {top}")
        return 0

    outdir = Path(os.path.expanduser(args.out)).resolve()

    if not args.query:
        if args.list:
            if not key:
                write("  use -p <plataforma> (ex.: rom -p switch --list)  ·  ou rom -l")
                return 1
            try:
                items = browse_items(key)
            except Exception as e:
                write(f"  ✖ {e}")
                return 1
            show_results(items, args.number)
            write(f"  {len(items)} itens no catálogo de {PLATFORM_LABELS.get(key, key)}"
                  " — o TUI (rom) navega tudo")
            return 0

        is_interactive = bool(sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty())
        if not is_interactive or not _has_textual():
            write("  digite: rom -p switch \"nome do jogo\"   (ou rom -l)")
            return 0

    query = " ".join(args.query).strip()

    if not query:
        launch_tui(platform_key=key, query="", outdir=outdir, force=args.refresh)
        return 0

    status(f"buscando '{query}'…")
    try:
        results = search_all(
            query, key or None,
            on_progress=lambda d, t: status(f"   índice {d}/{t} páginas"),
            force=args.refresh
        )
    except Exception as e:
        clear_status()
        write(f"  ✖ falha na busca: {e}")
        return 1
    clear_status()

    if not results:
        write("  ✖ nada encontrado. Tente outro nome ou outra plataforma.")
        return 1

    results = rank(results, query)

    if args.list:
        show_results(results, args.number)
        return 0

    if args.print_url:
        for r in results[:args.number]:
            write(f"  {r.title} [{r.platform_label} {r.kind or '-'} {human_size(r.size)}]")
            if r.source == "dlpsgame":
                for u in DLP.links(r.url):
                    write(f"  {u}")
            else:
                try:
                    url, name = SOURCES[r.source].resolve(r)
                    write(f"  {url}")
                except Exception as e:
                    write(f"  (erro: {e})")
            write()
        return 0

    is_interactive = bool(sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty())
    if args.yes or not is_interactive or not _has_textual():
        show_results(results, args.number)
        return run_cli_download(results[:1], outdir, auto_extract=args.extract, play=args.play)

    # Abre a TUI com os resultados pré-carregados
    launch_tui(platform_key=key, query=query, outdir=outdir, force=args.refresh)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        clear_status()
        write("\n  cancelado.")
        sys.exit(130)

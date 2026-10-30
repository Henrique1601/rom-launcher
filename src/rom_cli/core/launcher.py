"""Detector e executor de emuladores locais com monitoramento de tempo de jogo."""

import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Callable

from rom_cli.core.tracker import TRACKER


EMULATOR_CANDIDATES = {
    # Chave plataforma: [(nome_executavel, caminhos_comuns_windows)]
    "switch": [("ryujinx", ["Ryujinx/Ryujinx.exe", "AppData/Local/Ryujinx/Ryujinx.exe"])],
    "ps2": [("pcsx2", ["PCSX2/pcsx2.exe", "PCSX2/pcsx2-qtx64.exe"])],
    "ps1": [("duckstation", ["DuckStation/duckstation-qt-x64-ReleaseLTCG.exe"])],
    "ps3": [("rpcs3", ["rpcs3/rpcs3.exe"])],
    "gc": [("dolphin", ["Dolphin/Dolphin.exe", "Dolphin-x64/Dolphin.exe"])],
    "wii": [("dolphin", ["Dolphin/Dolphin.exe", "Dolphin-x64/Dolphin.exe"])],
    "xbox": [("xemu", ["xemu/xemu.exe"])],
    "xbox360": [("xenia", ["xenia/xenia.exe", "xenia_canary/xenia_canary.exe"])],
}


def find_emulator(platform_key: str) -> Optional[Path]:
    """Tenta localizar o emulador instalado no PATH ou em diretórios comuns de programas."""
    # 1. Verifica se há caminho configurado no EmulatorRegistry
    try:
        from rom_cli.launcher.registry import EmulatorRegistry
        reg_emu = EmulatorRegistry().find_emulator(platform_key)
        if reg_emu:
            return reg_emu
    except Exception:
        pass

    candidates = EMULATOR_CANDIDATES.get(platform_key, [])
    for exe_name, common_paths in candidates:
        which_path = shutil.which(exe_name)
        if which_path:
            return Path(which_path)

        local_app = Path(os.environ.get("LOCALAPPDATA", ""))
        prog_files = Path(os.environ.get("ProgramFiles", ""))
        prog_files_x86 = Path(os.environ.get("ProgramFiles(x86)", ""))
        home = Path.home()

        search_bases = [home, local_app, prog_files, prog_files_x86]
        for rel_path in common_paths:
            for base in search_bases:
                full = base / rel_path
                if full.exists():
                    return full

    # Procura retroarch globalmente como fallback geral
    retroarch = shutil.which("retroarch")
    if retroarch:
        return Path(retroarch)

    return None


def launch_game(rom_path: Path, platform_key: str, on_session_end: Optional[Callable[[int], None]] = None) -> bool:
    """Abre a ROM baixada diretamente com o emulador correspondente e monitora o tempo jogado."""
    emu_path = find_emulator(platform_key)
    if not emu_path:
        return False

    try:
        proc = subprocess.Popen([str(emu_path), str(rom_path)])
        start_time = time.time()
        game_key = rom_path.stem

        def monitor():
            proc.wait()
            duration = int(time.time() - start_time)
            TRACKER.record_session(game_key, duration)
            if on_session_end:
                on_session_end(duration)

        threading.Thread(target=monitor, daemon=True).start()
        return True
    except Exception:
        return False

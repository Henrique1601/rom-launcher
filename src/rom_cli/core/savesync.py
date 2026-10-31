"""Gerenciador de sincronização e backup automático de Saves e Memory Cards.

Permite proteger o progresso do jogador em emuladores como PCSX2, Dolphin,
DuckStation, RPCS3, Ryujinx, xemu, Xenia e RetroArch, gerando snapshots versionados.
"""

import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from rom_cli.config import CACHE_DIR

SAVES_BACKUP_DIR = CACHE_DIR / "saves_backup"
SAVES_BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def get_emulator_save_paths() -> Dict[str, List[Path]]:
    """Mapeia os caminhos padrão onde cada emulador armazena saves e memory cards."""
    home = Path.home()
    appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    localappdata = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    documents = home / "Documents"

    mapping: Dict[str, List[Path]] = {
        "ps2": [
            appdata / "PCSX2" / "memcards",
            documents / "PCSX2" / "memcards",
            home / ".config" / "PCSX2" / "memcards",
        ],
        "ps1": [
            documents / "DuckStation" / "memcards",
            appdata / "DuckStation" / "memcards",
            home / ".local" / "share" / "duckstation" / "memcards",
        ],
        "gc": [
            documents / "Dolphin Emulator" / "GC",
            appdata / "Dolphin Emulator" / "GC",
            home / ".local" / "share" / "dolphin-emu" / "GC",
        ],
        "wii": [
            documents / "Dolphin Emulator" / "Wii" / "title",
            appdata / "Dolphin Emulator" / "Wii" / "title",
            home / ".local" / "share" / "dolphin-emu" / "Wii" / "title",
        ],
        "ps3": [
            appdata / "RPCS3" / "dev_hdd0" / "home" / "00000001" / "savedata",
            home / ".config" / "rpcs3" / "dev_hdd0" / "home" / "00000001" / "savedata",
        ],
        "switch": [
            appdata / "Ryujinx" / "bis" / "user" / "save",
            home / ".config" / "Ryujinx" / "bis" / "user" / "save",
        ],
        "xbox": [
            appdata / "xemu" / "xemu",
            home / ".local" / "share" / "xemu" / "xemu",
        ],
        "xbox360": [
            documents / "Xenia" / "content",
            localappdata / "Xenia" / "content",
        ],
        "retroarch": [
            appdata / "RetroArch" / "saves",
            home / ".config" / "retroarch" / "saves",
        ],
    }

    # Adiciona RetroArch como fallback para consoles clássicos (SNES, NES, GBA, etc.)
    for retro in ["snes", "nes", "gba", "gbc", "gb", "nds", "n64", "genesis", "mastersystem", "dreamcast", "saturn"]:
        mapping[retro] = mapping["retroarch"]

    return mapping


def find_active_save_dir(platform_key: str) -> Optional[Path]:
    """Retorna o primeiro diretório existente de saves para a plataforma informada."""
    paths = get_emulator_save_paths().get(platform_key, [])
    for p in paths:
        if p.exists() and p.is_dir():
            return p
    return None


def create_save_backup(platform_key: str, game_title: Optional[str] = None, max_snapshots: int = 5) -> Optional[Path]:
    """
    Cria um arquivo .zip com snapshot dos saves da plataforma.
    Mantém no máximo `max_snapshots` cópias para evitar consumo de disco.
    """
    save_dir = find_active_save_dir(platform_key)
    if not save_dir:
        return None

    # Verifica se há arquivos na pasta
    files = [f for f in save_dir.rglob("*") if f.is_file()]
    if not files:
        return None

    plat_backup_dir = SAVES_BACKUP_DIR / platform_key
    plat_backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() else "_" for c in (game_title or "session"))[:30]
    zip_name = f"{platform_key}_{safe_title}_{timestamp}.zip"
    zip_path = plat_backup_dir / zip_name

    # Cria o arquivo ZIP comprimido
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            # Não inclui arquivos gigantes como discos virtuais inteiros > 200MB
            if f.stat().st_size < 200 * 1024 * 1024:
                rel_path = f.relative_to(save_dir)
                zf.write(f, arcname=str(rel_path))

    # Limpeza de snapshots antigos
    existing = sorted(plat_backup_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime)
    while len(existing) > max_snapshots:
        oldest = existing.pop(0)
        try:
            oldest.unlink()
        except Exception:
            pass

    return zip_path


def list_save_backups(platform_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista todos os backups de saves salvos localmente."""
    results = []
    dirs = [SAVES_BACKUP_DIR / platform_key] if platform_key else list(SAVES_BACKUP_DIR.iterdir())

    for d in dirs:
        if not d.exists() or not d.is_dir():
            continue
        pk = d.name
        for z in sorted(d.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True):
            stat = z.stat()
            results.append({
                "platform": pk,
                "filename": z.name,
                "path": str(z),
                "size_bytes": stat.st_size,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
            })
    return results


def restore_save_backup(backup_zip_path: Union[str, Path]) -> bool:
    """Restaura o conteúdo de um backup .zip para o diretório ativo do emulador."""
    zpath = Path(backup_zip_path)
    if not zpath.exists() or not zipfile.is_zipfile(zpath):
        return False

    pk = zpath.parent.name
    save_dir = find_active_save_dir(pk)
    if not save_dir:
        # Tenta criar o primeiro caminho padrão configurado
        paths = get_emulator_save_paths().get(pk, [])
        if paths:
            save_dir = paths[0]
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            return False

    with zipfile.ZipFile(zpath, "r") as zf:
        zf.extractall(save_dir)

    return True

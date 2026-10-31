"""Scraper de Capas e Posters de Jogos (Box Art) via Libretro Thumbnails e repositórios abertos."""

import os
import re
import urllib.parse
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    Image = None
    HAS_PIL = False

from rom_cli.config import CACHE_DIR
from rom_cli.core.utils import request_http, norm

COVERS_DIR = CACHE_DIR / "covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)

# Mapeamento de plataformas para repositórios oficiais Libretro Thumbnails
LIBRETRO_SYSTEMS = {
    "snes": "Nintendo_-_Super_Nintendo_Entertainment_System",
    "nes": "Nintendo_-_Nintendo_Entertainment_System",
    "gba": "Nintendo_-_Game_Boy_Advance",
    "gbc": "Nintendo_-_Game_Boy_Color",
    "gb": "Nintendo_-_Game_Boy",
    "nds": "Nintendo_-_Nintendo_DS",
    "n64": "Nintendo_-_Nintendo_64",
    "gc": "Nintendo_-_GameCube",
    "wii": "Nintendo_-_Wii",
    "switch": "Nintendo_-_Nintendo_Switch",
    "ps1": "Sony_-_PlayStation",
    "ps2": "Sony_-_PlayStation_2",
    "ps3": "Sony_-_PlayStation_3",
    "psp": "Sony_-_PlayStation_Portable",
    "psv": "Sony_-_PlayStation_Vita",
    "xbox": "Microsoft_-_Xbox",
    "xbox360": "Microsoft_-_Xbox_360",
    "genesis": "Sega_-_Mega_Drive_-_Genesis",
    "mastersystem": "Sega_-_Master_System_-_Mark_III",
    "dreamcast": "Sega_-_Dreamcast",
    "saturn": "Sega_-_Saturn",
    "arcade": "MAME",
}


def sanitize_filename_for_url(title: str) -> str:
    """Prepara o título para corresponder aos nomes padronizados do Libretro."""
    # Remove tags comuns como [v1.0], (USA), (Europe), etc. para fallback
    clean = re.sub(r"\[.*?\]", "", title)
    clean = re.sub(r"\(.*?\)", "", clean)
    clean = clean.replace("&", "_").replace("'", "").strip()
    return clean


def get_cover_path(title: str, platform_key: str) -> Path:
    """Retorna o caminho local onde a capa será salva em cache."""
    safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)[:80]
    plat_dir = COVERS_DIR / platform_key
    plat_dir.mkdir(parents=True, exist_ok=True)
    return plat_dir / f"{safe_title}.png"


def fetch_boxart(title: str, platform_key: str, force: bool = False) -> Optional[Path]:
    """
    Busca e faz cache local da capa (Box Art) do jogo.
    Retorna o Path da imagem local ou None se não encontrada.
    """
    local_path = get_cover_path(title, platform_key)
    if local_path.exists() and not force:
        return local_path

    system = LIBRETRO_SYSTEMS.get(platform_key)
    if not system:
        return None

    # Tenta com o nome completo original e depois com o nome limpo
    candidates = [title, sanitize_filename_for_url(title)]

    for cand in candidates:
        if not cand:
            continue
        quoted = urllib.parse.quote(cand)
        url = f"https://raw.githubusercontent.com/libretro-thumbnails/{system}/master/Named_Boxarts/{quoted}.png"

        try:
            status, _, body = request_http(url, timeout=12, retries=1)
            if status == 200 and len(body) > 1024:
                # Salva o arquivo temporário
                temp_path = local_path.with_suffix(".tmp")
                with open(temp_path, "wb") as f:
                    f.write(body)

                # Valida se é imagem PNG/JPEG válida (com Pillow se disponível, ou por magic bytes)
                if HAS_PIL and Image:
                    try:
                        with Image.open(temp_path) as img:
                            img.verify()
                        temp_path.replace(local_path)
                        return local_path
                    except Exception:
                        if temp_path.exists():
                            temp_path.unlink()
                else:
                    # Fallback sem Pillow: valida magic bytes de PNG ou JPEG
                    if body.startswith(b"\x89PNG\r\n\x1a\n") or body.startswith(b"\xff\xd8\xff"):
                        temp_path.replace(local_path)
                        return local_path
                    elif temp_path.exists():
                        temp_path.unlink()
        except Exception:
            continue

    return None

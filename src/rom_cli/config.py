"""Configurações globais e resolução de diretórios de forma cross-platform."""

import os
import sys
from pathlib import Path

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Diretório padrão para download de ROMs
_default_rom_dir = os.environ.get("ROM_DIR")
if _default_rom_dir:
    OUT_DIR = Path(_default_rom_dir).expanduser().resolve()
else:
    # No Windows e Unix, ~/.Downloads/roms é mapeado perfeitamente via Path.home()
    OUT_DIR = Path.home() / "Downloads" / "roms"

# Diretório de Cache
_xdg_cache = os.environ.get("XDG_CACHE_HOME")
_local_appdata = os.environ.get("LOCALAPPDATA")

if _xdg_cache:
    CACHE_DIR = Path(_xdg_cache).expanduser() / "rom-cli"
elif sys.platform == "win32" and _local_appdata:
    CACHE_DIR = Path(_local_appdata) / "rom-cli"
else:
    CACHE_DIR = Path.home() / ".cache" / "rom-cli"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

INDEX_FILE = CACHE_DIR / "dlarchive.json"
INDEX_TTL = 12 * 3600  # 12 horas
INDEX_PAGE = 200

PLATFORMS = {
    "switch": ("dlarchive", "switch"),
    "switchports": ("dlarchive", "switch"),
    "nds": ("dlarchive", "nds"),
    "gba": ("dlarchive", "gba"),
    "snes": ("dlarchive", "snes"),
    "pc": ("dlarchive", "pc"),
    "nes": ("romsgames", ["nintendo"]),
    "gb": ("romsgames", ["gameboy"]),
    "gbc": ("romsgames", ["gameboy-color"]),
    "n64": ("romsgames", ["nintendo-64"]),
    "3ds": ("romsgames", ["nintendo-3ds"]),
    "gc": ("romsgames", ["gamecube"]),
    "wii": ("romsgames", ["nintendo-wii"]),
    "ps1": ("romsgames", ["playstation"]),
    "ps2": ("romsgames", ["playstation-2"]),
    "psp": ("romsgames", ["playstation-portable"]),
    "ps3": ("nps", "ps3"),
    "psv": ("nps", "psv"),
    "ps4": ("dlpsgame", "ps4"),
    "ps5": ("dlpsgame", "ps5"),
    "genesis": ("romsgames", ["sega-genesis"]),
    "mastersystem": ("romsgames", ["sega-master-system"]),
    "dreamcast": ("romsgames", ["sega-dreamcast"]),
    "saturn": ("romsgames", ["sega-saturn"]),
    "arcade": ("romsgames", ["mame", "snk-neo-geo"]),
}

PLATFORM_LABELS = {
    "switch": "Switch",
    "switchports": "Switch Ports",
    "nds": "NDS",
    "gba": "GBA",
    "snes": "SNES",
    "ps2": "PS2",
    "psp": "PSP",
    "pc": "PC",
    "nes": "NES",
    "gb": "GB",
    "gbc": "GBC",
    "n64": "N64",
    "3ds": "3DS",
    "gc": "GameCube",
    "wii": "Wii",
    "ps1": "PS1",
    "ps3": "PS3",
    "psv": "PS Vita",
    "ps4": "PS4",
    "ps5": "PS5",
    "genesis": "Genesis",
    "mastersystem": "Master System",
    "dreamcast": "Dreamcast",
    "saturn": "Saturn",
    "arcade": "Arcade",
}

LABELS = {
    "nintendo": "NES",
    "super-nintendo": "SNES",
    "nintendo-64": "N64",
    "gameboy": "GB",
    "gameboy-color": "GBC",
    "gameboy-advance": "GBA",
    "nintendo-ds": "NDS",
    "nintendo-3ds": "3DS",
    "gamecube": "GameCube",
    "nintendo-wii": "Wii",
    "playstation": "PS1",
    "playstation-2": "PS2",
    "playstation-3": "PS3",
    "playstation-portable": "PSP",
    "sega-genesis": "Genesis",
    "sega-master-system": "Master System",
    "sega-dreamcast": "Dreamcast",
    "sega-saturn": "Saturn",
    "mame": "Arcade",
    "snk-neo-geo": "Neo Geo",
}

ROM_EXTS = (
    "zip", "7z", "rar", "nsp", "xci", "nsz", "iso", "cia", "pkg", "rom",
    "bin", "sfc", "smc", "nes", "gba", "gbc", "gb", "nds", "n64", "z64",
    "md", "smd", "gcm", "wbfs", "rvz", "cso", "pbp"
)

STOP_WORDS = {
    "the", "of", "a", "an", "and", "de", "do", "da", "o", "os", "as", "in",
    "to", "for", "e", "y"
}

BAD_WORDS = (
    "romhack", "translation", "beta", "prototype", "demo", "sample",
    "unlicensed", "(hack)", "homebrew", "soundtrack", "manual", "emulator"
)

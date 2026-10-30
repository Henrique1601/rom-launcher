"""Registro e gerenciamento de caminhos de emuladores locais."""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Optional

from rom_cli.config import CACHE_DIR

CONFIG_FILE = CACHE_DIR / "emulators.json"

DEFAULT_EMULATORS = {
    "switch": {
        "name": "Ryujinx",
        "binary": "Ryujinx",
        "relative_paths": ["Ryujinx/Ryujinx.exe", "AppData/Local/Ryujinx/Ryujinx.exe"]
    },
    "ps2": {
        "name": "PCSX2",
        "binary": "pcsx2",
        "relative_paths": ["PCSX2/pcsx2.exe", "PCSX2/pcsx2-qtx64.exe"]
    },
    "ps1": {
        "name": "DuckStation",
        "binary": "duckstation",
        "relative_paths": ["DuckStation/duckstation-qt-x64-ReleaseLTCG.exe"]
    },
    "ps3": {
        "name": "RPCS3",
        "binary": "rpcs3",
        "relative_paths": ["rpcs3/rpcs3.exe"]
    },
    "gc": {
        "name": "Dolphin",
        "binary": "dolphin",
        "relative_paths": ["Dolphin/Dolphin.exe", "Dolphin-x64/Dolphin.exe"]
    },
    "wii": {
        "name": "Dolphin",
        "binary": "dolphin",
        "relative_paths": ["Dolphin/Dolphin.exe", "Dolphin-x64/Dolphin.exe"]
    },
    "xbox": {
        "name": "xemu",
        "binary": "xemu",
        "relative_paths": ["xemu/xemu.exe"]
    },
    "xbox360": {
        "name": "Xenia",
        "binary": "xenia",
        "relative_paths": ["xenia/xenia.exe", "xenia_canary/xenia_canary.exe"]
    },
    "snes": {
        "name": "snes9x / RetroArch",
        "binary": "snes9x-x64",
        "relative_paths": ["snes9x/snes9x-x64.exe", "RetroArch/retroarch.exe"]
    },
    "gba": {
        "name": "mGBA / RetroArch",
        "binary": "mgba",
        "relative_paths": ["mGBA/mGBA.exe", "RetroArch/retroarch.exe"]
    },
    "nds": {
        "name": "melonDS / DeSmuME",
        "binary": "melonDS",
        "relative_paths": ["melonDS/melonDS.exe", "DeSmuME/DeSmuME_0.9.13_x64.exe"]
    },
    "n64": {
        "name": "Project64 / Simple64",
        "binary": "Project64",
        "relative_paths": ["Project64/Project64.exe"]
    },
    "psp": {
        "name": "PPSSPP",
        "binary": "PPSSPPWindows64",
        "relative_paths": ["PPSSPP/PPSSPPWindows64.exe"]
    }
}


class EmulatorRegistry:
    def __init__(self, config_file: Path = CONFIG_FILE):
        self.config_file = config_file
        self.custom_paths: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self) -> None:
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_paths, f, indent=2)
        except Exception:
            pass

    def set_emulator_path(self, platform_key: str, path: str) -> None:
        self.custom_paths[platform_key] = path
        self.save()

    def find_emulator(self, platform_key: str) -> Optional[Path]:
        """Localiza o executável do emulador para a plataforma especificada."""
        # 1. Custom path definido pelo usuário
        if platform_key in self.custom_paths:
            custom = Path(self.custom_paths[platform_key])
            if custom.exists():
                return custom

        # 2. Busca pelas definições padrão
        config = DEFAULT_EMULATORS.get(platform_key)
        if config:
            which = shutil.which(config["binary"])
            if which:
                return Path(which)

            search_bases = [
                Path.home(),
                Path(os.environ.get("LOCALAPPDATA", "")),
                Path(os.environ.get("ProgramFiles", "")),
                Path(os.environ.get("ProgramFiles(x86)", "")),
            ]

            for rel_path in config.get("relative_paths", []):
                for base in search_bases:
                    candidate = base / rel_path
                    if candidate.exists():
                        return candidate

        # 3. Fallback RetroArch
        retroarch = shutil.which("retroarch")
        if retroarch:
            return Path(retroarch)

        return None

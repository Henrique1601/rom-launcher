"""Modelos de dados estruturados para o rom-cli."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class RomItem:
    title: str
    platform: str          # chave interna (ex: 'switch', 'snes', 'ps2')
    platform_label: str    # rótulo legível (ex: 'Switch', 'SNES', 'PS2')
    source: str            # 'dlarchive', 'romsgames', 'nps', 'dlpsgame', 'archive_org'
    url: Optional[str] = None
    size: Optional[int] = None
    kind: str = ""         # 'Base', 'Update', 'DLC', 'Port'
    extra: Optional[Dict[str, Any]] = None
    is_star: bool = False  # Best-seller / destaque

    @property
    def filename(self) -> str:
        if self.extra and "filename" in self.extra:
            return self.extra["filename"]
        return self.title
